#pragma once
#include <atomic>
#include <cstdint>
#include <functional>
#include <string>
#include <thread>

class RPCServer {
public:
  using DispatchFn = std::function<std::string(const std::string& req_json)>;

  RPCServer();
  ~RPCServer();

  // socket_path: e.g. <HEIDI_HOME>/runtime/heidid.sock
  // dispatch: called with request JSON; returns response JSON (already JSON-RPC)
  bool start(const std::string& socket_path, DispatchFn dispatch);
  void stop();

private:
  void accept_loop();
  void handle_client(int client_fd);

  static bool read_exact(int fd, void* buf, size_t n);
  static bool write_exact(int fd, const void* buf, size_t n);
  static uint32_t load_be32(const uint8_t b[4]);
  static void store_be32(uint32_t v, uint8_t b[4]);

private:
  std::string socket_path_;
  DispatchFn dispatch_;

  std::atomic<bool> running_{false};
  int listen_fd_{-1};

  // Wake accept_loop() on stop without relying on signals:
  int stop_pipe_r_{-1};
  int stop_pipe_w_{-1};

  std::thread accept_thread_;
};
