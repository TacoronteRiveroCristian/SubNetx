# SubNetx VPN Monitoring System

This component of SubNetx provides comprehensive monitoring capabilities for the VPN server and its clients.

## Features

- **Ping Monitoring**: Tracks client connectivity and latency
- **Traffic Monitoring**: Monitors data transfer rates and usage
- **Status Monitoring**: Tracks connection states and events
- **Event Logging**: Records important events and state changes
- **JSON Output**: Exports monitoring data in JSON format

## Directory Structure

```
metrics/
├── collector/           # Monitoring scripts
│   ├── main.py         # Main orchestrator
│   ├── ping.py         # Ping monitoring
│   ├── traffic.py      # Traffic monitoring
│   └── status.py       # Status monitoring
├── Dockerfile          # Container definition
└── requirements.txt    # Python dependencies
```

## Log Files

The monitoring system generates several log files:

- `/var/log/subnetx/monitor.log`: Main monitoring system logs
- `/var/log/subnetx/ping_monitor.log`: Ping monitoring logs
- `/var/log/subnetx/traffic_monitor.log`: Traffic monitoring logs
- `/var/log/subnetx/status_monitor.log`: Status monitoring logs
- `/var/log/subnetx/client_stats.json`: Client statistics
- `/var/log/subnetx/traffic_stats.json`: Traffic statistics
- `/var/log/subnetx/status_stats.json`: Status and events

## Data Format

### Client Statistics
```json
{
  "ip": {
    "name": "client_name",
    "ip": "10.8.0.2",
    "real_ip": "1.2.3.4",
    "last_seen": "2024-03-20T10:30:45",
    "status": "connected",
    "timestamp": "2024-03-20T10:30:45"
  }
}
```

### Traffic Statistics
```json
{
  "ip": {
    "name": "client_name",
    "ip": "10.8.0.2",
    "real_ip": "1.2.3.4",
    "last_seen": "2024-03-20T10:30:45",
    "bytes_received": 1024000,
    "bytes_sent": 512000,
    "total_traffic": 1536000,
    "timestamp": "2024-03-20T10:30:45"
  }
}
```

### Status and Events
```json
{
  "clients": {
    "ip": {
      "name": "client_name",
      "ip": "10.8.0.2",
      "real_ip": "1.2.3.4",
      "last_seen": "2024-03-20T10:30:45",
      "status": "connected",
      "timestamp": "2024-03-20T10:30:45"
    }
  },
  "events": [
    {
      "timestamp": "2024-03-20T10:30:45",
      "type": "connected",
      "client": "client_name",
      "message": "Client connected"
    }
  ]
}
```

## Development

### Prerequisites

- Python 3.11+
- Docker
- Docker Compose

### Local Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run tests:
   ```bash
   pytest
   ```

### Docker Development

1. Build the container:
   ```bash
   docker-compose build subnetx-monitor
   ```

2. Run the container:
   ```bash
   docker-compose up subnetx-monitor
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
