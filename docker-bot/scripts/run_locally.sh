#!/bin/bash
set -euf -o pipefail
poetry run streamlit run docker_bot/bot.py --server.address 127.0.0.1