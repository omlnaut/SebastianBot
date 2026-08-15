#!/usr/bin/env bash

set -euo pipefail

echo "Start updating requirements.txt"

poetry export -f requirements.txt --output requirements.txt --without-hashes

echo "Finished updating requirements.txt"
