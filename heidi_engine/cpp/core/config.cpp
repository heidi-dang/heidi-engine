#include "config.h"
#include <cstdlib>

namespace heidi {
namespace core {

Config Config::load_from_env() {
    Config c;
    if (const char* env_p = std::getenv("RUN_ID")) c.run_id = env_p;
    if (const char* env_p = std::getenv("OUT_DIR")) c.out_dir = env_p;
    else c.out_dir = std::string(std::getenv("HOME")) + "/.local/heidi_engine";
    
    if (const char* env_p = std::getenv("BASE_MODEL")) c.base_model = env_p;
    if (const char* env_p = std::getenv("TEACHER_MODEL")) c.teacher_model = env_p;
    
    if (const char* env_p = std::getenv("SAMPLES_PER_ROUND")) c.samples_per_round = std::stoi(env_p);
    if (const char* env_p = std::getenv("ROUNDS")) c.rounds = std::stoi(env_p);
    if (const char* env_p = std::getenv("VAL_RATIO")) c.val_ratio = std::stof(env_p);
    if (const char* env_p = std::getenv("SEQ_LEN")) c.seq_len = std::stoi(env_p);
    if (const char* env_p = std::getenv("BATCH_SIZE")) c.batch_size = std::stoi(env_p);
    if (const char* env_p = std::getenv("GRAD_ACCUM")) c.grad_accum = std::stoi(env_p);
    if (const char* env_p = std::getenv("TRAIN_STEPS")) c.train_steps = std::stoi(env_p);
    if (const char* env_p = std::getenv("LORA_R")) c.lora_r = std::stoi(env_p);
    if (const char* env_p = std::getenv("SEED")) c.seed = env_p;
    
    if (const char* env_p = std::getenv("RUN_UNIT_TESTS")) {
        c.run_unit_tests = (std::string(env_p) == "1");
    }
    
    if (const char* env_p = std::getenv("HEIDI_MOCK_SUBPROCESSES")) {
        c.mock_subprocesses = (std::string(env_p) == "1");
    }

    return c;
}

} // namespace core
} // namespace heidi
