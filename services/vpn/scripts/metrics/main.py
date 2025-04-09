#!/usr/bin/env python3
"""
Host Metrics Collection Tool.

This script collects metrics from a specified target host (IP or domain)
and outputs the results in JSON format. It can be used to monitor
the connectivity and performance of hosts.

Usage:
    python main.py --target example.com
    python main.py --target 192.168.1.1 --count 10 --timeout 5
    python main.py --target example.com --no-tls
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from scripts.metrics.config import CHECK_TLS, LOG_FORMAT, LOG_LEVEL
from scripts.metrics.host_monitor.ping_monitor import HostPingMonitor

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def collect_host_metrics(
    target: str,
    check_tls_override: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Collect metrics from the specified target host.

    Args:
        target: Target hostname or IP address
        check_tls_override: Override the default TLS check behavior.
                          If None, uses config default.

    Returns:
        Dictionary with collected metrics in the following format:
        {
            "timestamp": "ISO-8601 timestamp of the measurement",
            "target": "Target hostname or IP being monitored",
            "primary_target": {
                "ip": "IP address of the target",
                "status": "Conn status ('online', 'offline', or 'timeout')",
                "timestamp": "ISO-8601 timestamp of the ping test",
                "connection_quality": ("Quality ('excellent', 'good', 'fair', "
                "'poor', or 'none')"),
                "rtt_stats": {
                    "min_ms": "Min round-trip time (ms)",
                    "avg_ms": "Avg round-trip time (ms)",
                    "max_ms": "Max round-trip time (ms)",
                    "mdev_ms": "Mean dev of round-trip times (ms)"
                },
                "icmp_details": [
                    {
                        "sequence": "ICMP sequence number",
                        "response_time_ms": "Response time (ms)"
                    }
                ],
                "packet_loss_percent": "Percentage of lost packets (0-100)",
                "packets": {
                    "transmitted": "Number of packets sent",
                    "received": "Number of packets received"
                },
                "raw_output": "Raw output from the ping command",
                "tls_info": {
                    "certificate": "TLS certificate info (if applicable)",
                    "expiry": "Certificate expiration date",
                    "issuer": "Certificate issuer details",
                    "subject": "Certificate subject details",
                    "version": "SSL/TLS version",
                    "cipher": "SSL/TLS cipher"
                }
            }
        }
    """
    try:
        logger.info(f"Collecting metrics for target: {target}")

        from scripts.metrics import config

        use_tls_check = (
            check_tls_override if check_tls_override is not None else CHECK_TLS
        )

        original_check_tls = config.CHECK_TLS
        config.CHECK_TLS = use_tls_check
        logger.debug(f"TLS check for {target}: {config.CHECK_TLS}")

        monitor = HostPingMonitor(target)
        result: Dict[str, Any] = monitor.collect()

        config.CHECK_TLS = original_check_tls

        logger.info(f"Successfully collected metrics for {target}")
        return result

    except Exception as e:
        logger.error(f"Error collecting metrics for {target}: {str(e)}")
        return {
            "timestamp": datetime.now().isoformat(),
            "target": target,
            "primary_target": {
                "ip": target,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "connection_quality": "none",
                "rtt_stats": {
                    "min_ms": 0,
                    "avg_ms": 0,
                    "max_ms": 0,
                    "mdev_ms": 0,
                },
                "icmp_details": [],
                "packet_loss_percent": 100,
                "packets": {"transmitted": 0, "received": 0},
                "raw_output": "",
                "tls_info": None,
            },
        }


def main() -> None:
    """Parse command line arguments and run metrics collection."""
    parser = argparse.ArgumentParser(
        description="Collect metrics from a target host"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target hostname or IP address to monitor",
    )
    parser.add_argument(
        "--no-tls",
        action="store_true",
        help="Disable TLS certificate checking for HTTPS targets",
    )
    parser.add_argument(
        "--output-file",
        help="Save results to the specified file (JSON format)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    tls_override_value: Optional[bool] = False if args.no_tls else None

    results = collect_host_metrics(
        target=args.target,
        check_tls_override=tls_override_value,
    )

    json_results = json.dumps(results, indent=2, default=str)

    if args.output_file:
        try:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(json_results)
            logger.info(f"Results saved to {args.output_file}")
        except Exception as e:
            logger.error(f"Error saving results to file: {str(e)}")
            print(json_results)
    else:
        print(json_results)


if __name__ == "__main__":
    main()
