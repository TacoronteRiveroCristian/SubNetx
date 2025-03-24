# SubNetx System Patterns

## System Architecture

SubNetx follows a containerized architecture with several key components:

```
┌────────────────────────────────────────────────┐
│                Docker Container                │
│                                                │
│  ┌─────────────┐       ┌───────────────────┐  │
│  │             │       │                   │  │
│  │  OpenVPN    │◄─────►│  iptables/NAT     │  │
│  │  Server     │       │  Configuration    │  │
│  │             │       │                   │  │
│  └─────┬───────┘       └───────────────────┘  │
│        │                                       │
│        ▼                                       │
│  ┌─────────────┐       ┌───────────────────┐  │
│  │             │       │                   │  │
│  │  Easy-RSA   │◄─────►│  Client Config    │  │
│  │  PKI        │       │  Management       │  │
│  │             │       │                   │  │
│  └─────────────┘       └───────────────────┘  │
│                                                │
│  ┌────────────────────────────────────────┐   │
│  │                                        │   │
│  │        Terminal Interface (CLI)        │   │
│  │                                        │   │
│  └────────────────────────────────────────┘   │
│                                                │
└────────────────────────────────────────────────┘
```

## Component Relationships

### 1. Core Components
- **OpenVPN Server**: The main VPN service that handles client connections
- **Easy-RSA PKI**: Public Key Infrastructure for certificate management
- **iptables/NAT Configuration**: Network routing and forwarding rules
- **Client Configuration Management**: Handles .ovpn file generation
- **Terminal Interface**: Interactive shell for managing all components

### 2. Data Flow
- Environment variables → Configuration scripts → OpenVPN configuration
- Terminal commands → Shell scripts → Component operations
- Client requests → OpenVPN server → NAT/routing → Internet
- Certificate generation → Client configuration files → Distribution

## Design Patterns

### 1. Command Pattern
The system uses a command pattern through shell scripts, where each operation (setup, start, stop, client-new, client-delete) is encapsulated in individual script files that can be invoked independently.

### 2. Facade Pattern
The `subnetx` command serves as a facade, providing a simplified interface to the complex underlying operations and hiding implementation details from users.

### 3. Environment-based Configuration
Configuration is externalized through environment variables, allowing for flexible deployment without code modifications.

### 4. Volume-based Persistence
Client certificates and configurations are persisted through Docker volumes, ensuring data survival across container restarts or replacements.

### 5. Modular Shell Scripts
Each functionality is implemented in separate shell scripts that focus on specific tasks, improving maintainability and reducing complexity.

## Key Technical Decisions

### 1. Containerization
- Using Docker to provide isolation and standardized deployment
- Container includes all necessary dependencies and tools

### 2. Bash-based Implementation
- Shell scripts for core functionality rather than a higher-level language
- Reduces dependencies and simplifies the execution environment
- Leverages standard Unix tools available in the container

### 3. Docker Networking
- Using host networking with port exposure for VPN traffic
- NAT configuration within the container for client routing

### 4. Security Considerations
- PKI-based authentication with OpenVPN
- Isolation of VPN instances through separate containers
- Proper permission settings for sensitive files

## Architectural Constraints

1. **Container Capabilities**: Requires NET_ADMIN capability and TUN device access
2. **Port Availability**: Requires available UDP/TCP ports on the host
3. **NAT Configuration**: Requires proper configuration for client internet access
4. **Storage Persistence**: Depends on Docker volumes for certificate persistence
