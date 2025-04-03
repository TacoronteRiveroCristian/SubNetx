"""
SubNetx VPN Base Monitor.

This module provides the base class for all VPN monitoring collectors.

It implements common functionality like TLS verification, and other
shared utilities that are used across different collector types.
"""

import json
import re
import socket
import ssl
import subprocess
from datetime import datetime
from typing import Any, Dict, List, TypedDict


class TlsInfo(TypedDict):
    certificate: str | None
    expiry: str | None
    issuer: str | None
    subject: str | None
    version: str | None
    cipher: str | None


class BaseMonitor:
    """Base class for all VPN monitoring collectors.

    This class provides common functionality for all monitor classes
    including logging setup, TLS verification, and utility methods.

    :param target: Target hostname or IP address to monitor
    :type target: str
    :ivar target: Target hostname or IP address being monitored
    :ivar timestamp: Current timestamp when monitor was initialized
    """

    def __init__(self, target: str):
        """Initialize the Base Monitor.

        :param target: Target hostname or IP address to monitor
        :type target: str
        """
        # Setup basic attributes
        self.target = target
        self.timestamp = datetime.now()

    def check_tls(self, hostname: str, port: int = 443) -> TlsInfo:
        """Check TLS certificate information for the target host.

        Attempts to establish a TLS connection to the target host and
        retrieves certificate information.

        :param hostname: Hostname to check TLS for
        :type hostname: str
        :param port: Port to check TLS on, defaults to 443
        :type port: int, optional
        :return: Dictionary containing TLS certificate information including version,
                cipher, expiry date, issuer and subject. Returns error information if check fails.
        :rtype: TlsInfo
        :raises: Various socket and SSL exceptions may be caught and logged
        """
        tls_info = self._check_tls_with_ssl_module(hostname, port)

        # If SSL module method failed to get meaningful data, try OpenSSL command
        if tls_info.get("certificate") is None:
            print(f"SSL module method failed, trying OpenSSL command for {hostname}:{port}")
            tls_info = self._check_tls_with_openssl(hostname, port)

        return tls_info

    def _check_tls_with_ssl_module(self, hostname: str, port: int = 443) -> TlsInfo:
        """Check TLS using Python's ssl module.

        :param hostname: Hostname to check TLS for
        :type hostname: str
        :param port: Port to check TLS on
        :type port: int
        :return: TLS info dictionary
        :rtype: TlsInfo
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
                        # Format issuer data into a readable string
                        issuer_raw: Any = cert.get("issuer", [])
                        issuer_formatted = self._format_certificate_dn(issuer_raw)
                        if issuer_formatted:
                            issuer = issuer_formatted
                        else:
                            # Fallback to JSON if formatting fails
                            issuer = json.dumps(issuer_raw)
                except Exception as e:
                    print(f"Error processing certificate issuer: {e}")
                    # Fallback to raw JSON
                    issuer = json.dumps(cert.get("issuer", []))

                # Format certificate subject in a human-readable way
                try:
                    if "subject" in cert:
                        # Format subject data into a readable string
                        subject_raw: Any = cert.get("subject", [])
                        subject_formatted = self._format_certificate_dn(subject_raw)
                        if subject_formatted:
                            subject = subject_formatted
                        else:
                            # Fallback to JSON if formatting fails
                            subject = json.dumps(subject_raw)
                except Exception as e:
                    print(f"Error processing certificate subject: {e}")
                    # Fallback to raw JSON
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

        Attempts to use the openssl command-line tool to gather certificate information
        when the Python SSL module fails.

        :param hostname: Hostname to check TLS for
        :type hostname: str
        :param port: Port to check TLS on
        :type port: int
        :return: TLS info dictionary
        :rtype: TlsInfo
        """
        try:
            # Use OpenSSL to get certificate info
            print(f"Using OpenSSL command for {hostname}:{port}")
            cmd = ["openssl", "s_client", "-connect", f"{hostname}:{port}", "-servername", hostname, "-showcerts"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input="\n", timeout=10)

            if process.returncode != 0:
                print(f"OpenSSL command failed: {stderr}")
                return self._get_default_tls_info()

            # Parse certificate information
            expiry = self._extract_openssl_field(stdout, "notAfter=")
            issuer = self._extract_openssl_field(stdout, "issuer=")
            subject = self._extract_openssl_field(stdout, "subject=")

            # Clean up issuer and subject strings for better readability
            if issuer:
                issuer = self._format_openssl_dn(issuer)

            if subject:
                subject = self._format_openssl_dn(subject)

            # Extract protocol version
            version_match = re.search(r"Protocol\s*:\s*(TLSv[\d\.]+)", stdout)
            version = version_match.group(1) if version_match else None

            # Extract cipher
            cipher_match = re.search(r"Cipher\s*:\s*([^\s]+)", stdout)
            cipher_name = cipher_match.group(1) if cipher_match else None

            # Try to get additional cipher info
            cipher_bits_match = re.search(r"Server public key is (\d+) bit", stdout)
            cipher_bits = cipher_bits_match.group(1) if cipher_bits_match else None

            # Format cipher string
            cipher = cipher_name
            if cipher_bits:
                cipher = f"{cipher_name} ({cipher_bits} bits)"

            # Return certificate information
            return {
                "certificate": json.dumps({"raw_cert": "OpenSSL extracted certificate"}),
                "expiry": self._format_openssl_date(expiry) if expiry else None,
                "issuer": issuer,
                "subject": subject,
                "version": version,
                "cipher": cipher,
            }

        except subprocess.TimeoutExpired:
            print(f"OpenSSL command timed out for {hostname}:{port}")
        except FileNotFoundError:
            print("OpenSSL command not found on the system")
        except Exception as e:
            print(f"Failed to get certificate using OpenSSL: {e}")

        return self._get_default_tls_info()

    def _format_openssl_dn(self, dn_string: str) -> str:
        """Format Distinguished Name string to be more readable.

        :param dn_string: DN string from OpenSSL
        :type dn_string: str
        :return: Formatted readable string
        :rtype: str
        """
        # Convert cryptic abbreviations to more readable names
        replacements = {
            "/C=": "Country=",
            "/ST=": "State=",
            "/L=": "Locality=",
            "/O=": "Organization=",
            "/OU=": "Organizational Unit=",
            "/CN=": "Common Name=",
            "/emailAddress=": "Email=",
        }

        result = dn_string
        for abbr, full in replacements.items():
            result = result.replace(abbr, full + ", ")

        # Remove leading slash and trailing comma if present
        result = result.lstrip("/").rstrip(", ")
        return result

    def _extract_openssl_field(self, text: str, field_prefix: str) -> str | None:
        """Extract field from OpenSSL output.

        :param text: OpenSSL output text
        :type text: str
        :param field_prefix: Field prefix to look for
        :type field_prefix: str
        :return: Extracted field value or None
        :rtype: str or None
        """
        pattern = re.escape(field_prefix) + r"([^\n]+)"
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    def _format_openssl_date(self, date_str: str) -> str:
        """Format OpenSSL date to ISO format.

        :param date_str: Date string from OpenSSL
        :type date_str: str
        :return: ISO formatted date or original string if parsing fails
        :rtype: str
        """
        try:
            # Typical format: "May 17 12:00:00 2024 GMT"
            if date_str:
                dt = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
                return dt.isoformat()
        except ValueError:
            print(f"Could not parse date: {date_str}")
        return date_str

    def _get_default_tls_info(self) -> TlsInfo:
        """Return default TLS information structure with null values.

        :return: Default TLS information dictionary
        :rtype: TlsInfo
        """
        return {
            "certificate": None,
            "expiry": None,
            "issuer": None,
            "subject": None,
            "version": None,
            "cipher": None,
        }

    def is_hostname(self, target: str) -> bool:
        """Check if target is a hostname or IP address.

        :param target: Target to check
        :type target: str
        :return: True if target is a hostname, False if it's an IP address
        :rtype: bool
        """
        # Simple IP address pattern matching
        return not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", target)

    def get_tls_info(self) -> TlsInfo:
        """Get TLS information for the target if it's a hostname.

        :return: TLS information or empty dict if target is an IP
        :rtype: TlsInfo
        """
        if self.is_hostname(self.target):
            import socket

            # Try standard HTTPS port first
            tls_info = self.check_tls(self.target)

            # If certificate is still None, try common alternative ports
            if tls_info.get("certificate") is None:
                print(f"TLS check failed on standard port for {self.target}, trying alternatives")
                for alt_port in [8443, 4443]:
                    try:
                        print(f"Checking port {alt_port} for {self.target}")
                        tls_info = self.check_tls(self.target, alt_port)
                        if tls_info.get("certificate") is not None:
                            print(f"Successfully obtained TLS info on port {alt_port}")
                            break
                    except Exception as e:
                        print(f"Error checking port {alt_port}: {e}")

            return tls_info

        print(f"Target {self.target} is an IP address, no TLS information will be collected")
        return self._get_default_tls_info()

    def _format_bytes(self, bytes_value: float) -> str:
        """Format bytes to human-readable format (KB, MB, GB).

        :param bytes_value: Bytes value to format
        :type bytes_value: float
        :return: Formatted string with appropriate units
        :rtype: str
        """
        if bytes_value is None or bytes_value < 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0

        # Convert to appropriate unit
        while bytes_value >= 1024 and unit_index < len(units) - 1:
            bytes_value /= 1024
            unit_index += 1

        return f"{bytes_value:.2f} {units[unit_index]}"

    def get_basic_result(self) -> Dict[str, Any]:
        """Get basic result dictionary with common fields.

        :return: Dictionary with timestamp and target
        :rtype: Dict[str, Any]
        """
        return {"timestamp": datetime.now().isoformat(), "target": self.target}

    def collect(self) -> Dict[str, Any]:
        """Collect metrics - to be implemented by subclasses.

        This method must be implemented by each subclass to collect
        the specific metrics relevant to that collector.

        :return: Collection results
        :rtype: Dict[str, Any]
        :raises NotImplementedError: If subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement collect()")

    def _format_certificate_dn(self, dn_data: Any) -> str:
        """Format certificate Distinguished Name data into a readable string.

        :param dn_data: Distinguished Name data from certificate
        :type dn_data: Any
        :return: Formatted readable string
        :rtype: str
        """
        # Map common abbreviations to more readable names
        key_map = {
            "C": "Country",
            "ST": "State",
            "L": "Locality",
            "O": "Organization",
            "OU": "Organizational Unit",
            "CN": "Common Name",
            "countryName": "Country",
            "stateOrProvinceName": "State",
            "localityName": "Locality",
            "organizationName": "Organization",
            "organizationalUnitName": "Organizational Unit",
            "commonName": "Common Name",
            "emailAddress": "Email",
        }

        try:
            # Extract key-value pairs from the DN data structure
            parts: List[str] = []

            # Handle different data structures that might be in the certificate
            if isinstance(dn_data, list) or isinstance(dn_data, tuple):
                # Process nested structures
                for item in dn_data:
                    # Process each item which might be a tuple or list
                    self._extract_dn_parts(item, key_map, parts)

            # Join the parts into a comma-separated string
            if parts:
                return ", ".join(parts)

            # If we couldn't extract any parts, fallback to string representation
            return str(dn_data)

        except Exception as e:
            print(f"Error formatting DN data: {e}")
            return str(dn_data)

    def _extract_dn_parts(self, item: Any, key_map: Dict[str, str], parts: List[str]) -> None:
        """Helper method to extract DN parts from certificate data.

        :param item: Item from DN data to process
        :type item: Any
        :param key_map: Mapping of abbreviations to readable names
        :type key_map: Dict[str, str]
        :param parts: List to add extracted parts to
        :type parts: List[str]
        """
        if isinstance(item, list) or isinstance(item, tuple):
            # Process nested list/tuple
            for subitem in item:
                self._extract_dn_parts(subitem, key_map, parts)
        elif isinstance(item, tuple) and len(item) == 2:
            # This is a key-value pair
            key, value = item
            readable_key = key_map.get(str(key), str(key))
            parts.append(f"{readable_key}={value}")
        # Ignore other types of items
