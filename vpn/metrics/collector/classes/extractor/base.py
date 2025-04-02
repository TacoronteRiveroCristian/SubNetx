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
from datetime import datetime
from typing import Any, Dict, TypedDict


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
        try:
            # Create a secure SSL context
            context = ssl.create_default_context()

            # Establish connection and wrap with SSL
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

                # Process certificate issuer
                try:
                    if "issuer" in cert:
                        issuer = json.dumps(cert.get("issuer", []))
                except Exception as e:
                    print(f"Error processing certificate issuer: {e}")

                # Process certificate subject
                try:
                    if "subject" in cert:
                        subject = json.dumps(cert.get("subject", []))
                except Exception as e:
                    print(f"Error processing certificate subject: {e}")

                # Return complete TLS information
                return {
                    "certificate": json.dumps(cert) if cert else None,
                    "expiry": expiry,
                    "issuer": issuer,
                    "subject": subject,
                    "version": version,
                    "cipher": json.dumps(cipher) if cipher else None,
                }
        except socket.gaierror:
            print(f"DNS resolution failed for {hostname}")
            return self._get_default_tls_info()
        except socket.timeout:
            print(f"Connection timed out for {hostname}")
            return self._get_default_tls_info()
        except ssl.SSLError as e:
            print(f"SSL error when connecting to {hostname}: {e}")
            return self._get_default_tls_info()
        except ConnectionRefusedError:
            print(f"Connection refused for {hostname}:{port}")
            return self._get_default_tls_info()
        except Exception as e:
            print(f"TLS check failed for {hostname}: {e}")
            return self._get_default_tls_info()

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
            # Try standard HTTPS port first
            tls_info = self.check_tls(self.target)

            # If certificate is still None, try common alternative ports
            if tls_info.get("certificate") is None:
                for alt_port in [8443, 4443]:
                    try:
                        tls_info = self.check_tls(self.target, alt_port)
                        if tls_info.get("certificate") is not None:
                            break
                    except Exception:
                        pass

            return tls_info
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
