#!/bin/bash
set -euf -o pipefail
poetry run streamlit run yt_whisper/app.py --server.address 127.0.0.1