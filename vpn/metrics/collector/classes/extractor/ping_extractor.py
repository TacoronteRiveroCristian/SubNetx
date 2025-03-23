"""
SubNetx VPN Client Ping Monitor

This module provides functionality to monitor VPN client connectivity
through ICMP ping tests, measuring latency, packet loss, and response times.
It serves as the primary tool for basic connectivity assessment.

JSON Response Format:
{
    "timestamp": "ISO-8601 timestamp of the measurement",
    "target": "Target hostname or IP being monitored",
    "primary_target": {
        "ip": "IP address of the target",
        "status": "Connection status ('online', 'offline', or 'timeout')",
        "timestamp": "ISO-8601 timestamp of the ping test",
        "connection_quality": "Quality assessment ('excellent', 'good', 'fair', 'poor', or 'none')",
        "rtt_stats": {
            "min_ms": "Minimum round-trip time in milliseconds",
            "avg_ms": "Average round-trip time in milliseconds",
            "max_ms": "Maximum round-trip time in milliseconds",
            "mdev_ms": "Mean deviation of round-trip times in milliseconds"
        },
        "icmp_details": [
            {
                "sequence": "ICMP sequence number",
                "response_time_ms": "Response time for this packet in milliseconds"
            }
        ],
        "packet_loss_percent": "Percentage of lost packets (0-100)",
        "packets": {
            "transmitted": "Number of packets sent",
            "received": "Number of packets received"
        },
        "raw_output": "Raw output from the ping command",
        "tls_info": {
            "certificate": "SSL/TLS certificate information (if applicable)",
            "expiry": "Certificate expiration date",
            "issuer": "Certificate issuer details"
        }
    }
}

Metrics Explained:
- status: Overall connection status of the target
- connection_quality: Based on packet loss:
  * excellent: 0% packet loss
  * good: < 5% packet loss
  * fair: < 20% packet loss
  * poor: >= 20% packet loss
- rtt_stats: Round-trip time statistics showing network latency
- packet_loss_percent: Percentage of packets that didn't receive a response
- icmp_details: Detailed information about each ICMP packet sent
- tls_info: SSL/TLS certificate information for HTTPS targets
"""

import json
import logging
import re
import subprocess
from datetime import datetime
from typing import Any, Dict

from vpn.metrics.collector.classes.extractor.base import BaseMonitor


class PingExtractor(BaseMonitor):
    """VPN Ping Extractor for measuring network connectivity and latency.

    This class specializes in ICMP ping-based measurements, providing
    detailed packet loss statistics, response times in milliseconds,
    and connection quality assessment.

    :param target: Target hostname or IP address to monitor
    :type target: str
    :ivar results: Storage for ping test results
    :type results: Dict[str, Dict[str, Any]]
    """

    def __init__(self, target: str) -> None:
        """Initialize the VPN Ping Monitor.

        :param target: Target hostname or IP address to monitor
        :type target: str
        """
        super().__init__(target)
        self.results: Dict[str, Dict[str, Any]] = {}

    def ping_target(self, count: int = 5) -> Dict[str, Any]:
        """Execute a ping test to the target and process the results.

        This method runs the ping command with the specified number of packets
        and parses the output to extract metrics like packet loss, round-trip times,
        and individual ICMP response details.

        :param count: Number of ICMP packets to send, defaults to 5
        :type count: int, optional
        :return: Dictionary with parsed ping metrics and status
        :rtype: Dict[str, Any]
        """
        # Create basic result structure
        result = {
            "ip": self.target,
            "status": "offline",
            "timestamp": datetime.now().isoformat(),
            "connection_quality": "none",
            "rtt_stats": {"min_ms": 0, "avg_ms": 0, "max_ms": 0, "mdev_ms": 0},
            "icmp_details": [],
            "packet_loss_percent": 100,
            "packets": {"transmitted": count, "received": 0},
            "raw_output": "",
        }

        try:
            # Determine the ping command based on the platform
            # The -c option specifies the count, -W sets the timeout in seconds
            cmd = ["ping", "-c", str(count), "-W", "2", self.target]

            # Execute the ping command and capture output using 'with' context manager
            with subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            ) as process:
                stdout, _ = process.communicate()

            # Store the raw output
            result["raw_output"] = stdout

            # Check if the ping was successful (exit code 0)
            if process.returncode == 0:
                result["status"] = "online"

                # Parse packet statistics
                packet_stats = re.search(
                    r"(\d+) packets transmitted, (\d+) received", stdout
                )
                if packet_stats:
                    transmitted = int(packet_stats.group(1))
                    received = int(packet_stats.group(2))
                    result["packets"]["transmitted"] = transmitted
                    result["packets"]["received"] = received

                    # Calculate packet loss percentage
                    if transmitted > 0:
                        packet_loss = 100 - (received / transmitted * 100)
                        result["packet_loss_percent"] = round(packet_loss, 2)

                # Parse RTT statistics
                rtt_stats = re.search(
                    r"min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)",
                    stdout,
                )
                if rtt_stats:
                    result["rtt_stats"]["min_ms"] = float(rtt_stats.group(1))
                    result["rtt_stats"]["avg_ms"] = float(rtt_stats.group(2))
                    result["rtt_stats"]["max_ms"] = float(rtt_stats.group(3))
                    result["rtt_stats"]["mdev_ms"] = float(rtt_stats.group(4))

                # Parse individual ICMP responses
                icmp_responses = re.finditer(
                    r"icmp_seq=(\d+) ttl=\d+ time=(\d+\.\d+) ms", stdout
                )
                for match in icmp_responses:
                    seq = int(match.group(1))
                    time_ms = float(match.group(2))
                    result["icmp_details"].append(
                        {"sequence": seq, "response_time_ms": time_ms}
                    )

                # Determine connection quality based on packet loss
                if result["packet_loss_percent"] == 0:
                    result["connection_quality"] = "excellent"
                elif result["packet_loss_percent"] < 5:
                    result["connection_quality"] = "good"
                elif result["packet_loss_percent"] < 20:
                    result["connection_quality"] = "fair"
                else:
                    result["connection_quality"] = "poor"
            else:
                # If ping command failed, set to timeout
                result["status"] = "timeout"

        except Exception as e:
            # Log the error and return the default offline result
            print(f"Error executing ping to {self.target}: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def collect(self) -> Dict[str, Any]:
        """Collect ping metrics for the target.

        Performs ping tests to measure basic connectivity metrics including
        latency, packet loss, and jitter.

        :return: Dictionary with ping metrics
        :rtype: Dict[str, Any]
        :raises Exception: If collection fails
        """
        try:
            # Start with the basic result structure
            result: Dict[str, Any] = self.get_basic_result()

            # Ping the main target
            ping_result = self.ping_target()

            # Add TLS information for hostnames
            if self.is_hostname(self.target):
                tls_info = self.get_tls_info()
                ping_result["tls_info"] = tls_info

            self.results[self.target] = ping_result
            result["primary_target"] = ping_result

            return result
        except Exception as e:
            print(f"Error in ping collection: {e}")
            raise


# Standalone testing when script is run directly
if __name__ == "__main__":
    # Setup basic logging if running standalone
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)

    # Test the ping monitor
    targets = ["google.com", "invalid.example.domain"]

    for target in targets:
        try:
            logger.info(f"Testing {target}")
            monitor = PingExtractor(target)
            results = monitor.collect()
            logger.info(f"\nResults for {target}:")
            logger.info(json.dumps(results, indent=2))

        except Exception as e:
            logger.error(f"Failed to collect metrics for {target}: {str(e)}")
            logger.error(f"Error details: {e.__class__.__name__}")
