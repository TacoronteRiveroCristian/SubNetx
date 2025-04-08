"""
Host TLS Certificate Checker.

This module provides functionality to check TLS certificates on target hosts.
"""

import json
import re
import socket
import ssl
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict


class TlsInfo(TypedDict):
    """TLS information structure."""
    certificate: Optional[str]
    expiry: Optional[str]
    issuer: Optional[str]
    subject: Optional[str]
    version: Optional[str]
    cipher: Optional[str]


class TlsChecker:
    """TLS Certificate checker for hosts.

    This class provides methods to retrieve TLS certificate information
    from hosts using both Python's ssl module and OpenSSL command-line tool.
    """

    def __init__(self, target: str):
        """Initialize the TLS Checker.

        Args:
            target: Target hostname or IP address
        """
        self.target = target

    def is_hostname(self, target: str) -> bool:
        """Check if the target is a hostname (not an IP address).

        Args:
            target: Target to check

        Returns:
            True if target is a hostname, False if it's an IP address
        """
        # Simple check if the target contains only digits and dots
        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if ip_pattern.match(target):
            return False
        return True

    def check_tls(self, hostname: str, port: int = 443) -> TlsInfo:
        """Check TLS certificate information for the target host.

        Args:
            hostname: Hostname to check TLS for
            port: Port to check TLS on, defaults to 443

        Returns:
            Dictionary containing TLS certificate information
        """
        tls_info = self._check_tls_with_ssl_module(hostname, port)

        # If SSL module method failed to get meaningful data, try OpenSSL command
        if tls_info.get("certificate") is None:
            print(f"SSL module method failed, trying OpenSSL command for {hostname}:{port}")
            tls_info = self._check_tls_with_openssl(hostname, port)

        return tls_info

    def get_tls_info(self) -> TlsInfo:
        """Get TLS information for the configured target.

        Returns:
            TLS information dictionary
        """
        # Only try to get TLS info if target is a hostname, not an IP
        if self.is_hostname(self.target):
            try:
                # Try with the default HTTPS port
                return self.check_tls(self.target)
            except Exception as e:
                print(f"Error getting TLS info for {self.target}: {e}")
                return self._get_default_tls_info()

        # Return empty TLS info for IP addresses
        return self._get_default_tls_info()

    def _get_default_tls_info(self) -> TlsInfo:
        """Get default (empty) TLS information structure.

        Returns:
            Empty TLS information dictionary
        """
        return {
            "certificate": None,
            "expiry": None,
            "issuer": None,
            "subject": None,
            "version": None,
            "cipher": None,
        }

    def _check_tls_with_ssl_module(self, hostname: str, port: int = 443) -> TlsInfo:
        """Check TLS using Python's ssl module.

        Args:
            hostname: Hostname to check TLS for
            port: Port to check TLS on

        Returns:
            TLS info dictionary
        """
        try:
            # Create a secure SSL context
            context = ssl.create_default_context()

            # Establish connection and wrap with SSL
            print(f"Connecting to {hostname}:{port} using SSL module...")
            with socket.create_connection(
                (hostname, port), timeout=5
            ) as sock, context.wrap_socket(
                sock, server_hostname=hostname
            ) as ssock:
                # Get the certificate details
                cert = ssock.getpeercert()

                # Get information about the TLS connection
                cipher = ssock.cipher()
                version = ssock.version()

                # Check if certificate exists
                if not cert:
                    raise ValueError("No certificate found")

                # Process certificate data
                expiry = None
                issuer = None
                subject = None

                try:
                    # Format expiry date
                    expiry_str = cert.get("notAfter", "")
                    if expiry_str and isinstance(expiry_str, str):
                        expiry = datetime.strptime(
                            expiry_str, "%b %d %H:%M:%S %Y %Z"
                        ).isoformat()
                except (ValueError, TypeError) as e:
                    print(f"Error parsing certificate expiry date: {e}")

                # Format certificate issuer in a human-readable way
                try:
                    if "issuer" in cert:
                        issuer_raw: Any = cert.get("issuer", [])
                        issuer = self._format_certificate_dn(issuer_raw)
                except Exception as e:
                    print(f"Error processing certificate issuer: {e}")
                    issuer = json.dumps(cert.get("issuer", []))

                # Format certificate subject in a human-readable way
                try:
                    if "subject" in cert:
                        subject_raw: Any = cert.get("subject", [])
                        subject = self._format_certificate_dn(subject_raw)
                except Exception as e:
                    print(f"Error processing certificate subject: {e}")
                    subject = json.dumps(cert.get("subject", []))

                # Format cipher in a human-readable way
                cipher_str = None
                if cipher:
                    try:
                        # The cipher tuple contains (cipher_name, tls_version, secret_bits)
                        if len(cipher) >= 3:
                            cipher_name, cipher_version, cipher_bits = cipher[:3]
                            cipher_str = f"{cipher_name} ({cipher_version}, {cipher_bits} bits)"
                        else:
                            # Convert cipher to string directly to avoid iteration issues
                            cipher_str = str(cipher)
                    except Exception as e:
                        print(f"Error formatting cipher: {e}")
                        cipher_str = json.dumps(cipher)

                # Return complete TLS information
                return {
                    "certificate": json.dumps(cert) if cert else None,
                    "expiry": expiry,
                    "issuer": issuer,
                    "subject": subject,
                    "version": version,
                    "cipher": cipher_str,
                }
        except socket.gaierror:
            print(f"DNS resolution failed for {hostname}")
        except socket.timeout:
            print(f"Connection timed out for {hostname}")
        except ssl.SSLError as e:
            print(f"SSL error when connecting to {hostname}: {e}")
        except ConnectionRefusedError:
            print(f"Connection refused for {hostname}:{port}")
        except Exception as e:
            print(f"TLS check failed for {hostname}: {e}")

        return self._get_default_tls_info()

    def _check_tls_with_openssl(self, hostname: str, port: int = 443) -> TlsInfo:
        """Check TLS using OpenSSL command.

        Args:
            hostname: Hostname to check TLS for
            port: Port to check TLS on

        Returns:
            TLS info dictionary
        """
        try:
            # Run OpenSSL command to get certificate info
            cmd = f"echo | openssl s_client -connect {hostname}:{port} -servername {hostname} 2>/dev/null | openssl x509 -text"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"OpenSSL command failed for {hostname}: {result.stderr}")
                return self._get_default_tls_info()

            cert_text = result.stdout

            # Extract certificate information
            issuer = self._extract_openssl_field(cert_text, "Issuer:")
            subject = self._extract_openssl_field(cert_text, "Subject:")

            # Extract validity dates
            not_after = self._extract_openssl_field(cert_text, "Not After:")
            expiry = self._format_openssl_date(not_after) if not_after else None

            # Get cipher and TLS version
            cipher_cmd = f"echo | openssl s_client -connect {hostname}:{port} -servername {hostname} 2>/dev/null | grep 'Protocol\\|Cipher'"
            cipher_result = subprocess.run(cipher_cmd, shell=True, capture_output=True, text=True)

            version = None
            cipher = None

            if cipher_result.returncode == 0:
                for line in cipher_result.stdout.splitlines():
                    if "Protocol" in line:
                        version = line.split(":")[-1].strip()
                    elif "Cipher" in line and "Cipher is" in line:
                        cipher = line.split("Cipher is")[-1].strip()

            return {
                "certificate": cert_text if cert_text else None,
                "expiry": expiry,
                "issuer": issuer,
                "subject": subject,
                "version": version,
                "cipher": cipher,
            }
        except Exception as e:
            print(f"Error checking TLS with OpenSSL for {hostname}: {e}")
            return self._get_default_tls_info()

    def _extract_openssl_field(self, text: str, field_prefix: str) -> Optional[str]:
        """Extract a field from OpenSSL output.

        Args:
            text: OpenSSL output text
            field_prefix: Field prefix to search for

        Returns:
            Extracted field value or None
        """
        if not text:
            return None

        for line in text.splitlines():
            if line.strip().startswith(field_prefix):
                return line.split(field_prefix, 1)[1].strip()
        return None

    def _format_openssl_date(self, date_str: str) -> str:
        """Format OpenSSL date string to ISO format.

        Args:
            date_str: Date string from OpenSSL

        Returns:
            Formatted date string
        """
        try:
            if not date_str:
                return ""
            # Example: "May  3 12:00:00 2023 GMT"
            dt = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
            return dt.isoformat()
        except ValueError:
            print(f"Error parsing OpenSSL date: {date_str}")
            return date_str

    def _format_certificate_dn(self, dn_data: Any) -> str:
        """Format Distinguished Name (DN) from certificate data.

        Args:
            dn_data: DN data from certificate

        Returns:
            Formatted DN string
        """
        if not dn_data:
            return ""

        # Common attribute mapping
        key_map = {
            "organizationName": "O",
            "commonName": "CN",
            "countryName": "C",
            "stateOrProvinceName": "ST",
            "localityName": "L",
            "organizationalUnitName": "OU",
            "emailAddress": "E",
            "serialNumber": "SN",
        }

        parts = []

        # Handle different certificate formats
        if isinstance(dn_data, list):
            for item in dn_data:
                self._extract_dn_parts(item, key_map, parts)
        elif isinstance(dn_data, tuple):
            for item in dn_data:
                self._extract_dn_parts(item, key_map, parts)
        elif isinstance(dn_data, dict):
            self._extract_dn_parts(dn_data, key_map, parts)

        return ", ".join(parts) if parts else str(dn_data)

    def _extract_dn_parts(self, item: Any, key_map: Dict[str, str], parts: List[str]) -> None:
        """Extract parts of a Distinguished Name.

        Args:
            item: Item to extract from
            key_map: Mapping of keys
            parts: List to append parts to
        """
        if isinstance(item, tuple) and len(item) >= 2:
            key, value = item[0], item[1]
            if isinstance(key, str):
                short_key = key_map.get(key, key)
                parts.append(f"{short_key}={value}")
            else:
                parts.append(f"{key}={value}")
        elif isinstance(item, list) and len(item) == 2:
            key_items = item[0]
            if isinstance(key_items, list) and len(key_items) > 0:
                for key_item in key_items:
                    if isinstance(key_item, tuple) and len(key_item) >= 2:
                        key, value = key_item[0], key_item[1]
                        short_key = key_map.get(key, key)
                        parts.append(f"{short_key}={value}")
        elif isinstance(item, dict):
            for key, value in item.items():
                short_key = key_map.get(key, key)
                parts.append(f"{short_key}={value}")
