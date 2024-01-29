#!/bin/bash
set -euf -o pipefail
declare -r docker_image_name="dockerbot:demo"
docker build -t ${docker_image_name} .
docker run -it --rm -p 8504:8504 --env-file .env ${docker_image_name}