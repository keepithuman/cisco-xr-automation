#!/usr/bin/env python3
"""Fetch 'show version' from a Cisco IOS-XR device and output structured JSON via J2."""

import json
import os
import re
import sys

from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler


def parse_show_version(raw_output):
    """Extract fields from raw 'show version' output."""
    fields = {}

    m = re.search(r"^\s*(.+?)\s+uptime is\s+(.+)", raw_output, re.MULTILINE)
    if m:
        fields["hostname"] = m.group(1).strip()
        fields["uptime"] = m.group(2).strip()

    m = re.search(r"Software,?\s+Version\s+([\S]+)", raw_output)
    if m:
        fields["software_version"] = m.group(1).strip()

    m = re.search(r"cisco\s+(\S+)", raw_output, re.IGNORECASE)
    if m:
        fields["platform"] = m.group(1).strip()

    m = re.search(r"processor\s+.*?with\s+(\S+)\s", raw_output, re.IGNORECASE)
    if m:
        fields["memory"] = m.group(1).strip()

    m = re.search(r"processor\s*:\s*(.+)", raw_output, re.IGNORECASE)
    if not m:
        m = re.search(r"([\w\s]+processor)", raw_output, re.IGNORECASE)
    if m:
        fields["processor"] = m.group(1).strip()

    return fields


def main():
    device_ip = os.environ.get("DEVICE_IP") or (sys.argv[1] if len(sys.argv) > 1 else None)
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
    raw_output = conn.send_command("show version")
    conn.disconnect()

    fields = parse_show_version(raw_output)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("version.j2")
    result = template.render(**fields)

    # Validate and print clean JSON
    print(json.dumps(json.loads(result)))


if __name__ == "__main__":
    main()
