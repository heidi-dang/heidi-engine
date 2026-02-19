#include "pipeline/pipeline.h"
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <unistd.h>
#include <chrono>
#include <fstream>
#include <sstream>
#include <filesystem>
#include <cstring>
#include <algorithm>
#include <set>

namespace fs = std::filesystem;
using namespace std::chrono;

namespace heidi {
namespace pipeline {

// =============================================================================
// Pipeline Implementation
// =============================================================================

Pipeline::Pipeline(const PipelineConfig& config) : ctx_{} {
    ctx_.config = config;
    ctx_.current_run_id = config.run_id.empty() ? get_run_id() : config.run_id;
    ctx_.current_run_id = ctx_.current_run_id;
    ctx_.output_dir = config.out_dir;
    ctx_.data_dir = config.out_dir + "/data";
}

Pipeline::~Pipeline() = default;

std::string Pipeline::get_run_id() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;
    
    std::stringstream ss;
    ss << "run_" << std::put_time(std::localtime(&time_t), "%Y%m%d_%H%M%S")
       << "_" << std::setfill('0') << std::setw(3) << ms.count();
    return ss.str();
}

void Pipeline::ensure_directories() {
    fs::create_directories(ctx_.output_dir + "/state");
    fs::create_directories(ctx_.output_dir + "/actions");
    fs::create_directories(ctx_.output_dir + "/logs");
    fs::create_directories(ctx_.data_dir);
    fs::create_directories(ctx_.output_dir + "/eval");
    fs::create_directories(ctx_.output_dir + "/runs");
}

bool Pipeline::run() {
    ensure_directories();
    initialized_ = true;
    
    for (int round = 1; round <= ctx_.config.rounds; ++round) {
        auto metrics = run_round(round);
        ctx_.round_history.push_back(metrics);
        
        // Check budget pause in collect mode
        if (ctx_.budget_paused) {
            break;
        }
    }
    
    return true;
}

RoundMetrics Pipeline::run_round(int round_num) {
    RoundMetrics metrics;
    metrics.round_num = round_num;
    
    ctx_.current_round = round_num;
    
    // Set up file paths for this round
    ctx_.raw_file = ctx_.data_dir + "/raw_round_" + std::to_string(round_num) + ".jsonl";
    ctx_.clean_file = ctx_.data_dir + "/clean_round_" + std::to_string(round_num) + ".jsonl";
    ctx_.train_file = ctx_.data_dir + "/train_round_" + std::to_string(round_num) + ".jsonl";
    ctx_.val_file = ctx_.data_dir + "/val_round_" + std::to_string(round_num) + ".jsonl";
    
    auto start = high_resolution_clock::now();
    
    // Stage 1: Generate
    auto gen_result = stage_generate(ctx_);
    metrics.generate_time = duration_cast<milliseconds>(high_resolution_clock::now() - start);
    if (!gen_result.success) {
        metrics.last_error = gen_result.error_message;
        return metrics;
    }
    
    // Stage 2: Validate
    auto val_start = high_resolution_clock::now();
    auto val_result = stage_validate(ctx_);
    metrics.validate_time = duration_cast<milliseconds>(high_resolution_clock::now() - val_start);
    metrics.raw_lines = val_result.lines_in;
    metrics.clean_lines = val_result.lines_out;
    metrics.rejected_lines = val_result.lines_rejected;
    if (!val_result.success) {
        metrics.last_error = val_result.error_message;
        return metrics;
    }
    
    // Stage 3: Split
    auto split_start = high_resolution_clock::now();
    auto split_result = stage_split(ctx_);
    metrics.split_time = duration_cast<milliseconds>(high_resolution_clock::now() - split_start);
    metrics.train_lines = split_result.lines_out;
    // val_lines will be set by split
    if (!split_result.success) {
        metrics.last_error = split_result.error_message;
        return metrics;
    }
    
    // Check for train-now trigger in collect mode
    if (ctx_.config.collect_only) {
        if (check_train_now_trigger()) {
            metrics.training_triggered = true;
            auto train_start = high_resolution_clock::now();
            auto train_result = stage_train(ctx_);
            metrics.train_time = duration_cast<milliseconds>(high_resolution_clock::now() - train_start);
            metrics.training_completed = train_result.success;
            if (train_result.success) {
                clear_train_now_trigger();
            }
        }
    } else {
        // Full mode: always train
        auto train_start = high_resolution_clock::now();
        auto train_result = stage_train(ctx_);
        metrics.train_time = duration_cast<milliseconds>(high_resolution_clock::now() - train_start);
        metrics.training_completed = train_result.success;
    }
    
    // Write run state after each round
    write_run_state();
    
    return metrics;
}

StageResult Pipeline::stage_generate(PipelineContext& ctx) {
    // Call external generator via system() - this is the adapter to existing Python
    std::string cmd = "python3 " + ctx_.config.out_dir + "/../../../scripts/01_teacher_generate.py "
        + " --samples " + std::to_string(ctx_.config.samples_per_round)
        + " --output " + ctx_.raw_file
        + " --teacher " + ctx_.config.teacher_model
        + " --round " + std::to_string(ctx_.current_round)
        + " --seed " + std::to_string(ctx_.config.seed)";
    
    int ret = system(cmd.c_str());
    
    if (ret != 0) {
        return StageResult::error("Generation failed with code " + std::to_string(ret));
    }
    
    // Count lines
    JsonlReader reader;
    if (reader.open(ctx_.raw_file)) {
        int count = (int)reader.count_lines();
        reader.close();
        return StageResult::ok(ctx_.raw_file, count);
    }
    
    return StageResult::error("Failed to read generated file");
}

StageResult Pipeline::stage_validate(PipelineContext& ctx) {
    // Call existing validate_clean.py
    std::string cmd = "python3 " + ctx_.config.out_dir + "/../../../scripts/02_validate_clean.py "
        + " --input " + ctx_.raw_file
        + " --output " + ctx_.clean_file;
    
    int ret = system(cmd.c_str());
    
    if (ret != 0) {
        return StageResult::error("Validation failed with code " + std::to_string(ret));
    }
    
    // Count lines
    JsonlReader raw_reader, clean_reader;
    int raw_count = 0, clean_count = 0;
    
    if (raw_reader.open(ctx_.raw_file)) {
        raw_count = (int)raw_reader.count_lines();
        raw_reader.close();
    }
    if (clean_reader.open(ctx_.clean_file)) {
        clean_count = (int)clean_reader.count_lines();
        clean_reader.close();
    }
    
    return StageResult::ok(ctx_.clean_file, clean_count, raw_count - clean_count);
}

StageResult Pipeline::stage_split(PipelineContext& ctx) {
    // Call existing split script or use native implementation
    std::string cmd = "python3 " + ctx_.config.out_dir + "/../../../.local/ml/scripts/split_holdout.py "
        + " --input " + ctx_.clean_file
        + " --val-ratio " + std::to_string(ctx_.config.val_ratio)
        + " --seed " + std::to_string(ctx_.config.seed);
    
    int ret = system(cmd.c_str());
    
    // Move to expected locations
    std::string train_src = ctx_.data_dir + "/train.jsonl";
    std::string val_src = ctx_.data_dir + "/val.jsonl";
    
    if (ret != 0) {
        return StageResult::error("Split failed with code " + std::to_string(ret));
    }
    
    // Rename to round-specific files
    rename(train_src.c_str(), ctx_.train_file.c_str());
    rename(val_src.c_str(), ctx_.val_file.c_str());
    
    // Count lines
    JsonlReader train_reader, val_reader;
    int train_count = 0, val_count = 0;
    
    if (train_reader.open(ctx_.train_file)) {
        train_count = (int)train_reader.count_lines();
        train_reader.close();
    }
    if (val_reader.open(ctx_.val_file)) {
        val_count = (int)val_reader.count_lines();
        val_reader.close();
    }
    
    return StageResult::ok(ctx_.train_file, train_count);
}

StageResult Pipeline::stage_train(PipelineContext& ctx) {
    // Call existing training script
    std::string cmd = "python3 " + ctx_.config.out_dir + "/../../../scripts/04_train_qlora.py "
        + " --data " + ctx_.train_file
        + " --val-data " + ctx_.val_file
        + " --output " + ctx_.output_dir + "/out_lora_round_" + std::to_string(ctx_.current_round)
        + " --base-model " + ctx_.config.base_model
        + " --seq-len " + std::to_string(ctx_.config.seq_len)
        + " --batch-size " + std::to_string(ctx_.config.batch_size)
        + " --lora-r " + std::to_string(ctx_.config.lora_r)
        + " --train-steps " + std::to_string(ctx_.config.train_steps);
    
    int ret = system(cmd.c_str());
    
    if (ret != 0) {
        return StageResult::error("Training failed with code " + std::to_string(ret));
    }
    
    return StageResult::ok(ctx_.output_dir + "/out_lora_round_" + std::to_string(ctx_.current_round));
}

bool Pipeline::check_train_now_trigger() {
    std::string latch1 = ctx_.output_dir + "/actions/train_now." + ctx_.current_run_id;
    std::string latch2 = ctx_.output_dir + "/actions/train_now.latest";
    
    return fs::exists(latch1) || fs::exists(latch2);
}

void Pipeline::clear_train_now_trigger() {
    std::string latch1 = ctx_.output_dir + "/actions/train_now." + ctx_.current_run_id;
    std::string latch2 = ctx_.output_dir + "/actions/train_now.latest";
    
    fs::remove(latch1);
    fs::remove(latch2);
}

void Pipeline::write_run_state() {
    std::string state_file = ctx_.output_dir + "/state/run_state.json";
    
    std::stringstream ss;
    ss << "{\n";
    ss << "    \"run_id\": \"" << ctx_.current_run_id << "\",\n";
    ss << "    \"mode\": \"" << (ctx_.config.collect_only ? "collect" : "full") << "\",\n";
    ss << "    \"current_round\": " << ctx_.current_round << ",\n";
    ss << "    \"last_write_ts\": \"" << std::chrono::system_clock::now().time_since_epoch().count() << "\",\n";
    
    // Current round counts
    if (!ctx_.round_history.empty()) {
        auto& last = ctx_.round_history.back();
        ss << "    \"counts\": {\n";
        ss << "        \"raw_lines\": " << last.raw_lines << ",\n";
        ss << "        \"clean_lines\": " << last.clean_lines << ",\n";
        ss << "        \"rejected_lines\": " << last.rejected_lines << "\n";
        ss << "    },\n";
    } else {
        ss << "    \"counts\": {\"raw_lines\": 0, \"clean_lines\": 0, \"rejected_lines\": 0},\n";
    }
    
    ss << "    \"budget_paused\": " << (ctx_.budget_paused ? "true" : "false") << "\n";
    ss << "}\n";
    
    write_state_atomic(state_file, ss.str());
}

// =============================================================================
// JSONL Reader/Writer
// =============================================================================

bool JsonlReader::open(const std::string& path) {
    fp_ = fopen(path.c_str(), "r");
    if (!fp_) return false;
    is_open_ = true;
    return true;
}

void JsonlReader::close() {
    if (fp_) {
        fclose(fp_);
        fp_ = nullptr;
    }
    is_open_ = false;
}

bool JsonlReader::read_line(std::string& out) {
    if (!fp_) return false;
    
    char* line = nullptr;
    size_t len = 0;
    ssize_t n = getline(&line, &len, fp_);
    
    if (n < 0) {
        free(line);
        return false;
    }
    
    // Remove trailing newline
    if (n > 0 && line[n-1] == '\n') {
        line[n-1] = '\0';
    }
    if (n > 1 && line[n-2] == '\r') {
        line[n-2] = '\0';
    }
    
    out = line;
    free(line);
    return true;
}

int64_t JsonlReader::count_lines() const {
    if (!fp_) return 0;
    
    // Save position
    long pos = ftell(fp_);
    fseek(fp_, 0, SEEK_SET);
    
    int64_t count = 0;
    char buffer[4096];
    while (fgets(buffer, sizeof(buffer), fp_)) {
        if (buffer[0] != '\n' && buffer[0] != '\0') {
            count++;
        }
    }
    
    // Restore position
    fseek(fp_, pos, SEEK_SET);
    return count;
}

bool JsonlWriter::open(const std::string& path) {
    fp_ = fopen(path.c_str(), "w");
    if (!fp_) return false;
    is_open_ = true;
    return true;
}

void JsonlWriter::close() {
    if (fp_) {
        fflush(fp_);
        fclose(fp_);
        fp_ = nullptr;
    }
    is_open_ = false;
}

bool JsonlWriter::write_line(const std::string& json) {
    if (!fp_) return false;
    
    if (fputs(json.c_str(), fp_) < 0) return false;
    if (fputc('\n', fp_) < 0) return false;
    return true;
}

bool JsonlWriter::flush() {
    if (!fp_) return false;
    return fflush(fp_) == 0;
}

// =============================================================================
// Validation
// =============================================================================

ValidationResult validate_sample(const std::string& json_line) {
    ValidationResult result;
    
    // Basic JSON parsing would go here
    // For now, just check for empty and basic structure
    
    if (json_line.empty()) {
        result.valid = false;
        result.error = ValidationError::InvalidJson;
        result.message = "Empty line";
        return result;
    }
    
    // Check for required fields (basic check)
    // In a full implementation, parse JSON and check fields
    
    result.valid = true;
    result.error = ValidationError::None;
    result.sanitized_output = json_line;
    return result;
}

// =============================================================================
// Atomic State Write
// =============================================================================

bool write_state_atomic(const std::string& path, const std::string& content) {
    std::string tmp_path = path + ".tmp";
    
    std::ofstream out(tmp_path, std::ios::binary);
    if (!out) return false;
    
    out << content;
    out.close();
    
    // Atomic rename
    return rename(tmp_path.c_str(), path.c_str()) == 0;
}

bool read_state(const std::string& path, std::string& content) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return false;
    
    std::stringstream buffer;
    buffer << in.rdbuf();
    content = buffer.str();
    return true;
}

} // namespace pipeline
} // namespace heidi
