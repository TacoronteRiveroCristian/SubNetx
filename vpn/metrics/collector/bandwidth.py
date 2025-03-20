#!/usr/bin/env python3
"""
SubNetx VPN Bandwidth Monitor

This module provides functionality to measure available bandwidth and connection quality
for VPN connections, focusing on download/upload speeds and jitter measurements.
"""

import subprocess
import time
import json
import logging
import requests
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from .base import BaseMonitor
from .ping import PingMonitor

class BandwidthMonitor(BaseMonitor):
    """Monitor for available bandwidth and connection quality.

    This class specializes in measuring available bandwidth, including
    download/upload speeds, jitter, and latency. It provides both raw
    metrics and human-readable summaries.

    :param target: Target hostname or IP address to monitor
    :type target: str
    :ivar download_speeds: Historical download speed measurements
    :type download_speeds: List[Dict[str, Any]]
    :ivar upload_speeds: Historical upload speed measurements
    :type upload_speeds: List[Dict[str, Any]]
    :ivar test_servers: List of servers to test bandwidth with
    :type test_servers: List[str]
    :ivar last_test_time: Timestamp of the last bandwidth test
    :type last_test_time: float
    :ivar test_interval: Interval between bandwidth tests in seconds
    :type test_interval: int
    """

    def __init__(self, target: str):
        """Initialize the Bandwidth Monitor.

        :param target: Target hostname or IP address to monitor
        :type target: str
        """
        super().__init__(target)
        self.download_speeds = []
        self.upload_speeds = []
        self.test_servers = [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://www.amazon.com",
            "https://www.microsoft.com"
        ]
        self.last_test_time = 0
        self.test_interval = 3600  # Default test interval: 1 hour
        print(f"Initialized Bandwidth Monitor for {target}")

    def _download_test(self, url: str, timeout: int = 10) -> Optional[float]:
        """Perform a download speed test by downloading a file from a URL.

        :param url: URL to download from
        :type url: str
        :param timeout: Timeout in seconds
        :type timeout: int, optional
        :return: Download speed in bytes per second, or None if failed
        :rtype: Optional[float]
        :raises requests.RequestException: If download fails
        """
        try:
            start_time = time.time()

            # Download the main page
            response = requests.get(f"{url}", stream=True, timeout=timeout)
            if not response.ok:
                print(f"Download test failed for {url}: {response.status_code}")
                return None

            # Read the content and measure
            total_bytes = 0
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    total_bytes += len(chunk)

            # Calculate speed
            duration = time.time() - start_time
            if duration > 0:
                speed = total_bytes / duration
                print(f"Download test: {self._format_bytes(speed)}/s from {url}")
                return speed
            else:
                print(f"Download test had zero duration for {url}")
                return None
        except Exception as e:
            print(f"Error in download test for {url}: {e}")
            return None

    def _upload_test(self, url: str, data_size: int = 1024*1024, timeout: int = 10) -> Optional[float]:
        """Perform an upload speed test by uploading data to a URL.

        :param url: URL to upload to
        :type url: str
        :param data_size: Size of data to upload in bytes
        :type data_size: int, optional
        :param timeout: Timeout in seconds
        :type timeout: int, optional
        :return: Upload speed in bytes per second, or None if failed
        :rtype: Optional[float]
        :raises requests.RequestException: If upload fails
        """
        try:
            # Generate test data
            data = b'0' * data_size

            start_time = time.time()

            # Send a POST request with the data
            response = requests.post(
                f"{url}",
                data=data,
                timeout=timeout,
                headers={'Content-Type': 'application/octet-stream'}
            )

            # Calculate speed
            duration = time.time() - start_time
            if duration > 0:
                # We calculate bytes transferred including headers
                speed = len(data) / duration
                print(f"Upload test: {self._format_bytes(speed)}/s to {url}")
                return speed
            else:
                print(f"Upload test had zero duration for {url}")
                return None
        except Exception as e:
            print(f"Error in upload test for {url}: {e}")
            return None

    def _should_run_test(self) -> bool:
        """Determine if a bandwidth test should be run based on elapsed time.

        :return: True if a test should be run, False otherwise
        :rtype: bool
        """
        current_time = time.time()
        return (current_time - self.last_test_time) >= self.test_interval

    def _run_speed_tests(self) -> Dict[str, Any]:
        """Run a complete set of speed tests.

        :return: Speed test results
        :rtype: Dict[str, Any]
        :raises Exception: If speed tests fail
        """
        print("Running bandwidth tests...")
        download_speeds = []
        upload_speeds = []
        server_results = {}

        for server_url in self.test_servers:
            try:
                print(f"Testing bandwidth with server: {server_url}")

                # Download test
                download_speed = self._download_test(server_url)
                if download_speed:
                    download_speeds.append(download_speed)

                # Upload test (using smaller data for upload to be respectful)
                upload_speed = self._upload_test(server_url, data_size=512*1024)
                if upload_speed:
                    upload_speeds.append(upload_speed)

                # Store individual server results
                server_results[server_url] = {
                    'download_speed': download_speed,
                    'upload_speed': upload_speed,
                    'download_human': self._format_bytes(download_speed) if download_speed else "N/A",
                    'upload_human': self._format_bytes(upload_speed) if upload_speed else "N/A",
                }

                # Avoid overloading servers
                time.sleep(1)

            except Exception as e:
                print(f"Error testing with {server_url}: {e}")

        # Calculate averages if we have data
        avg_download = statistics.mean(download_speeds) if download_speeds else 0
        avg_upload = statistics.mean(upload_speeds) if upload_speeds else 0

        # Store results
        self.download_speeds.append({
            'timestamp': datetime.now().isoformat(),
            'speed': avg_download
        })

        self.upload_speeds.append({
            'timestamp': datetime.now().isoformat(),
            'speed': avg_upload
        })

        # Keep only the last 100 entries
        self.download_speeds = self.download_speeds[-100:]
        self.upload_speeds = self.upload_speeds[-100:]

        # Update last test time
        self.last_test_time = time.time()

        # Return results
        return {
            'timestamp': datetime.now().isoformat(),
            'average_download': avg_download,
            'average_upload': avg_upload,
            'download_human': self._format_bytes(avg_download),
            'upload_human': self._format_bytes(avg_upload),
            'servers_tested': len(server_results),
            'server_results': server_results
        }

    def _get_jitter_latency(self) -> Dict[str, Any]:
        """Measure network jitter and latency using PingMonitor.

        :return: Jitter and latency measurements
        :rtype: Dict[str, Any]
        :raises Exception: If ping measurements fail
        """
        try:
            # Use PingMonitor to get accurate ICMP measurements
            ping_monitor = PingMonitor(self.target)
            ping_result = ping_monitor.ping_target(count=10)  # Use more packets for jitter

            if ping_result.get('status') != 'online':
                return {
                    'success': False,
                    'error': f"Target is {ping_result.get('status', 'unavailable')}"
                }

            # Extract RTT stats
            rtt_stats = ping_result.get('rtt_stats', {})

            # Extract individual ping times for jitter calculation
            icmp_details = ping_result.get('icmp_details', [])
            response_times = [ping.get('response_time_ms', 0) for ping in icmp_details]

            # Calculate jitter (mean absolute difference between consecutive samples)
            jitter_ms = 0
            if len(response_times) > 1:
                diffs = [abs(response_times[i] - response_times[i-1]) for i in range(1, len(response_times))]
                jitter_ms = sum(diffs) / len(diffs) if diffs else 0

            return {
                'success': True,
                'latency_ms': rtt_stats.get('avg_ms', 0),
                'min_latency_ms': rtt_stats.get('min_ms', 0),
                'max_latency_ms': rtt_stats.get('max_ms', 0),
                'jitter_ms': jitter_ms,
                'standard_deviation_ms': rtt_stats.get('mdev_ms', 0),
                'packets_sent': len(response_times),
                'packets_received': len([t for t in response_times if t > 0])
            }
        except Exception as e:
            print(f"Error measuring jitter and latency: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def collect(self) -> Dict[str, Any]:
        """Collect bandwidth metrics for the target.

        Performs bandwidth tests to measure download/upload speeds and
        network quality metrics including jitter and latency.

        :return: Dictionary with bandwidth metrics
        :rtype: Dict[str, Any]
        :raises Exception: If collection fails
        """
        try:
            # Start with the basic result structure
            result = self.get_basic_result()

            # Run bandwidth tests if needed
            if self._should_run_test():
                speed_results = self._run_speed_tests()
                result.update(speed_results)

            # Get jitter and latency measurements
            jitter_latency = self._get_jitter_latency()
            result['network_quality'] = jitter_latency

            # Add historical data
            result['historical_data'] = {
                'download_speeds': self.download_speeds,
                'upload_speeds': self.upload_speeds
            }

            return result
        except Exception as e:
            print(f"Error in bandwidth collection: {e}")
            raise

# Standalone testing when script is run directly
if __name__ == "__main__":
    # Setup basic logging if running standalone
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger(__name__)

    # Test the bandwidth monitor
    targets = ["google.com", "8.8.8.8"]

    for target in targets:
        try:
            logger.info(f"Testing {target}")
            monitor = BandwidthMonitor(target)
            results = monitor.collect()
            logger.info(f"\nResults for {target}:")
            logger.info(json.dumps(results, indent=2))
        except Exception as e:
            logger.error(f"Failed to collect metrics for {target}: {str(e)}")
            logger.error(f"Error details: {e.__class__.__name__}")
