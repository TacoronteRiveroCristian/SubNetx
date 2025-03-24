# SubNetx Project Brief

## Project Overview
SubNetx is a Docker container manager for OpenVPN, providing an optimized solution for configuring and administering VPN servers securely and efficiently. Each container deploys an independent VPN subnet, facilitating network segmentation for different projects or environments.

## Core Requirements
1. Create a Docker image based on Ubuntu 22.04 that includes OpenVPN, Easy-RSA, iptables, and other essential tools
2. Develop an interactive terminal interface for easy OpenVPN management
3. Implement automated configuration through environment variables
4. Support VPN client management (creation, deletion)
5. Configure iptables for NAT and packet forwarding
6. Enable deployment through Docker Compose
7. Support multiple independent VPN subnets through separate containers

## Key Features
- **Ubuntu 22.04 Base**: Modern and well-supported OS foundation
- **Interactive Terminal Interface**: Simplified VPN management without complex commands
- **Environment-based Configuration**: Automated setup through variables
- **Client Management**: Tools for adding and removing VPN clients
- **NAT and Forwarding**: Network configuration for proper VPN routing
- **Docker Compose Support**: Easy deployment of one or multiple VPN instances
- **Independent Subnets**: Ability to run multiple isolated VPNs with separate configurations

## Project Goals
- Create a user-friendly solution for OpenVPN deployment
- Enable network segmentation through multiple VPN instances
- Provide secure and efficient VPN configuration
- Minimize manual configuration steps
- Support scalable deployment options

## Project Constraints
- Must run as a Docker container with appropriate capabilities
- Must support multiple operating environments (behind NAT, direct internet)
- Must maintain security best practices for VPN configuration
