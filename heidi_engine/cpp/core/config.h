#pragma once

#include <string>

namespace heidi {
namespace core {

struct Config {
    std::string run_id;
    std::string out_dir;
<<<<<<< HEAD
    std::string repo_root;
=======
>>>>>>> origin/main
    std::string base_model;
    std::string teacher_model;
    int samples_per_round = 50;
    int rounds = 3;
    float val_ratio = 0.1f;
    int seq_len = 2048;
    int batch_size = 1;
    int grad_accum = 8;
    int train_steps = 500;
    int lora_r = 64;
    std::string seed;
    bool run_unit_tests = false;
    bool mock_subprocesses = false;
<<<<<<< HEAD
    
    // Budget Guardrails
    int max_wall_time_minutes = 60;
    int max_disk_mb = 10000;
    double max_cpu_pct = 90.0;
    double max_mem_pct = 90.0;
    
=======

>>>>>>> origin/main
    // Load from environment or python dictionary equiv. 
    // For now we keep it simple for P1 integration.
    static Config load_from_env();
};

} // namespace core
} // namespace heidi
