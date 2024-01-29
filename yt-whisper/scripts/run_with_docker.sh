#!/bin/bash
set -euf -o pipefail
declare -r docker_image_name="yt-whisper:demo"
docker build -t ${docker_image_name} .
docker run -it --rm -p 8503:8503 --env-file .env ${docker_image_name}