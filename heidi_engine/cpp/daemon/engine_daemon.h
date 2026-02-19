#pragma once

#include <string>
#include <memory>
#include "heidi-kernel/resource_governor.h"
#include "heidi-kernel/job.h"

namespace heidi {

class EngineDaemon {
public:
    explicit EngineDaemon(const std::string& config_path);
    ~EngineDaemon() = default;

    void run();

private:
    std::string config_path_;
    std::unique_ptr<ResourceGovernor> governor_;
    std::unique_ptr<JobRunner> job_runner_;
};

} // namespace heidi
