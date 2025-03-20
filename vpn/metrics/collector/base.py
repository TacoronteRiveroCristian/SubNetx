#!/usr/bin/env python3
"""
SubNetx VPN Base Monitor

This module provides the base class for all VPN monitoring collectors.

It implements common functionality like TLS verification, and other
shared utilities that are used across different collector types.
"""


import ssl
import socket
import re
from datetime import datetime
from typing import Dict, Any

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

    def check_tls(self, hostname: str, port: int = 443) -> Dict[str, Any]:
        """Check TLS certificate information for the target host.

        Attempts to establish a TLS connection to the target host and
        retrieves certificate information.

        :param hostname: Hostname to check TLS for
        :type hostname: str
        :param port: Port to check TLS on, defaults to 443
        :type port: int, optional
        :return: Dictionary containing TLS certificate information including version,
                cipher, expiry date, issuer and subject. Returns error information if check fails.
        :rtype: Dict[str, Any]
        :raises: Various socket and SSL exceptions may be caught and logged
        """
        try:
            # Create a secure SSL context
            context = ssl.create_default_context()

            # Establish connection and wrap with SSL
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Get the certificate details
                    cert = ssock.getpeercert()

                    # Return TLS information
                    return {
                        'tls_version': ssock.version(),
                        'cipher': ssock.cipher(),
                        'cert_expiry': datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z').isoformat(),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'subject': dict(x[0] for x in cert['subject'])
                    }
        except Exception as e:
            print(f"TLS check failed for {hostname}: {e}")
            return {
                'tls_version': None,
                'cipher': None,
                'cert_expiry': None,
                'issuer': None,
                'subject': None,
                'error': str(e)
            }

    def is_hostname(self, target: str) -> bool:
        """Check if target is a hostname or IP address.

        :param target: Target to check
        :type target: str
        :return: True if target is a hostname, False if it's an IP address
        :rtype: bool
        """
        # Simple IP address pattern matching
        return not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', target)

    def get_tls_info(self) -> Dict[str, Any]:
        """Get TLS information for the target if it's a hostname.

        :return: TLS information or empty dict if target is an IP
        :rtype: Dict[str, Any]
        """
        if self.is_hostname(self.target):
            return self.check_tls(self.target)
        return {}

    def _format_bytes(self, bytes_value: float) -> str:
        """Format bytes to human-readable format (KB, MB, GB).

        :param bytes_value: Bytes value to format
        :type bytes_value: float
        :return: Formatted string with appropriate units
        :rtype: str
        """
        if bytes_value is None or bytes_value < 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB', 'TB']
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
        return {
            'timestamp': datetime.now().isoformat(),
            'target': self.target
        }

    def collect(self) -> Dict[str, Any]:
        """Collect metrics - to be implemented by subclasses.

        This method must be implemented by each subclass to collect
        the specific metrics relevant to that collector.

        :return: Collection results
        :rtype: Dict[str, Any]
        :raises NotImplementedError: If subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement collect()")
