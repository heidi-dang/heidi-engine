# Heidi Daemon (heidid) Setup

The `heidid` binary provides resource-aware orchestration for the training pipeline.

## Build

```bash
mkdir -p build && cd build
cmake ..
make -j$(nproc)
```

## Running

### Simple Start
```bash
./build/bin/heidid --config engine_config.yaml
```

### Systemd Service
To run as a persistent service:

1. Edit `scripts/heidid.service` to verify paths.
2. Link the service file:
   ```bash
   sudo ln -s $(pwd)/scripts/heidid.service /etc/systemd/system/heidid.service
   ```
3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable heidid
   sudo systemctl start heidid
   ```

## Configuration

The daemon currently uses a simplified YAML/key-value parser. In the future, it can be extended with `yaml-cpp` for robust configuration management.
