#include "core.h"
#include <iostream>
#include <sstream>

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
}

void Core::emit_event(const std::string& event_type, const std::string& message, 
                      const std::string& stage, const std::string& level) {
    if (!journal_) return;
    
    Event e;
    e.ts = clock_->now_iso8601();
    e.run_id = config_.run_id;
    e.round = current_round_;
    e.stage = stage;
    e.level = level;
    e.event_type = event_type;
    e.message = message;
    
    journal_->write(e);
}

void Core::set_state(const std::string& new_state, const std::string& stage) {
    current_state_ = new_state;
    if (status_) {
        // Enhanced state.json to match dashboard contract
        std::ostringstream ss;
        ss << "{";
        ss << "\"run_id\":\"" << config_.run_id << "\",";
        ss << "\"status\":\"" << (new_state == "IDLE" ? "completed" : "running") << "\",";
        ss << "\"current_round\":" << current_round_ << ",";
        ss << "\"current_stage\":\"" << stage << "\",";
        ss << "\"total_rounds\":" << config_.rounds << ",";
        ss << "\"mode\":\"" << mode_ << "\",";
        ss << "\"samples_per_round\":" << config_.samples_per_round << ",";
        ss << "\"teacher_generated\":0,";
        ss << "\"validated_clean\":0,";
        ss << "\"last_update\":\"" << clock_->now_iso8601() << "\"";
        ss << "}";
        status_->write(ss.str());
    }
}

void Core::start(const std::string& mode) {
    mode_ = mode;
    current_round_ = 1;
    stop_requested_ = false;
    emit_event("pipeline_start", "Starting training pipeline (C++)", "pipeline");
    set_state("COLLECTING", "initializing");
}

std::string Core::tick(int max_steps) {
    if (current_state_ == "IDLE" || stop_requested_) {
        return get_status_json();
    }
    
    // Simulate one state transition per tick for testing pybind
    if (current_state_ == "COLLECTING") {
        emit_event("stage_start", "Starting teacher generation", "generate");
        emit_event("stage_end", "Generated samples", "generate");
        set_state("VALIDATING", "validate");
    } 
    else if (current_state_ == "VALIDATING") {
        emit_event("stage_start", "Starting validation", "validate");
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
        emit_event("stage_end", "Completed unit tests", "test");
        if (mode_ == "full") {
            set_state("FINALIZING", "train");
        } else {
            set_state("IDLE", "complete");
        }
    } 
    else if (current_state_ == "FINALIZING") {
        emit_event("stage_start", "Starting training", "train");
        emit_event("stage_end", "Training complete", "train");
        set_state("EVALUATING", "eval");
    } 
    else if (current_state_ == "EVALUATING") {
        emit_event("stage_start", "Starting evaluation", "eval");
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
