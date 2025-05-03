# OpenVPN Client Management Scripts

This directory contains scripts for managing OpenVPN clients within the SubNetx system.

## Scripts

### 1. `openvpn-client-new.sh`

Creates a new OpenVPN client with a specified name and fixed IP address.

**Usage:**
```bash
./openvpn-client-new.sh --name <client_name> --ip <client_ip>
```

**Requirements:**
- Server must be properly set up (PKI infrastructure initialized)
- Configuration file must exist
- CA certificate and other necessary files must be present

### 2. `openvpn-client-delete.sh`

Deletes an existing OpenVPN client.

**Usage:**
```bash
./openvpn-client-delete.sh <client_name>
```

### 3. `openvpn-client-list-json.sh`

Lists all OpenVPN clients in JSON format.

**Usage:**
```bash
./openvpn-client-list-json.sh
```

### 4. `openvpn-client-verify-pki.sh` (New)

Verifies that the PKI infrastructure is properly initialized before attempting client creation.

**Usage:**
```bash
./openvpn-client-verify-pki.sh
```

**Checks:**
- Configuration file exists (`vpn_config.json`)
- PKI directory is initialized
- Serial file exists (for certificate numbering)
- CA certificate is present
- Server certificate and key exist
- DH parameters file exists
- TLS auth key exists

**Exit Codes:**
- `0`: Success - PKI is properly initialized
- `1`: Failure - PKI is not fully initialized

## Correct Sequence for Client Creation

To avoid errors when creating clients, always follow this sequence:

1. Set up the server:
   ```bash
   curl -X POST http://localhost:9020/server/setup -H "Content-Type: application/json" -d '{...}'
   ```

2. Start the server:
   ```bash
   curl -X POST http://localhost:9020/server/start
   ```

3. Create clients:
   ```bash
   curl -X POST http://localhost:9020/clients/ -H "Content-Type: application/json" -d '{...}'
   ```

Following this sequence ensures that the PKI infrastructure is properly initialized before attempting to create clients.

## Troubleshooting

### Missing Serial File Error

If you encounter an error about a missing serial file, it means the PKI infrastructure hasn't been properly initialized:

```
Error: Serial file not found at [path]/pki/serial
```

**Solution:** Run the server setup endpoint first to initialize the PKI.

### Certificate Generation Errors

If certificate generation fails, it could be due to:
1. Missing PKI infrastructure
2. Permission issues
3. Corrupt PKI directory

**Solution:** Use the verification script to diagnose the specific issue:
```bash
./openvpn-client-verify-pki.sh
```
