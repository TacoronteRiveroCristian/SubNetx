"""
Host Ping Monitor.

This module provides functionality to monitor host connectivity
through ICMP ping tests, measuring latency, packet loss, and response times.
"""

import logging
import re
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from scripts.metrics.config import (
    CHECK_TLS,
    DEFAULT_PING_COUNT,
    DEFAULT_PING_TIMEOUT,
)

from .tls_checker import TlsChecker, TlsInfo

# Configure module logger
logger = logging.getLogger(__name__)


class RttStats(TypedDict):
    """Round-trip time statistics."""

    min_ms: float
    avg_ms: float
    max_ms: float
    mdev_ms: float


class Packets(TypedDict):
    """Packet statistics."""

    transmitted: int
    received: int


class IcmpDetail(TypedDict):
    """Individual ICMP packet detail."""

    sequence: int
    response_time_ms: float


class PingResult(TypedDict):
    """Ping result structure."""

    ip: str
    status: str
    timestamp: str
    connection_quality: str
    rtt_stats: RttStats
    icmp_details: List[IcmpDetail]
    packet_loss_percent: float
    packets: Packets
    raw_output: str
    error: Optional[str]
    tls_info: Optional[TlsInfo]


class HostPingMonitor:
    """Host Ping Monitor for measuring network connectivity and latency.

    This class specializes in ICMP ping-based measurements, providing
    detailed packet loss statistics, response times in milliseconds,
    and connection quality assessment.
    """

    def __init__(self, target: str):
        """Initialize the Host Ping Monitor.

        Args:
            target: Target hostname or IP address to monitor
        """
        self.target = target
        self.tls_checker = TlsChecker(target)

    def ping_target(
        self,
        count: int = DEFAULT_PING_COUNT,
        timeout: int = DEFAULT_PING_TIMEOUT,
    ) -> PingResult:
        """Execute a ping test to the target and process the results.

        Args:
            count: Number of ICMP packets to send, defaults to DEFAULT_PING_COUNT
            timeout: Timeout in seconds for each packet, defaults to DEFAULT_PING_TIMEOUT

        Returns:
            Dictionary with parsed ping metrics and status
        """
        # Create basic result structure
        result: PingResult = {
            "ip": self.target,
            "status": "offline",
            "timestamp": datetime.now().isoformat(),
            "connection_quality": "none",
            "rtt_stats": {"min_ms": 0, "avg_ms": 0, "max_ms": 0, "mdev_ms": 0},
            "icmp_details": [],
            "packet_loss_percent": 100,
            "packets": {"transmitted": count, "received": 0},
            "raw_output": "",
            "error": None,
            "tls_info": None,
        }

        try:
            # Determine the ping command with timeout in seconds
            cmd = ["ping", "-c", str(count), "-W", str(timeout), self.target]

            # Execute the ping command and capture output
            logger.info(f"Executing ping command: {' '.join(cmd)}")
            with subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            ) as process:
                stdout, stderr = process.communicate()

            # Store the raw output
            result["raw_output"] = stdout
            logger.debug(f"Raw ping output: {stdout}")

            # Check if the ping was successful (exit code 0)
            if process.returncode == 0:
                result["status"] = "online"

                # Parse packet statistics
                packet_stats = re.search(
                    r"(\d+)\s+packets\s+transmitted,\s+(\d+)\s+received", stdout
                )
                if packet_stats:
                    transmitted = int(packet_stats.group(1))
                    received = int(packet_stats.group(2))
                    result["packets"]["transmitted"] = transmitted
                    result["packets"]["received"] = received

                    # Calculate packet loss percentage
                    if transmitted > 0:
                        packet_loss = 100.0 - (received / transmitted * 100.0)
                        result["packet_loss_percent"] = round(packet_loss, 2)
                    else:
                        # Default to 100% loss if no packets transmitted
                        result["packet_loss_percent"] = 100.0

                # Parse RTT statistics
                rtt_stats = re.search(
                    r"min/avg/max/mdev\s*=\s*(\d+\.?\d*)/(\d+\.?\d*)/(\d+\.?\d*)/(\d+\.?\d*)",
                    stdout,
                )
                if rtt_stats:
                    result["rtt_stats"]["min_ms"] = float(rtt_stats.group(1))
                    result["rtt_stats"]["avg_ms"] = float(rtt_stats.group(2))
                    result["rtt_stats"]["max_ms"] = float(rtt_stats.group(3))
                    result["rtt_stats"]["mdev_ms"] = float(rtt_stats.group(4))

                # Extract individual ICMP packet details
                self._extract_icmp_details(stdout, result, count)

                # Calculate connection quality based on packet loss
                if result["packet_loss_percent"] == 0:
                    result["connection_quality"] = "excellent"
                elif result["packet_loss_percent"] < 5:
                    result["connection_quality"] = "good"
                elif result["packet_loss_percent"] < 20:
                    result["connection_quality"] = "fair"
                else:
                    result["connection_quality"] = "poor"

            else:
                # If ping failed completely
                result["status"] = "timeout"
                result["error"] = stderr if stderr else "Ping command failed"
                logger.warning(f"Ping failed for {self.target}: {stderr}")

                # Generate simulated ICMP details for timeout case to maintain structure
                self._generate_simulated_icmp_details(result, count)

        except Exception as e:
            # Handle exceptions
            logger.error(f"Error during ping test for {self.target}: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)

            # Generate simulated ICMP details for error case to maintain structure
            self._generate_simulated_icmp_details(result, count)

        return result

    def _extract_icmp_details(
        self, stdout: str, result: PingResult, count: int
    ) -> None:
        """Extract individual ICMP packet details from ping output.

        Args:
            stdout: Ping command output
            result: Result dictionary to update
            count: Number of packets sent
        """
        # Initialize details list
        details = []

        # Regular expression to extract ICMP sequence and time
        icmp_pattern = re.compile(
            r"icmp_seq=(\d+).*time=(\d+\.?\d*)", re.IGNORECASE
        )

        for line in stdout.splitlines():
            # Look for lines containing ICMP responses
            if "icmp_seq=" in line:
                match = icmp_pattern.search(line)
                if match:
                    sequence = int(match.group(1))
                    response_time = float(match.group(2))
                    details.append(
                        {
                            "sequence": sequence,
                            "response_time_ms": response_time,
                        }
                    )

        # If we didn't find all expected responses, some packets were lost
        if len(details) < count:
            # We can also try to extract RTT directly from these lines
            # if the standard method failed
            if all(v == 0 for v in result["rtt_stats"].values()):
                self._extract_rtt_from_icmp_lines(stdout, result)

            # If we still don't have RTT stats but have some details,
            # calculate them from the details
            if all(v == 0 for v in result["rtt_stats"].values()) and details:
                self._calculate_rtt_from_icmp_details(result)

        # Update the result with extracted details
        result["icmp_details"] = [
            IcmpDetail(
                sequence=int(d["sequence"]),
                response_time_ms=d["response_time_ms"],
            )
            for d in details
        ]

    def _generate_simulated_icmp_details(
        self, result: PingResult, count: int
    ) -> None:
        """Generate simulated ICMP details for error or timeout cases.

        Args:
            result: Result dictionary to update
            count: Number of packets that were sent
        """
        details = []
        for i in range(1, count + 1):
            # For timed out or failed pings, use None for response time
            details.append(
                {
                    "sequence": i,
                    "response_time_ms": 0.0,  # Using 0.0 for timed out packets
                }
            )
        result["icmp_details"] = [
            IcmpDetail(
                sequence=int(d["sequence"]),
                response_time_ms=d["response_time_ms"],
            )
            for d in details
        ]

    def _extract_rtt_from_icmp_lines(
        self, stdout: str, result: PingResult
    ) -> None:
        """Extract RTT statistics from individual ICMP response lines.

        Args:
            stdout: Ping command output
            result: Result dictionary to update
        """
        # Find all response times
        response_times = []
        icmp_pattern = re.compile(r"time=(\d+\.?\d*)", re.IGNORECASE)

        for line in stdout.splitlines():
            if "time=" in line:
                match = icmp_pattern.search(line)
                if match:
                    response_times.append(float(match.group(1)))

        # Calculate RTT statistics if we have response times
        if response_times:
            result["rtt_stats"]["min_ms"] = min(response_times)
            result["rtt_stats"]["avg_ms"] = sum(response_times) / len(
                response_times
            )
            result["rtt_stats"]["max_ms"] = max(response_times)

            # Calculate standard deviation for mdev
            mean = result["rtt_stats"]["avg_ms"]
            sum_squared_diff = sum((x - mean) ** 2 for x in response_times)
            if len(response_times) > 1:
                result["rtt_stats"]["mdev_ms"] = (
                    sum_squared_diff / len(response_times)
                ) ** 0.5
            else:
                result["rtt_stats"]["mdev_ms"] = 0.0

    def _calculate_rtt_from_icmp_details(self, result: PingResult) -> None:
        """Calculate RTT statistics from collected ICMP details.

        Args:
            result: Result dictionary to update
        """
        # Extract response times from details
        response_times = [
            detail["response_time_ms"]
            for detail in result["icmp_details"]
            if detail["response_time_ms"] > 0
        ]

        # Calculate statistics if there are valid response times
        if response_times:
            result["rtt_stats"]["min_ms"] = min(response_times)
            result["rtt_stats"]["avg_ms"] = sum(response_times) / len(
                response_times
            )
            result["rtt_stats"]["max_ms"] = max(response_times)

            # Calculate standard deviation for mdev
            mean = result["rtt_stats"]["avg_ms"]
            sum_squared_diff = sum((x - mean) ** 2 for x in response_times)
            if len(response_times) > 1:
                result["rtt_stats"]["mdev_ms"] = (
                    sum_squared_diff / len(response_times)
                ) ** 0.5
            else:
                result["rtt_stats"]["mdev_ms"] = 0.0

    def collect(self) -> Dict[str, Any]:
        """Collect ping metrics for the target.

        Returns:
            Dictionary with ping metrics and status
        """
        # Get basic ping metrics
        result = self.ping_target()

        # If the target is online and TLS checking is enabled, get TLS info
        if result["status"] == "online" and CHECK_TLS:
            result["tls_info"] = self.tls_checker.get_tls_info()

        # Format the final result
        return {
            "timestamp": datetime.now().isoformat(),
            "target": self.target,
            "primary_target": result,
        }
