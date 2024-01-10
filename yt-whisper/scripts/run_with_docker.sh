#!/bin/bash
set -euf -o pipefail
docker run -p 8503:8503 --env-file .env  demo 