#!/usr/bin/env python3
"""Fetch 'show ipv4 interface brief' from a Cisco IOS-XR device and output structured JSON via J2."""

import argparse
import json
import os
import re
import sys

from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler


def parse_show_interfaces(raw_output):
    """Extract interface entries from raw 'show ipv4 interface brief' output."""
    interfaces = []
    for line in raw_output.splitlines():
        # Match lines like: GigabitEthernet0/0/0/0  10.0.0.1  Up  Up
        m = re.match(
            r"^(\S+)\s+([\d.]+|unassigned)\s+(\S+)\s+(\S+)",
            line.strip(),
        )
        if m and not line.strip().startswith("Interface"):
            interfaces.append({
                "name": m.group(1),
                "ip_address": m.group(2),
                "status": m.group(3),
                "protocol": m.group(4),
            })
    return interfaces


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device_ip", required=False)
    args, _ = parser.parse_known_args()

    device_ip = args.device_ip or os.environ.get("DEVICE_IP")
    username = os.environ.get("DEVICE_USERNAME")
    password = os.environ.get("DEVICE_PASSWORD")

    if not all([device_ip, username, password]):
        print(json.dumps({"error": "Missing device_ip, DEVICE_USERNAME, or DEVICE_PASSWORD"}))
        sys.exit(1)

    device = {
        "device_type": "cisco_xr",
        "host": device_ip,
        "username": username,
        "password": password,
    }

    conn = ConnectHandler(**device)
    raw_output = conn.send_command("show ipv4 interface brief")
    conn.disconnect()

    interfaces = parse_show_interfaces(raw_output)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("interfaces.j2")
    result = template.render(interfaces=interfaces)

    # Validate and print clean JSON
    print(json.dumps(json.loads(result)))


if __name__ == "__main__":
    main()
