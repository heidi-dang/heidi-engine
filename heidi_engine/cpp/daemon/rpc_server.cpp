#include "rpc_server.h"

#include <cerrno>
#include <cstring>
#include <stdexcept>

#include <fcntl.h>
#include <poll.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/un.h>
#include <unistd.h>

namespace {
constexpr uint32_t kMaxFrame = 512u * 1024u; // 512KB hard cap
constexpr int kBacklog = 64;

struct Fd {
  int fd{-1};
  Fd() = default;
  explicit Fd(int f) : fd(f) {}
  ~Fd() { if (fd >= 0) ::close(fd); }
  Fd(const Fd&) = delete;
  Fd& operator=(const Fd&) = delete;
  Fd(Fd&& o) noexcept : fd(o.fd) { o.fd = -1; }
  Fd& operator=(Fd&& o) noexcept { if (this != &o) { if (fd>=0) ::close(fd); fd=o.fd; o.fd=-1; } return *this; }
  int release() { int r=fd; fd=-1; return r; }
};

static bool set_cloexec(int fd) {
  int flags = ::fcntl(fd, F_GETFD);
  if (flags < 0) return false;
  return (::fcntl(fd, F_SETFD, flags | FD_CLOEXEC) == 0);
}

static bool set_nonblock(int fd) {
  int flags = ::fcntl(fd, F_GETFL);
  if (flags < 0) return false;
  return (::fcntl(fd, F_SETFL, flags | O_NONBLOCK) == 0);
}

static bool safe_unlink(const std::string& path) {
  if (::unlink(path.c_str()) == 0) return true;
  return (errno == ENOENT);
}

static std::string make_err_response(const char* code, const char* message) {
  // Keep it minimal; replace with your JSON builder.
  // Note: This is not full JSON-RPC unless you include id; your dispatch should do that.
  // Use this only for “transport-level” errors if you want.
  (void)code;
  (void)message;
  return "{}";
}
} // namespace

RPCServer::RPCServer() = default;

RPCServer::~RPCServer() {
  stop();
}

bool RPCServer::start(const std::string& socket_path, DispatchFn dispatch) {
  if (running_.exchange(true)) return false; // already running

  socket_path_ = socket_path;
  dispatch_ = std::move(dispatch);

  // ----- stop pipe (wakeup) -----
  int p[2];
  if (::pipe(p) != 0) {
    running_.store(false);
    return false;
  }
  stop_pipe_r_ = p[0];
  stop_pipe_w_ = p[1];
  set_cloexec(stop_pipe_r_);
  set_cloexec(stop_pipe_w_);
  set_nonblock(stop_pipe_r_);
  set_nonblock(stop_pipe_w_);

  // ----- create UDS socket -----
  Fd s(::socket(AF_UNIX, SOCK_STREAM, 0));
  if (s.fd < 0) { stop(); return false; }
  set_cloexec(s.fd);

  // Ensure parent dir exists elsewhere (daemon should create runtime dir).
  // Remove any stale socket file.
  if (!safe_unlink(socket_path_)) { stop(); return false; }

  // Tighten default perms for the created filesystem node:
  // Use umask to ensure no group/other bits sneak in before chmod.
  mode_t old_umask = ::umask(0177); // results in 0600 for new nodes
  sockaddr_un addr{};
  addr.sun_family = AF_UNIX;
  if (socket_path_.size() >= sizeof(addr.sun_path)) {
    ::umask(old_umask);
    stop();
    return false;
  }
  std::strncpy(addr.sun_path, socket_path_.c_str(), sizeof(addr.sun_path) - 1);

  // ----- bind + listen -----
  if (::bind(s.fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) != 0) {
    ::umask(old_umask);
    stop();
    return false;
  }

  // Explicitly enforce 0600 even if umask changed elsewhere.
  if (::chmod(socket_path_.c_str(), 0600) != 0) {
    ::umask(old_umask);
    stop();
    return false;
  }
  ::umask(old_umask);

  struct stat st{};
  if (::stat(socket_path_.c_str(), &st) != 0) { stop(); return false; }
  if (!S_ISSOCK(st.st_mode)) { stop(); return false; }
  if ((st.st_mode & 077) != 0) { stop(); return false; } // no group/other perms
  if (st.st_uid != ::getuid()) { stop(); return false; }

  if (::listen(s.fd, kBacklog) != 0) {
    stop();
    return false;
  }

  // Non-blocking listen socket so accept loop can poll with stop pipe.
  set_nonblock(s.fd);

  listen_fd_ = s.release();

  // ----- start accept loop thread -----
  accept_thread_ = std::thread([this]() { this->accept_loop(); });
  return true;
}

