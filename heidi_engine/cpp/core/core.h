#pragma once

#include "config.h"
#include "clock.h"
#include "journal_writer.h"
#include "status_writer.h"
#include <memory>
#include <atomic>
#include <map>
#include "heidi-kernel/metrics.h"

namespace heidi {
namespace core {

class Core {
public:
    Core();
    ~Core();

    void init(const std::string& config_path = "");
    void start(const std::string& mode = "full");
    std::string tick(int max_steps = 1);
    void shutdown();
    std::string get_status_json() const;
    void action_train_now();

private:
    std::string current_state_;
    int current_round_;
    std::string mode_;
    std::atomic<bool> stop_requested_;
    
    Config config_;
    std::unique_ptr<Clock> clock_;
    std::unique_ptr<JournalWriter> journal_;
    std::unique_ptr<StatusWriter> status_;
    std::unique_ptr<heidi::MetricsSampler> sampler_;
    
    void emit_event(const std::string& event_type, const std::string& message, 
                    const std::string& stage, const std::string& level = "info",
                    const std::map<std::string, int>& usage_delta = {});
    void set_state(const std::string& new_state, const std::string& stage);
    bool run_script(const std::string& script_name, const std::string& stage);
};

} // namespace core
} // namespace heidi
