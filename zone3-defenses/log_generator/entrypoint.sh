#!/bin/sh
# Create the log directory as root, then drop privileges.
set -eu
mkdir -p /var/log/cyberforge
chown cyberforge:cyberforge /var/log/cyberforge
exec runuser -u cyberforge -- python -u /app/generator.py
