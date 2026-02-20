#include "provider.h"

#include "provider_transport.h"
#ifdef HAVE_CURL
#include <curl/curl.h>
#endif
// Prefer system nlohmann if available; fallback header is in deps/include
#include <nlohmann/json.hpp>

#include <sstream>
#include <stdexcept>
#include <chrono>
#include <thread>
#include <algorithm>

using json = nlohmann::json;

namespace heidi {
namespace core {

namespace {
    size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
        ((std::string*)userp)->append((char*)contents, size * nmemb);
        return size * nmemb;
    }

    std::string escapeJsonString(const std::string& s) {
        std::string result;
        for (char c : s) {
            switch (c) {
                case '"': result += "\\\""; break;
                case '\\': result += "\\\\"; break;
                case '\b': result += "\\b"; break;
                case '\f': result += "\\f"; break;
                case '\n': result += "\\n"; break;
                case '\r': result += "\\r"; break;
                case '\t': result += "\\t"; break;
                default: result += c; break;
            }
        }
        return result;
    }

    std::string messagesToJsonArray(const std::vector<Message>& messages) {
        std::string result = "[";
        for (size_t i = 0; i < messages.size(); ++i) {
            if (i > 0) result += ",";
            result += "{\"role\":\"" + escapeJsonString(messages[i].role) + "\",";
            result += "\"content\":\"" + escapeJsonString(messages[i].content) + "\"}";
        }
        result += "]";
        return result;
    }

    bool g_real_network_enabled = false;

