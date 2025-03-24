# SubNetx Technical Context

## Technologies Used

### 1. Core Technologies
- **Docker**: Container platform for application packaging and deployment
- **Ubuntu 22.04**: Base operating system for the container
- **OpenVPN**: Open-source VPN implementation
- **Easy-RSA**: PKI management tools for certificate creation and management
- **iptables**: Linux firewall and NAT configuration tool
- **Bash**: Shell scripting language for the command-line interface and automation

### 2. Supporting Technologies
- **Docker Compose**: Multi-container Docker application orchestration
- **Python**: Used for metrics collection (optional component)
- **Whiptail**: Terminal-based dialog boxes for the interactive interface
- **Expect**: Automation tool for interactive command scripts
- **socat**: Multipurpose relay for bidirectional data transfer

## Development Setup

### Requirements
- Docker Engine 20.10.0+
- Docker Compose v2.0.0+ (optional, for multi-container deployment)
- Bash shell environment
- Git (for source code management)
- Linux environment with support for:
  - TUN/TAP devices
  - NET_ADMIN capabilities

### Development Environment Configuration
1. Clone the repository
2. Set up environment variables in `.env` file
3. Build the Docker image using provided Dockerfile
4. Test deployment using Docker Compose

### Testing Procedures
- Manual testing of VPN connection establishment
- Client configuration generation verification
- Network routing tests for client traffic
- Container restart persistence tests

## Technical Constraints

### 1. Docker Constraints
- Must run with `--cap-add=NET_ADMIN` for network configuration
- Requires `/dev/net/tun` device access
- Port mapping needed for VPN service exposure

### 2. Networking Constraints
- Router port forwarding required for external access
- Subnet ranges should not overlap with existing networks
- UDP/TCP ports must be available on the host

### 3. Security Considerations
- Certificate generation requires proper entropy sources
- Private keys must be protected with appropriate permissions
- Configuration files should not be world-readable

### 4. File System Constraints
- Persistent volumes needed for certificate storage
- Permission requirements for OpenVPN configuration files

## Dependencies

### 1. Runtime Dependencies
- **OpenVPN**: Core VPN functionality
- **Easy-RSA**: Certificate management
- **iptables**: Network routing and NAT
- **Bash**: Script execution
- **Whiptail**: Terminal UI
- **Expect**: Interactive automation

### 2. Build Dependencies
- **Docker Build Tools**: For image creation
- **Git**: Source code management

### 3. Optional Dependencies
- **Python 3**: For metrics collection
- **DuckDNS**: For dynamic DNS updates (if used)

## Configuration Parameters

### 1. Essential Environment Variables
- `VPN_NETWORK`: VPN subnet network address (e.g., 10.8.0.0)
- `VPN_NETMASK`: VPN subnet mask (e.g., 255.255.255.0)
- `OPENVPN_PORT`: Port for OpenVPN service (default: 1194)
- `OPENVPN_PROTO`: Protocol for OpenVPN (udp/tcp)
- `TUN_DEVICE`: TUN device name (default: tun0)
- `PUBLIC_IP`: Public domain or IP for client configurations

### 2. Optional Environment Variables
- `DUCKDNS_TOKEN`: Token for DuckDNS dynamic DNS updates
- Custom certificate parameters (country, province, etc.)

## Deployment Considerations

### 1. Single-Container Deployment
- Uses standard Docker run commands
- Requires volume mapping for persistence
- Needs port exposure and network capabilities

### 2. Multi-Container Deployment
- Uses Docker Compose for orchestration
- Supports multiple VPN subnets through separate service definitions
- Requires careful port mapping to avoid conflicts
