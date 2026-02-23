#pragma once

#include <string>
#include <vector>
#include <optional>
#include <chrono>
#include <memory>
#include <functional>
#include <variant>

namespace heidi {
namespace pipeline {

// Forward declarations
struct PipelineConfig;
struct PipelineContext;
struct StageResult;
struct EngineState;

// =============================================================================
// Configuration
// =============================================================================

struct PipelineConfig {
    int rounds = 1;
    int samples_per_round = 50;
    std::string base_model = "mistralai/Mistral-7B-Instruct-v0.2";
    std::string teacher_model = "gpt-4o-mini";
    double val_ratio = 0.05;
    int seq_len = 2048;
    int batch_size = 1;
    int grad_accum = 8;
    int train_steps = 10;
    int lora_r = 32;
    int seed = 42;
    bool run_unit_tests = false;
    bool collect_only = false;  // Skip training
    std::string out_dir;
    std::string run_id;
};

// Per-round results
struct RoundMetrics {
    int round_num = 0;
    int raw_lines = 0;
    int clean_lines = 0;
    int rejected_lines = 0;
    int train_lines = 0;
    int val_lines = 0;
    std::chrono::milliseconds generate_time{0};
    std::chrono::milliseconds validate_time{0};
    std::chrono::milliseconds split_time{0};
    std::chrono::milliseconds train_time{0};
    std::optional<std::string> last_error;
    bool training_triggered = false;
    bool training_completed = false;
};

// =============================================================================
// Pipeline Context (carried through stages)
// =============================================================================

struct PipelineContext {
    PipelineConfig config;
    int current_round = 0;
    std::string current_run_id;
    std::string output_dir;
    std::string data_dir;
    
    // Current round files
    std::string raw_file;
    std::string clean_file;
    std::string train_file;
    std::string val_file;
    
    // Accumulated metrics
    std::vector<RoundMetrics> round_history;
    
    // Budget state (for future use)
    double remaining_budget_usd = 0.0;
    bool budget_paused = false;
};

// =============================================================================
// Stage Result
// =============================================================================

struct StageResult {
    bool success = true;
    std::optional<std::string> error_message;
    std::optional<std::string> output_file;
    int lines_in = 0;
    int lines_out = 0;
    int lines_rejected = 0;
    std::chrono::milliseconds elapsed{0};
    
    // For chaining
    static StageResult ok(const std::string& out = "", int out_lines = 0) {
        return StageResult{true, std::nullopt, out, 0, out_lines, 0, {}};
    }
    
    static StageResult error(const std::string& msg) {
        return StageResult{false, msg, std::nullopt, 0, 0, 0, {}};
    }
};

// =============================================================================
// Stage Interface
// =============================================================================

using StageRunner = std::function<StageResult(PipelineContext&)>;

// =============================================================================
// Pipeline Runner
// =============================================================================

class Pipeline {
public:
    explicit Pipeline(const PipelineConfig& config);
    ~Pipeline();
    
    // Run the full pipeline (all rounds)
    bool run();
    
    // Run a single round
    RoundMetrics run_round(int round_num);
    
    // Get current context
    const PipelineContext& context() const { return ctx_; }
    
    // Check if training should be triggered (for collect mode)
    bool check_train_now_trigger();
    
    // Clear train-now trigger
    void clear_train_now_trigger();
    
private:
    PipelineContext ctx_;
    bool initialized_ = false;
    
    // Stage implementations
    StageResult stage_generate(PipelineContext& ctx);
    StageResult stage_validate(PipelineContext& ctx);
    StageResult stage_split(PipelineContext& ctx);
    StageResult stage_train(PipelineContext& ctx);
    
    // Helpers
    void ensure_directories();
    void write_run_state();
    std::string get_run_id();
};

// =============================================================================
// JSONL I/O Utilities
// =============================================================================

struct JsonlReader {
    std::string path;
    bool open();
    bool read_line(std::string& out);
    void close();
    int64_t count_lines() const;
    bool is_open() const { return is_open_; }
    
private:
    FILE* fp_ = nullptr;
    bool is_open_ = false;
};

struct JsonlWriter {
    std::string path;
    bool open();
    bool write_line(const std::string& json);
    void close();
    bool flush();
    bool is_open() const { return is_open_; }
    
private:
    FILE* fp_ = nullptr;
    bool is_open_ = false;
};

// =============================================================================
// Validation
// =============================================================================

enum class ValidationError {
    None = 0,
    InvalidJson,
    MissingField,
    InvalidField,
    SecretDetected,
    TooLong,
    TooShort,
    Duplicate,
    ProvenanceFailed,
};

struct ValidationResult {
    bool valid = false;
    ValidationError error = ValidationError::None;
    std::string message;
    std::string sanitized_output;
};

ValidationResult validate_sample(const std::string& json_line);

// =============================================================================
// State File I/O (atomic)
// =============================================================================

bool write_state_atomic(const std::string& path, const std::string& content);
bool read_state(const std::string& path, std::string& content);

} // namespace pipeline
} // namespace heidi