    std::string redactAuth(const std::string& auth_header) {
        if (auth_header.find("Authorization:") != std::string::npos) {
            return "Authorization: REDACTED";
        }
        return "REDACTED";
    }
}

std::string AIApiProvider::httpPost(const std::string& url, const std::string& auth_header, const std::string& json_body) {
    int dummy;
    return httpPost(url, auth_header, json_body, dummy);
}

std::string AIApiProvider::httpPost(const std::string& url, const std::string& auth_header, const std::string& json_body, int& response_code) {
    // Preserve fail-closed behavior: network attempts are rejected unless
    // ProviderConfig.real_network_enabled is true.
    if (!g_real_network_enabled) {
        throw std::runtime_error("Real network is disabled. Set ProviderConfig.real_network_enabled = true to enable.");
    }

#ifdef HAVE_CURL
    return transport_post(url, auth_header, json_body, response_code);
#else
    (void)url; (void)auth_header; (void)json_body; (void)response_code;
    throw std::runtime_error("libcurl dev headers not available; install libcurl dev headers or rebuild with network disabled");
#endif
}

std::future<ApiResponse> AIApiProvider::generate_async(const std::vector<Message>& messages, const GenerationParams& params) {
    return std::async(std::launch::async, [this, messages, params]() {
        return this->generate(messages, params);
    });
}

OpenAIProvider::OpenAIProvider(const ProviderConfig& config) : config_(config) {}

ApiResponse OpenAIProvider::generate(const std::vector<Message>& messages, const GenerationParams& params) {
    std::string url = config_.base_url.empty() ? "https://api.openai.com/v1/chat/completions" : config_.base_url + "/v1/chat/completions";
    
    std::string auth_header = "Authorization: Bearer " + config_.api_key;
    if (!config_.organization.empty()) {
        auth_header += ";org=" + config_.organization;
    }

    std::string payload = "{";
    payload += "\"model\":\"" + config_.model + "\",";
    payload += "\"messages\":" + messagesToJsonArray(messages) + ",";
    payload += "\"temperature\":" + std::to_string(params.temperature) + ",";
    payload += "\"max_tokens\":" + std::to_string(params.max_tokens) + ",";
    payload += "\"top_p\":" + std::to_string(params.top_p) + ",";
    payload += "\"frequency_penalty\":" + std::to_string(params.frequency_penalty) + ",";
    payload += "\"presence_penalty\":" + std::to_string(params.presence_penalty);
    if (params.stop.has_value()) {
        payload += ",\"stop\":[\"" + escapeJsonString(*params.stop) + "\"]";
    }
    payload += "}";

    int response_code = 0;
    std::string response = httpPost(url, auth_header, payload, response_code);

    if (response_code != 200) {
        try {
            json err = json::parse(response);
            std::string err_msg = "Unknown error";
            if (err.contains("error")) {
                err_msg = err["error"].value("message", "Unknown error");
            }
            throw std::runtime_error("OpenAI API error: " + err_msg);
        } catch (const json::parse_error&) {
            throw std::runtime_error("OpenAI API error (code " + std::to_string(response_code) + "): " + response);
        }
    }

    json resp = json::parse(response);
    ApiResponse result;
    result.content = resp["choices"][0]["message"]["content"].get<std::string>();
    result.raw_json = response;
    result.model = resp.value("model", config_.model);
    result.provider = "openai";

    if (resp.contains("usage")) {
        result.usage_prompt_tokens = resp["usage"].value("prompt_tokens", 0);
        result.usage_completion_tokens = resp["usage"].value("completion_tokens", 0);
        result.usage_total_tokens = resp["usage"].value("total_tokens", 0);
    }

    return result;
}

AnthropicProvider::AnthropicProvider(const ProviderConfig& config) : config_(config) {}

std::string AnthropicProvider::extractSystemPrompt(const std::vector<Message>& messages) const {
    for (const auto& msg : messages) {
        if (msg.role == "system") {
            return msg.content;
        }
    }
    return "";
}

ApiResponse AnthropicProvider::generate(const std::vector<Message>& messages, const GenerationParams& params) {
    std::string url = config_.base_url.empty() ? "https://api.anthropic.com/v1/messages" : config_.base_url + "/v1/messages";
    
    std::string auth_header = "x-api-key: " + config_.api_key;
    std::string anth_version = "anthropic-version: 2023-06-01";

    std::string system = extractSystemPrompt(messages);
    
    std::string payload = "{";
    payload += "\"model\":\"" + config_.model + "\",";
    payload += "\"max_tokens\":" + std::to_string(params.max_tokens) + ",";
    payload += "\"temperature\":" + std::to_string(params.temperature) + ",";
    
    if (!system.empty()) {
        payload += "\"system\":\"" + escapeJsonString(system) + "\",";
    }

    std::vector<Message> filtered;
    for (const auto& msg : messages) {
        if (msg.role != "system") {
            filtered.push_back(msg);
        }
    }
    payload += "\"messages\":" + messagesToJsonArray(filtered);
    payload += "}";

    int response_code = 0;
    std::string response = httpPost(url, auth_header, payload, response_code);
    if (response_code != 200) {
        throw std::runtime_error("Anthropic API error (code " + std::to_string(response_code) + "): " + response);
    }

    json resp = json::parse(response);
    ApiResponse result;
    result.content = resp["content"][0]["text"].get<std::string>();
    result.raw_json = response;
    result.model = resp.value("model", config_.model);
    result.provider = "anthropic";

    if (resp.contains("usage")) {
        result.usage_prompt_tokens = resp["usage"].value("input_tokens", 0);
        result.usage_completion_tokens = resp["usage"].value("output_tokens", 0);
        result.usage_total_tokens = result.usage_prompt_tokens + result.usage_completion_tokens;
    }

    return result;
}

GoogleProvider::GoogleProvider(const ProviderConfig& config) : config_(config) {}

ApiResponse GoogleProvider::generate(const std::vector<Message>& messages, const GenerationParams& params) {
    std::string model_name = config_.model.empty() ? "gemini-1.5-pro" : config_.model;
    std::string url = config_.base_url.empty() 
        ? "https://generativelanguage.googleapis.com/v1beta/models/" + model_name + ":generateContent"
        : config_.base_url + "/v1beta/models/" + model_name + ":generateContent";
    
    std::string auth_header = "Authorization: Bearer " + config_.api_key;

    std::string contents = "[";
    for (size_t i = 0; i < messages.size(); ++i) {
        if (i > 0) contents += ",";
        contents += "{\"role\":\"" + messages[i].role + "\",";
        contents += "\"parts\":[{\"text\":\"" + escapeJsonString(messages[i].content) + "\"}]}";
    }
    contents += "]";

    std::string payload = "{";
    payload += "\"contents\":" + contents + ",";
    payload += "\"generationConfig\":{";
    payload += "\"temperature\":" + std::to_string(params.temperature) + ",";
    payload += "\"maxOutputTokens\":" + std::to_string(params.max_tokens) + ",";
    payload += "\"topP\":" + std::to_string(params.top_p);
    payload += "}}";

    int response_code = 0;
    std::string response = httpPost(url, auth_header, payload, response_code);

    if (response_code != 200) {
        throw std::runtime_error("Google API error (code " + std::to_string(response_code) + "): " + response);
    }

    json resp = json::parse(response);
    ApiResponse result;
    result.content = resp["candidates"][0]["content"]["parts"][0]["text"].get<std::string>();
    result.raw_json = response;
    result.model = config_.model;
    result.provider = "google";

    if (resp.contains("usageMetadata")) {
        result.usage_prompt_tokens = resp["usageMetadata"].value("promptTokenCount", 0);
        result.usage_completion_tokens = resp["usageMetadata"].value("candidatesTokenCount", 0);
        result.usage_total_tokens = resp["usageMetadata"].value("totalTokenCount", 0);
    }

    return result;
}

CohereProvider::CohereProvider(const ProviderConfig& config) : config_(config) {}

ApiResponse CohereProvider::generate(const std::vector<Message>& messages, const GenerationParams& params) {
    std::string url = config_.base_url.empty() ? "https://api.cohere.com/v1/chat" : config_.base_url + "/v1/chat";
    
    std::string auth_header = "Authorization: Bearer " + config_.api_key;

    std::string last_user_message;
    std::string preamble;
    for (const auto& msg : messages) {
        if (msg.role == "system") {
            preamble = msg.content;
        } else if (msg.role == "user") {
            last_user_message = msg.content;
        }
    }

    std::string payload = "{";
    payload += "\"model\":\"" + config_.model + "\",";
    if (!preamble.empty()) {
        payload += "\"preamble\":\"" + escapeJsonString(preamble) + "\",";
    }
    payload += "\"message\":\"" + escapeJsonString(last_user_message) + "\",";
    payload += "\"temperature\":" + std::to_string(params.temperature) + ",";
    payload += "\"max_tokens\":" + std::to_string(params.max_tokens);
    payload += "}";

    int response_code = 0;
    std::string response = httpPost(url, auth_header, payload, response_code);

    if (response_code != 200) {
        throw std::runtime_error("Cohere API error (code " + std::to_string(response_code) + "): " + response);
    }

    json resp = json::parse(response);
    ApiResponse result;
    result.content = resp["text"].get<std::string>();
    result.raw_json = response;
    result.model = resp.value("model", config_.model);
    result.provider = "cohere";

    if (resp.contains("usage")) {
        result.usage_prompt_tokens = resp["usage"].value("prompt_tokens", 0);
        result.usage_completion_tokens = resp["usage"].value("completion_tokens", 0);
        result.usage_total_tokens = resp["usage"].value("total_tokens", 0);
    }

    return result;
}

MistralProvider::MistralProvider(const ProviderConfig& config) : config_(config) {}

ApiResponse MistralProvider::generate(const std::vector<Message>& messages, const GenerationParams& params) {
    std::string url = config_.base_url.empty() ? "https://api.mistral.ai/v1/chat/completions" : config_.base_url + "/v1/chat/completions";
    
    std::string auth_header = "Authorization: Bearer " + config_.api_key;

    std::string payload = "{";
    payload += "\"model\":\"" + config_.model + "\",";
    payload += "\"messages\":" + messagesToJsonArray(messages) + ",";
    payload += "\"temperature\":" + std::to_string(params.temperature) + ",";
    payload += "\"max_tokens\":" + std::to_string(params.max_tokens);
    payload += "}";

    int response_code = 0;
    std::string response = httpPost(url, auth_header, payload, response_code);

    if (response_code != 200) {
        throw std::runtime_error("Mistral API error (code " + std::to_string(response_code) + "): " + response);
    }

    json resp = json::parse(response);
    ApiResponse result;
    result.content = resp["choices"][0]["message"]["content"].get<std::string>();
    result.raw_json = response;
    result.model = resp.value("model", config_.model);
    result.provider = "mistral";

    if (resp.contains("usage")) {
        result.usage_prompt_tokens = resp["usage"].value("prompt_tokens", 0);
        result.usage_completion_tokens = resp["usage"].value("completion_tokens", 0);
        result.usage_total_tokens = resp["usage"].value("total_tokens", 0);
    }

    return result;
}

GrokProvider::GrokProvider(const ProviderConfig& config) : config_(config) {}

ApiResponse GrokProvider::generate(const std::vector<Message>& messages, const GenerationParams& params) {
    std::string url = config_.base_url.empty() ? "https://api.x.ai/v1/chat/completions" : config_.base_url + "/v1/chat/completions";
    
    std::string auth_header = "Authorization: Bearer " + config_.api_key;

    std::string payload = "{";
    payload += "\"model\":\"" + config_.model + "\",";
    payload += "\"messages\":" + messagesToJsonArray(messages) + ",";
    payload += "\"temperature\":" + std::to_string(params.temperature) + ",";
    payload += "\"max_tokens\":" + std::to_string(params.max_tokens);
    payload += "}";

    int response_code = 0;
    std::string response = httpPost(url, auth_header, payload, response_code);

    if (response_code != 200) {
        throw std::runtime_error("Grok API error (code " + std::to_string(response_code) + "): " + response);
    }

    json resp = json::parse(response);
    ApiResponse result;
    result.content = resp["choices"][0]["message"]["content"].get<std::string>();
    result.raw_json = response;
    result.model = resp.value("model", config_.model);
    result.provider = "grok";

    if (resp.contains("usage")) {
        result.usage_prompt_tokens = resp["usage"].value("prompt_tokens", 0);
        result.usage_completion_tokens = resp["usage"].value("completion_tokens", 0);
        result.usage_total_tokens = resp["usage"].value("total_tokens", 0);
    }

    return result;
}

HuggingFaceProvider::HuggingFaceProvider(const ProviderConfig& config) : config_(config) {}

ApiResponse HuggingFaceProvider::generate(const std::vector<Message>& messages, const GenerationParams& params) {
    std::string model_id = config_.model.empty() ? "microsoft/Phi-3-mini-4k-instruct" : config_.model;
    std::string url = config_.base_url.empty() 
        ? "https://api-inference.huggingface.co/models/" + model_id
        : config_.base_url + "/models/" + model_id;
    
    std::string auth_header = "Authorization: Bearer " + config_.api_key;

    std::string inputs;
    for (const auto& msg : messages) {
        if (!inputs.empty()) inputs += "\n";
        inputs += msg.role + ": " + msg.content;
    }

    json payload = {
        {"inputs", inputs},
        {"parameters", {
            {"temperature", params.temperature},
            {"max_new_tokens", params.max_tokens},
            {"top_p", params.top_p}
        }}
    };

    std::string payload_str = payload.dump();
    int response_code = 0;
    std::string response = httpPost(url, auth_header, payload_str, response_code);

    if (response_code != 200) {
        throw std::runtime_error("HuggingFace API error (code " + std::to_string(response_code) + "): " + response);
    }

    json resp = json::parse(response);
    ApiResponse result;

    if (resp.is_array() && resp.size() > 0 && resp[0].contains("generated_text")) {
        result.content = resp[0]["generated_text"].get<std::string>();
    } else if (resp.is_array() && resp.size() > 0 && resp[0].is_object() && resp[0].contains("text")) {
        result.content = resp[0]["text"].get<std::string>();
    } else {
        result.content = resp.dump();
    }

    result.raw_json = response;
    result.model = config_.model;
    result.provider = "huggingface";

    return result;
}

std::unique_ptr<AIApiProvider> createProvider(const ProviderConfig& config) {
    g_real_network_enabled = config.real_network_enabled;
    return createProvider(config.type, config.api_key, config.model);
}

std::unique_ptr<AIApiProvider> createProvider(ProviderType type, const std::string& api_key, const std::string& model) {
    ProviderConfig config;
    config.type = type;
    config.api_key = api_key;
    config.model = model;

    switch (type) {
        case ProviderType::OpenAI:
            return std::make_unique<OpenAIProvider>(config);
        case ProviderType::Anthropic:
            return std::make_unique<AnthropicProvider>(config);
        case ProviderType::Google:
            return std::make_unique<GoogleProvider>(config);
        case ProviderType::Cohere:
            return std::make_unique<CohereProvider>(config);
        case ProviderType::Mistral:
            return std::make_unique<MistralProvider>(config);
        case ProviderType::Grok:
            return std::make_unique<GrokProvider>(config);
        case ProviderType::HuggingFace:
            return std::make_unique<HuggingFaceProvider>(config);
        default:
            throw std::invalid_argument("Unknown provider type");
    }
}

void enableRealNetwork(bool enabled) {
    g_real_network_enabled = enabled;
}

bool isRealNetworkEnabled() {
    return g_real_network_enabled;
}

ProviderType parseProviderType(const std::string& name) {
    std::string lower = name;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
    
    if (lower == "openai" || lower == "gpt") return ProviderType::OpenAI;
    if (lower == "anthropic" || lower == "claude") return ProviderType::Anthropic;
    if (lower == "google" || lower == "gemini") return ProviderType::Google;
    if (lower == "cohere") return ProviderType::Cohere;
    if (lower == "mistral") return ProviderType::Mistral;
    if (lower == "grok" || lower == "xai") return ProviderType::Grok;
    if (lower == "huggingface" || lower == "hf") return ProviderType::HuggingFace;
    
    throw std::invalid_argument("Unknown provider: " + name);
}

std::string providerTypeToString(ProviderType type) {
    switch (type) {
        case ProviderType::OpenAI: return "openai";
        case ProviderType::Anthropic: return "anthropic";
        case ProviderType::Google: return "google";
        case ProviderType::Cohere: return "cohere";
        case ProviderType::Mistral: return "mistral";
        case ProviderType::Grok: return "grok";
        case ProviderType::HuggingFace: return "huggingface";
        default: return "unknown";
    }
}

} // namespace core
} // namespace heidi
