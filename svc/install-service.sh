#!/bin/bash

# Get the absolute path of the script
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"

# Get the directory containing the script
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

# Get the parent directory of the script's directory
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

sed "s@###ROOT###@$PARENT_DIR@g" ${PARENT_DIR}/svc/edr-state-server.service > /etc/systemd/system/edr-state-server.service
sed "s@###ROOT###@$PARENT_DIR@g" ${PARENT_DIR}/svc/edr-state-monitor.cron /etc/systemd/system/edr-state-monitor.cron

systemctl daemon-reload
systemctl start edr-state-server.service
systemctl status edr-state-server.service