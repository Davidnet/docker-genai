FROM python:3.11-bullseye

WORKDIR /usr/src/app

COPY yt_whisper /usr/src/app/yt_whisper
COPY pyproject.toml /usr/src/app/pyproject.toml
COPY README.md /usr/src/app/README.md

RUN pip install -e .

EXPOSE 8503

HEALTHCHECK CMD curl --fail http://localhost:8503/_stcore/health

ENTRYPOINT ["streamlit", "run", "yt_whisper/app.py", "--server.port=8503", "--server.address=0.0.0.0"]