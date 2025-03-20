#!/usr/bin/env python3
"""
SubNetx VPN Bandwidth Monitor
This script measures available bandwidth to assess connection quality.
"""

import subprocess
import time
import json
import logging
import requests
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class BandwidthMonitor:
    def __init__(self, target: str):
        """
        Initialize the Bandwidth Monitor.

        Args:
            target (str): Target hostname or IP address to monitor
        """
        self.target = target
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
        self.logger = logging.getLogger('subnetx')
        self.logger.info(f"Initialized Bandwidth Monitor for {target}")

    def _download_test(self, url: str, timeout: int = 10) -> Optional[float]:
        """
        Perform a download speed test by downloading a file from a URL.

        Args:
            url (str): URL to download from
            timeout (int): Timeout in seconds

        Returns:
            Optional[float]: Download speed in bytes per second, or None if failed
        """
        try:
            start_time = time.time()

            # Download the main page
            response = requests.get(f"{url}", stream=True, timeout=timeout)
            if not response.ok:
                self.logger.warning(f"Download test failed for {url}: {response.status_code}")
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
                self.logger.info(f"Download test: {self._format_bytes(speed)}/s from {url}")
                return speed
            else:
                self.logger.warning(f"Download test had zero duration for {url}")
                return None
        except Exception as e:
            self.logger.error(f"Error in download test for {url}: {e}")
            return None

    def _upload_test(self, url: str, data_size: int = 1024*1024, timeout: int = 10) -> Optional[float]:
        """
        Perform an upload speed test by uploading data to a URL.

        Args:
            url (str): URL to upload to
            data_size (int): Size of data to upload in bytes
            timeout (int): Timeout in seconds

        Returns:
            Optional[float]: Upload speed in bytes per second, or None if failed
        """
        try:
            # Since we can't easily upload to arbitrary URLs without a server component,
            # we'll simulate an upload by measuring how quickly we can send headers and
            # start sending a POST request

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
                # This is an approximation
                speed = len(data) / duration
                self.logger.info(f"Upload test: {self._format_bytes(speed)}/s to {url}")
                return speed
            else:
                self.logger.warning(f"Upload test had zero duration for {url}")
                return None
        except Exception as e:
            self.logger.error(f"Error in upload test for {url}: {e}")
            return None

    def _format_bytes(self, bytes_value: float) -> str:
        """
        Format bytes to human-readable format (KB, MB, GB).

        Args:
            bytes_value (float): Bytes value to format

        Returns:
            str: Formatted string with units
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0

        while bytes_value >= 1024 and unit_index < len(units) - 1:
            bytes_value /= 1024
            unit_index += 1

        return f"{bytes_value:.2f} {units[unit_index]}"

    def _should_run_test(self) -> bool:
        """
        Determine if a bandwidth test should be run based on elapsed time.

        Returns:
            bool: True if a test should be run, False otherwise
        """
        current_time = time.time()
        return (current_time - self.last_test_time) >= self.test_interval

    def _run_speed_tests(self) -> Dict[str, Any]:
        """
        Run a complete set of speed tests.

        Returns:
            Dict[str, Any]: Speed test results
        """
        self.logger.info("Running bandwidth tests...")
        download_speeds = []
        upload_speeds = []
        server_results = {}

        for server_url in self.test_servers:
            try:
                self.logger.info(f"Testing bandwidth with server: {server_url}")

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
                self.logger.error(f"Error testing with {server_url}: {e}")

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

    def _get_jitter_latency(self, count: int = 4) -> Dict[str, Any]:
        """
        Measure network jitter and latency using ping.

        Args:
            count (int): Number of ping packets to send

        Returns:
            Dict[str, Any]: Jitter and latency measurements
        """
        try:
            self.logger.info(f"Measuring jitter and latency to {self.target}")

            # Run ping command
            result = subprocess.run(
                ['ping', '-c', str(count), self.target],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.logger.warning(f"Ping failed with return code {result.returncode}")
                return {
                    'success': False,
                    'error': f"Ping failed with return code {result.returncode}"
                }

            # Extract RTT values
            rtts = []
            for line in result.stdout.split('\n'):
                if 'time=' in line:
                    try:
                        rtt = float(line.split('time=')[1].split()[0])
                        rtts.append(rtt)
                    except (IndexError, ValueError):
                        pass

            # Calculate statistics
            if rtts:
                avg_latency = statistics.mean(rtts)

                # Calculate jitter (variation in latency)
                if len(rtts) > 1:
                    jitter = statistics.stdev(rtts)
                else:
                    jitter = 0

                return {
                    'success': True,
                    'latency_ms': avg_latency,
                    'jitter_ms': jitter,
                    'min_latency_ms': min(rtts),
                    'max_latency_ms': max(rtts),
                    'samples': len(rtts)
                }
            else:
                self.logger.warning("No RTT values found in ping output")
                return {
                    'success': False,
                    'error': "No RTT values found in ping output"
                }

        except Exception as e:
            self.logger.error(f"Error measuring jitter and latency: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def collect(self) -> Dict[str, Any]:
        """
        Collect bandwidth metrics.

        Returns:
            Dict[str, Any]: Dictionary with bandwidth metrics
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'target': self.target
        }

        # Always measure jitter and latency (fast)
        jitter_latency = self._get_jitter_latency()
        result['jitter_latency'] = jitter_latency

        # Run bandwidth tests periodically (resource-intensive)
        if self._should_run_test():
            self.logger.info("Running full bandwidth test")
            bandwidth_test = self._run_speed_tests()
            result['bandwidth_test'] = bandwidth_test
        else:
            # Return the last test results if available
            if self.download_speeds and self.upload_speeds:
                last_download = self.download_speeds[-1]['speed']
                last_upload = self.upload_speeds[-1]['speed']
                result['bandwidth_test'] = {
                    'timestamp': datetime.now().isoformat(),
                    'average_download': last_download,
                    'average_upload': last_upload,
                    'download_human': self._format_bytes(last_download),
                    'upload_human': self._format_bytes(last_upload),
                    'note': 'Using cached bandwidth test result'
                }
            else:
                result['bandwidth_test'] = {
                    'note': 'No bandwidth tests run yet'
                }

        # Include historical data
        result['history'] = {
            'download_speeds': self.download_speeds[-10:],
            'upload_speeds': self.upload_speeds[-10:]
        }

        # Log a summary of the results
        if 'bandwidth_test' in result and 'average_download' in result['bandwidth_test']:
            self.logger.info(f"Bandwidth: ↓{result['bandwidth_test']['download_human']}/s, ↑{result['bandwidth_test']['upload_human']}/s")

        if 'jitter_latency' in result and result['jitter_latency']['success']:
            self.logger.info(f"Latency: {result['jitter_latency']['latency_ms']:.2f}ms, Jitter: {result['jitter_latency']['jitter_ms']:.2f}ms")

        return result

# Standalone testing when script is run directly
if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger('subnetx')

    # Test the bandwidth monitor
    target = "google.com"

    # Set short test interval for demo purposes
    monitor = BandwidthMonitor(target)
    monitor.test_interval = 0  # Always run test for demo

    print(f"Testing bandwidth for {target}")
    results = monitor.collect()
    print(json.dumps(results, indent=2))
