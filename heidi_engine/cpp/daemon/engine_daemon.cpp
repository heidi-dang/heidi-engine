#include "engine_daemon.h"
#include "../include/kernel.h"
#include <iostream>
#include <string>
#include <chrono>
#include <thread>

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

    // Prepare shell command
    std::string cmd = "./scripts/loop_repos.sh --config " + config_path_;

    // Submit job
    JobLimits limits;
    limits.max_runtime_ms = 3600000; // 1 hour
    
    std::string job_id = job_runner_->submit_job(cmd, limits);

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
            finished = true;
        }

        if (!finished) {
            std::this_thread::sleep_for(std::chrono::seconds(2));
        }
    }

    job_runner_->stop();
    std::cout << "[INFO] EngineDaemon shutting down" << std::endl;
}

} // namespace heidi