void RPCServer::stop() {
  if (!running_.exchange(false)) return;

  // Wake accept loop
  if (stop_pipe_w_ >= 0) {
    uint8_t b = 1;
    if (::write(stop_pipe_w_, &b, 1) < 0) {}
  }

  // Join thread
  if (accept_thread_.joinable()) {
    accept_thread_.join();
  }

  // Close fds
  if (listen_fd_ >= 0) { ::close(listen_fd_); listen_fd_ = -1; }
  if (stop_pipe_r_ >= 0) { ::close(stop_pipe_r_); stop_pipe_r_ = -1; }
  if (stop_pipe_w_ >= 0) { ::close(stop_pipe_w_); stop_pipe_w_ = -1; }

  // Remove socket file
  if (!socket_path_.empty()) {
    (void)safe_unlink(socket_path_);
  }
}

void RPCServer::accept_loop() {
  // poll on: listen_fd_ (incoming) + stop_pipe_r_ (stop)
  pollfd pfds[2];
  pfds[0].fd = listen_fd_;
  pfds[0].events = POLLIN;
  pfds[1].fd = stop_pipe_r_;
  pfds[1].events = POLLIN;

  while (running_.load()) {
    int rc = ::poll(pfds, 2, 1000); // 1s tick to re-check running_
    if (rc < 0) {
      if (errno == EINTR) continue;
      break;
    }
    if (rc == 0) continue;

    if (pfds[1].revents & POLLIN) {
      // drain pipe
      uint8_t buf[32];
      while (::read(stop_pipe_r_, buf, sizeof(buf)) > 0) {}
      break;
    }

    if (pfds[0].revents & POLLIN) {
      for (;;) {
        int cfd = ::accept(listen_fd_, nullptr, nullptr);
        if (cfd < 0) {
          if (errno == EAGAIN || errno == EWOULDBLOCK) break;
          if (errno == EINTR) continue;
          // accept error; continue loop
          break;
        }
        set_cloexec(cfd);

        // Simple and safe: handle each client synchronously in a detached thread.
        // If you already have a bounded worker pool, enqueue handle_client instead.
        std::thread([this, cfd]() {
          this->handle_client(cfd);
          ::close(cfd);
        }).detach();
      }
    }
  }
}

void RPCServer::handle_client(int client_fd) {
  // Optional: set receive/send timeouts to avoid hangs on broken peers
  timeval tv{};
  tv.tv_sec = 60;
  tv.tv_usec = 0;
  (void)::setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
  (void)::setsockopt(client_fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

  while (running_.load()) {
    uint8_t lenb[4];
    if (!read_exact(client_fd, lenb, sizeof(lenb))) break;

    uint32_t len = load_be32(lenb);
    if (len == 0 || len > kMaxFrame) {
      // Protocol violation: close connection
      break;
    }

    std::string req;
    req.resize(len);
    if (!read_exact(client_fd, &req[0], len)) break;

    // dispatch -> response JSON string
    std::string resp;
    try {
      resp = dispatch_ ? dispatch_(req) : std::string("{\"jsonrpc\":\"2.0\",\"error\":{\"code\":-32601,\"message\":\"No dispatch\"}}");
    } catch (...) {
      // No exceptions over the wire; deterministic generic error
      resp = "{\"jsonrpc\":\"2.0\",\"error\":{\"code\":-32603,\"message\":\"Internal error\"}}";
    }

    if (resp.size() > kMaxFrame) {
      // Refuse to send oversized responses
      resp = "{\"jsonrpc\":\"2.0\",\"error\":{\"code\":-32603,\"message\":\"Response too large\"}}";
    }

    uint8_t outlen[4];
    store_be32(static_cast<uint32_t>(resp.size()), outlen);
    if (!write_exact(client_fd, outlen, sizeof(outlen))) break;
    if (!write_exact(client_fd, resp.data(), resp.size())) break;
  }
}

bool RPCServer::read_exact(int fd, void* buf, size_t n) {
  uint8_t* p = static_cast<uint8_t*>(buf);
  size_t off = 0;
  while (off < n) {
    ssize_t r = ::read(fd, p + off, n - off);
    if (r == 0) return false;
    if (r < 0) {
      if (errno == EINTR) continue;
      if (errno == EAGAIN || errno == EWOULDBLOCK) return false;
      return false;
    }
    off += static_cast<size_t>(r);
  }
  return true;
}

bool RPCServer::write_exact(int fd, const void* buf, size_t n) {
  const uint8_t* p = static_cast<const uint8_t*>(buf);
  size_t off = 0;
  while (off < n) {
    ssize_t w = ::write(fd, p + off, n - off);
    if (w <= 0) {
      if (w < 0 && errno == EINTR) continue;
      if (w < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) return false;
      return false;
    }
    off += static_cast<size_t>(w);
  }
  return true;
}

uint32_t RPCServer::load_be32(const uint8_t b[4]) {
  return (uint32_t(b[0]) << 24) | (uint32_t(b[1]) << 16) | (uint32_t(b[2]) << 8) | uint32_t(b[3]);
}

void RPCServer::store_be32(uint32_t v, uint8_t b[4]) {
  b[0] = uint8_t((v >> 24) & 0xFF);
  b[1] = uint8_t((v >> 16) & 0xFF);
  b[2] = uint8_t((v >> 8) & 0xFF);
  b[3] = uint8_t(v & 0xFF);
}
