#include "engine_daemon.h"
#include "../include/kernel.h"
#include <iostream>
#include <string>
#include <chrono>
#include <thread>
#include <map>

namespace heidi {

EngineDaemon::EngineDaemon(const std::string& config_path) : config_path_(config_path) {
    // Load config (simplified placeholders)
    int max_concurrent_jobs = 4; // Use this as max_threads proxy for now

    // Create JobRunner with max concurrent jobs
    job_runner_ = std::make_unique<JobRunner>(max_concurrent_jobs);
}

void EngineDaemon::run() {
    std::cout << "[INFO] EngineDaemon starting with config: " << config_path_ << std::endl;

    // Start the runner
    job_runner_->start();

    // Determine command based on provider and mode
    char* provider_env = std::getenv("HEIDI_PROVIDER");
    char* cmd_override = std::getenv("HEIDI_JOB_COMMAND");
    
    std::string cmd;
    if (cmd_override) {
        cmd = cmd_override;
    } else if (provider_env && std::string(provider_env) == "copilot") {
        // Use the pipelined enhanced rig for Copilot
        cmd = "./scripts/run_enhanced.sh --repos 50 --parallel 8";
    } else {
        // Default pipeline: use the enhanced rig but with safer parallelism
        cmd = "./scripts/run_enhanced.sh --repos 50 --parallel 8";
        if (provider_env) {
            cmd += " --provider ";
            cmd += provider_env;
        }
    }
    // Note: loop_repos.sh doesn't currently support --config, 
    // but we'll include it if config_path_ is not default for future-proofing
    // or if the user added it elsewhere.
    if (config_path_ != "engine_config.yaml") {
        // cmd += " --config " + config_path_; // Skipping for now as loop_repos doesn't support it
    }

    // Submit job with environment variables
    JobLimits limits;
    limits.max_runtime_ms = 3600000; // 1 hour
    // Increase allowed child processes to avoid spurious PROC_LIMIT failures
    limits.max_child_processes = 256;
    
    // Collect environment variables to pass to job
    std::map<std::string, std::string> job_env;
    const char* env_vars[] = {"GITHUB_PAT", "GH_TOKEN", "COPILOT_GITHUB_TOKEN", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", 
                              "AZURE_OPENAI_DEPLOYMENT", "OPENAI_API_KEY", "TEACHER_MODEL"};
    for (const char* var : env_vars) {
        char* val = std::getenv(var);
        if (val) {
            job_env[var] = val;
        }
    }
    
    // Add PATH to include copilot CLI
    char* current_path = std::getenv("PATH");
    std::string new_path = std::string(current_path ? current_path : "") + ":/home/heidi/.local/share/gh/copilot/cli/stable/bin:/home/heidi/.local/bin";
    job_env["PATH"] = new_path;
    
    std::cout << "[INFO] Submitting job with command: " << cmd << std::endl;
    std::cout << "[INFO] Passing " << job_env.size() << " environment variables to job" << std::endl;
    std::string job_id = job_runner_->submit_job(cmd, limits, job_env);

    if (job_id == INVALID_JOB_ID) {
        std::cerr << "[ERROR] Job submission failed" << std::endl;
        return;
    }

    std::cout << "[INFO] Job submitted with ID: " << job_id << std::endl;

    MetricsSampler sampler;
    
    // Poll for completion
    bool finished = false;
    while (!finished) {
        // We must tick the runner to process its queue and check limits
        uint64_t now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();
        SystemMetrics metrics = sampler.sample();
        
        job_runner_->tick(now_ms, metrics);

        auto job = job_runner_->get_job_status(job_id);
        if (!job) {
            std::cerr << "[ERROR] Job lost from runner tracking" << std::endl;
            break;
        }

        JobStatus status = job->status;
        if (status == JobStatus::COMPLETED) {
            std::cout << "[INFO] Job completed successfully" << std::endl;
            finished = true;
        } else if (status == JobStatus::FAILED || status == JobStatus::CANCELLED || 
                   status == JobStatus::TIMEOUT || status == JobStatus::PROC_LIMIT) {
            std::cerr << "[ERROR] Job ended with status: " << (int)status << std::endl;
            if (!job->error.empty()) {
                std::cerr << "[ERROR] Job stderr:\n" << job->error << std::endl;
            }
            finished = true;
        }

        if (!finished) {
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
        }
    }

    job_runner_->stop();
    std::cout << "[INFO] EngineDaemon shutting down" << std::endl;
}

} // namespace heidi
