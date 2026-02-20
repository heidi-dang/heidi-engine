#pragma once

#include <memory>
#include <string>
#include <vector>
#include <optional>
#include <future>
#include <functional>

namespace heidi {
namespace core {

enum class ProviderType {
    OpenAI,
    Anthropic,
    Google,
    Cohere,
    Mistral,
    Grok,
    HuggingFace
};

struct GenerationParams {
    double temperature = 0.7;
    int max_tokens = 512;
    double top_p = 1.0;
    double frequency_penalty = 0.0;
    double presence_penalty = 0.0;
    std::optional<std::string> stop;
};

struct Message {
    std::string role;
    std::string content;
};

struct ApiResponse {
    std::string content;
    std::string raw_json;
    int usage_prompt_tokens = 0;
    int usage_completion_tokens = 0;
    int usage_total_tokens = 0;
    std::string model;
    std::string provider;
};

struct ProviderConfig {
    ProviderType type;
    std::string api_key;
    std::string model;
    std::string base_url;
    std::string organization;
    bool real_network_enabled = false;
};

class AIApiProvider {
public:
    virtual ~AIApiProvider() = default;
    virtual ApiResponse generate(const std::vector<Message>& messages, const GenerationParams& params) = 0;
    virtual std::future<ApiResponse> generate_async(const std::vector<Message>& messages, const GenerationParams& params);
    virtual ProviderType type() const = 0;
    virtual std::string name() const = 0;

protected:
    static std::string httpPost(const std::string& url, const std::string& auth_header, const std::string& json_body);
    static std::string httpPost(const std::string& url, const std::string& auth_header, const std::string& json_body, int& response_code);
};

class OpenAIProvider : public AIApiProvider {
public:
    explicit OpenAIProvider(const ProviderConfig& config);
    ApiResponse generate(const std::vector<Message>& messages, const GenerationParams& params) override;
    ProviderType type() const override { return ProviderType::OpenAI; }
    std::string name() const override { return "openai"; }

private:
    ProviderConfig config_;
};

class AnthropicProvider : public AIApiProvider {
public:
    explicit AnthropicProvider(const ProviderConfig& config);
    ApiResponse generate(const std::vector<Message>& messages, const GenerationParams& params) override;
    ProviderType type() const override { return ProviderType::Anthropic; }
    std::string name() const override { return "anthropic"; }

private:
    ProviderConfig config_;
    std::string extractSystemPrompt(const std::vector<Message>& messages) const;
};

class GoogleProvider : public AIApiProvider {
public:
    explicit GoogleProvider(const ProviderConfig& config);
    ApiResponse generate(const std::vector<Message>& messages, const GenerationParams& params) override;
    ProviderType type() const override { return ProviderType::Google; }
    std::string name() const override { return "google"; }

private:
    ProviderConfig config_;
};

class CohereProvider : public AIApiProvider {
public:
    explicit CohereProvider(const ProviderConfig& config);
    ApiResponse generate(const std::vector<Message>& messages, const GenerationParams& params) override;
    ProviderType type() const override { return ProviderType::Cohere; }
    std::string name() const override { return "cohere"; }

private:
    ProviderConfig config_;
};

class MistralProvider : public AIApiProvider {
public:
    explicit MistralProvider(const ProviderConfig& config);
    ApiResponse generate(const std::vector<Message>& messages, const GenerationParams& params) override;
    ProviderType type() const override { return ProviderType::Mistral; }
    std::string name() const override { return "mistral"; }

private:
    ProviderConfig config_;
};

class GrokProvider : public AIApiProvider {
public:
    explicit GrokProvider(const ProviderConfig& config);
    ApiResponse generate(const std::vector<Message>& messages, const GenerationParams& params) override;
    ProviderType type() const override { return ProviderType::Grok; }
    std::string name() const override { return "grok"; }

private:
    ProviderConfig config_;
};

class HuggingFaceProvider : public AIApiProvider {
public:
    explicit HuggingFaceProvider(const ProviderConfig& config);
    ApiResponse generate(const std::vector<Message>& messages, const GenerationParams& params) override;
    ProviderType type() const override { return ProviderType::HuggingFace; }
    std::string name() const override { return "huggingface"; }

private:
    ProviderConfig config_;
};

std::unique_ptr<AIApiProvider> createProvider(const ProviderConfig& config);
std::unique_ptr<AIApiProvider> createProvider(ProviderType type, const std::string& api_key, const std::string& model);

void enableRealNetwork(bool enabled);
bool isRealNetworkEnabled();

ProviderType parseProviderType(const std::string& name);
std::string providerTypeToString(ProviderType type);

} // namespace core
} // namespace heidi
