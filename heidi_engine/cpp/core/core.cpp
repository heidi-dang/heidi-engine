#include "core.h"
#include "subprocess.h"
#include <iostream>
#include <sstream>
#include <vector>
#include <thread>
#include <chrono>
#include <stdexcept>

namespace heidi {
namespace core {

Core::Core() 
    : current_state_("IDLE"), current_round_(0), stop_requested_(false) {
}

Core::~Core() = default;

void Core::init(const std::string& config_path) {
    (void)config_path; // Mocking parsing for now
    config_ = Config::load_from_env();
    clock_ = std::make_unique<Clock>();
    
    std::string journal_path = config_.out_dir + "/events.jsonl";
    std::string status_path = config_.out_dir + "/state.json";
    
    journal_ = std::make_unique<JournalWriter>(journal_path, config_.run_id);
    status_ = std::make_unique<StatusWriter>(status_path);
    sampler_ = std::make_unique<heidi::MetricsSampler>();
    
    // Set up resource guardrails based on configuration parameters
    heidi::GovernorPolicy policy;
    policy.cpu_high_watermark_pct = config_.max_cpu_pct;
    // Note: Kernel defines RAM constraints via mem available pct, but we want absolute bounds. Note this.
    // For simplicity, we assume an 8GB nominal test container bounds map to max_mem_pct, but usually this is OS wide.
    policy.mem_high_watermark_pct = config_.max_mem_pct;
    
    governor_ = std::make_unique<heidi::ResourceGovernor>(policy);
}

void Core::emit_event(std::string_view event_type, std::string_view message, 
                      std::string_view stage, std::string_view level,
                      const std::map<std::string, int>& usage_delta) {
    if (!journal_) return;
    
    Event e;
    e.ts = clock_->now_iso8601();
    e.run_id = config_.run_id;
    e.round = current_round_;
    e.stage = std::string(stage);
    e.level = std::string(level);
    e.event_type = std::string(event_type);
    e.message = std::string(message);
    e.usage_delta = usage_delta;
    
    journal_->write(e);
}

void Core::set_state(std::string_view new_state, std::string_view stage) {
    current_state_ = std::string(new_state);
    if (status_) {
        // Simple serialization since we don't have json.hpp handy
        std::ostringstream ss;
        ss << "{";
        ss << "\"run_id\":\"" << config_.run_id << "\",";
        ss << "\"status\":\"" << (new_state == "IDLE" ? "completed" : "running") << "\",";
        ss << "\"current_round\":" << current_round_ << ",";
        ss << "\"current_stage\":\"" << stage << "\"";
        ss << "}";
        status_->write(ss.str());
    }
}

void Core::start(const std::string& mode) {
    if (stop_requested_) return;

    // Zero-Trust Gatekeeper (Lane C): Refuse REAL mode if insecure
    if (mode == "real") {
        if (!governor_) {
            emit_event("gatekeeper_failed", "REAL mode refused: Resource Governor (guardrails) NOT initialized", "init", "critical");
            set_state("ERROR", "error");
            throw std::runtime_error("REAL mode refused: Resource Governor NOT initialized");
        }

        // Internal call to heidi doctor --strict (Lane C requirement)
        // Invoke via module path to prevent local repo overrides
        std::string doctor_output;
        std::vector<std::string> doctor_args = {"python3", "-m", "heidi_engine.doctor", "--strict"};
        int doctor_status = Subprocess::execute(doctor_args, doctor_output, 30);
        
        // Log doctor output hash for audit (no secrets)
        std::string output_summary = "Doctor Status: " + std::to_string(doctor_status) + 
                                     " (Output Hash: " + journal_->compute_sha256(doctor_output).substr(0, 8) + ")";

        if (doctor_status != 0) {
            emit_event("gatekeeper_failed", "REAL mode refused: " + output_summary, "init", "critical");
            set_state("ERROR", "error");
            throw std::runtime_error("REAL mode refused: " + output_summary);
        }

        emit_event("gatekeeper_passed", output_summary, "init", "info");

        // Check for mandatory Zero-Trust environment variables
        const char* key = std::getenv("HEIDI_SIGNING_KEY");
        const char* keystore = std::getenv("HEIDI_KEYSTORE_PATH");
        if (!key || !keystore) {
             emit_event("gatekeeper_failed", "REAL mode refused: Missing signing key or keystore path", "init", "critical");
             set_state("ERROR", "error");
             return;
        }
    }

    mode_ = mode;
    current_round_ = 1;
    stop_requested_ = false;
    emit_event("pipeline_start", "Starting training pipeline (C++)", "pipeline");
    set_state("COLLECTING", "initializing");
}

bool Core::run_script(const std::string& script_name, std::string_view stage) {
    if (mode_ == "full" && current_state_ == "IDLE") {
        emit_event("gatekeeper_violation", "Attempted to run script in REAL mode without start()", "execution", "critical");
        return false;
    }
    if (stop_requested_) return false;

    if (config_.mock_subprocesses) {
        std::map<std::string, int> usage;
        if (sampler_) {
            // Hotpath fix: do not sample /proc/stat in mock mode; use synthetic baseline
            usage["system_mem_available_kb_delta"] = 1024;
            usage["system_cpu_pct"] = 5;
        }
        emit_event("script_success", script_name + " completed successfully (mocked)", stage, "info", usage);
        return true;
    }

    // Apply Budget Guardrails check looping until resources clear or timeout
    double wait_time_sec = 0;
    heidi::SystemMetrics stats_before;
    bool has_stats_before = false;

    while (!stop_requested_) {
        if (sampler_) {
            stats_before = sampler_->sample();
            has_stats_before = true;
        }
        
        // Wait gracefully while spikes exist
        if (governor_ && sampler_) {
            double mem_pct = 100.0 * (1.0 - static_cast<double>(stats_before.mem.available) / static_cast<double>(stats_before.mem.total));
            
            auto decision = governor_->decide(stats_before.cpu_usage_percent, mem_pct, 1, 0); 
            if (decision.decision == heidi::GovernorDecision::HOLD_QUEUE) {
                std::string reason_str = "Unknown";
                if (decision.reason == heidi::BlockReason::CPU_HIGH) reason_str = "CPU spiked > " + std::to_string(config_.max_cpu_pct) + "%";
                else if (decision.reason == heidi::BlockReason::MEM_HIGH) reason_str = "RAM spiked > " + std::to_string(config_.max_mem_pct) + "%";
                
                emit_event("pipeline_throttled", "Delaying script execution: " + reason_str, stage, "warn");
                std::this_thread::sleep_for(std::chrono::milliseconds(decision.retry_after_ms));
                wait_time_sec += (decision.retry_after_ms / 1000.0);
                
                if (wait_time_sec > (config_.max_wall_time_minutes * 60)) {
                   emit_event("pipeline_error", "Exceeded maximum global pipeline wall time limits waiting for resources", stage, "error");
                   set_state("ERROR", "error");
                   return false; 
                }
                continue; 
            }
        }
        break; 
    }
    
    if (stop_requested_) return false;

    std::vector<std::string> args;
    args.push_back("python3"); // Assumption: the environment has python3 in PATH
    
    // Use explicit repo_root instead of assuming cwd
    std::string script_path = config_.repo_root + "/scripts/" + script_name;
    args.push_back(script_path);
    
    // Map current parameters that the script needs.
    // In full implementation we might pass `--output` etc.
    args.push_back("--round");
    args.push_back(std::to_string(current_round_));
    
    std::string output;
    try {
        int status = Subprocess::execute(args, output, 300); // 300 second hard timeout
        
        std::map<std::string, int> usage;
        if (sampler_ && has_stats_before) {
            heidi::SystemMetrics stats_after = sampler_->sample();
            int mem_delta_kb = static_cast<int>(stats_before.mem.available - stats_after.mem.available);
            usage["system_mem_available_kb_delta"] = mem_delta_kb;
            usage["system_cpu_pct"] = static_cast<int>(stats_after.cpu_usage_percent);
        }

        if (status != 0) {
            std::string err_msg = script_name + " failed with exit code " + std::to_string(status) + ":\n" + output.substr(0, 200);
            emit_event("pipeline_error", journal_ ? journal_->sanitize(err_msg) : err_msg, "pipeline", "error", usage);
            set_state("ERROR", "error");
            return false;
        }
        
        emit_event("script_success", script_name + " completed successfully", stage, "info", usage);
    } catch (const std::exception& e) {
        std::string err_msg = "Subprocess exception for " + script_name + ": " + e.what();
        emit_event("pipeline_error", err_msg, "pipeline", "error");
        set_state("ERROR", "error");
        return false;
    }
    return true;
}

std::string Core::tick(int max_steps) {
    if (current_state_ == "IDLE" || current_state_ == "ERROR" || stop_requested_) {
        return get_status_json();
    }
    
    if (current_state_ == "COLLECTING") {
        emit_event("round_start", "Starting round " + std::to_string(current_round_), "round");
        emit_event("stage_start", "Starting teacher generation", "generate");
        
        if (!run_script("01_teacher_generate.py", "generate")) return get_status_json();
        
        emit_event("stage_end", "Generated samples", "generate");
        set_state("VALIDATING", "validate");
    } 
    else if (current_state_ == "VALIDATING") {
        emit_event("stage_start", "Starting validation", "validate");
        
        if (!run_script("02_validate_clean.py", "validate")) return get_status_json();
        
        emit_event("stage_end", "Validated samples", "validate");
        if (config_.run_unit_tests) {
            set_state("TESTING", "test");
        } else if (mode_ == "full") {
            set_state("FINALIZING", "train");
        } else {
            set_state("IDLE", "complete");
        }
    } 
    else if (current_state_ == "TESTING") {
        emit_event("stage_start", "Starting unit tests", "test");
        
        if (!run_script("03_unit_test_gate.py", "test")) return get_status_json();
        
        emit_event("stage_end", "Completed unit tests", "test");
        if (mode_ == "full") {
            set_state("FINALIZING", "train");
        } else {
            set_state("IDLE", "complete");
        }
    } 
    else if (current_state_ == "FINALIZING") {
        emit_event("stage_start", "Starting training", "train");
        
        if (!run_script("04_train_qlora.py", "train")) return get_status_json();
        
        emit_event("stage_end", "Training complete", "train");
        set_state("EVALUATING", "eval");
    } 
    else if (current_state_ == "EVALUATING") {
        emit_event("stage_start", "Starting evaluation", "eval");
        
        run_script("05_eval.py", "eval"); // allowed to fail without taking down pipeline
        
        emit_event("stage_end", "Evaluation complete", "eval");
        
        if (current_round_ < config_.rounds) {
            current_round_++;
            set_state("COLLECTING", "generate");
        } else {
            emit_event("pipeline_complete", "Training pipeline finished", "pipeline");
            set_state("IDLE", "complete");
        }
    }
    
    return get_status_json();
}

void Core::shutdown() {
    stop_requested_ = true;
    emit_event("pipeline_stop", "Stop requested", "pipeline");
    set_state("IDLE", "interrupted");
}

void Core::action_train_now() {
    if (mode_ == "collect" && current_state_ == "IDLE") {
        set_state("FINALIZING", "train");
    }
}

std::string Core::get_status_json() const {
    std::ostringstream ss;
    ss << "{";
    ss << "\"state\":\"" << current_state_ << "\",";
    ss << "\"round\":" << current_round_ << ",";
    ss << "\"mode\":\"" << mode_ << "\",";
    ss << "\"run_id\":\"" << config_.run_id << "\"";
    ss << "}";
    return ss.str();
}

} // namespace core
} // namespace heidi
