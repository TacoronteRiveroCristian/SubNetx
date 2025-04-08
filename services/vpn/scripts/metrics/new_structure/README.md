# Host Metrics Monitor

A simple tool to collect performance and availability metrics from a specific host (IP or domain).

## Features

- **Ping Monitoring**: Measures connectivity, latency, and packet loss
- **TLS Certificate Verification**: For HTTPS targets, checks certificate validity and details
- **Simple CLI Interface**: Easy to use command-line tool with various options
- **JSON Output**: Results in structured JSON format for easy integration with other tools

## Usage

### Basic Usage

```bash
# Monitor a domain with default settings
python host_metrics.py --target example.com

# Monitor an IP address
python host_metrics.py --target 192.168.1.1

# Save results to a file
python host_metrics.py --target example.com --output-file metrics.json
```

### Advanced Options

```bash
# Increase ping count to 10 packets (default is 5)
python host_metrics.py --target example.com --count 10

# Increase ping timeout to 5 seconds (default is 2)
python host_metrics.py --target example.com --timeout 5

# Disable TLS certificate checking
python host_metrics.py --target example.com --no-tls

# Enable verbose logging
python host_metrics.py --target example.com --verbose
```

## Output Format

The tool outputs data in JSON format with the following structure:

```json
{
  "timestamp": "2023-05-10T08:15:30.123456",
  "target": "example.com",
  "primary_target": {
    "ip": "93.184.216.34",
    "status": "online",
    "timestamp": "2023-05-10T08:15:30.123456",
    "connection_quality": "excellent",
    "rtt_stats": {
      "min_ms": 45.6,
      "avg_ms": 48.2,
      "max_ms": 52.8,
      "mdev_ms": 2.5
    },
    "icmp_details": [
      {
        "sequence": 1,
        "response_time_ms": 45.6
      },
      ...
    ],
    "packet_loss_percent": 0.0,
    "packets": {
      "transmitted": 5,
      "received": 5
    },
    "raw_output": "...",
    "error": null,
    "tls_info": {
      "certificate": "...",
      "expiry": "2024-05-10T12:00:00",
      "issuer": "CN=DigiCert TLS RSA SHA256 2020 CA1, O=DigiCert Inc, C=US",
      "subject": "CN=example.com, O=Example Inc, L=Los Angeles, ST=California, C=US",
      "version": "TLSv1.3",
      "cipher": "TLS_AES_256_GCM_SHA384 (TLSv1.3, 256 bits)"
    }
  }
}
```

## Connection Quality Criteria

The connection quality is assessed based on packet loss:

- **Excellent**: 0% packet loss
- **Good**: < 5% packet loss
- **Fair**: < 20% packet loss
- **Poor**: >= 20% packet loss

## Requirements

- Python 3.6+
- Standard Linux utilities (ping, openssl)

## API Usage

You can also use the module in your own Python code:

```python
from host_monitor import HostPingMonitor

# Create a monitor for a specific target
monitor = HostPingMonitor("example.com")

# Collect metrics
metrics = monitor.collect()

# Access specific metrics
status = metrics["primary_target"]["status"]
rtt = metrics["primary_target"]["rtt_stats"]["avg_ms"]
```
