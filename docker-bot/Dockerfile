FROM python:3.11-bullseye

WORKDIR /usr/src/app

COPY docker_bot /usr/src/app/docker_bot
COPY pyproject.toml /usr/src/app/pyproject.toml
COPY README.md /usr/src/app/README.md

RUN pip install -e .

EXPOSE 8504

HEALTHCHECK CMD curl --fail http://localhost:8504/_stcore/health

ENTRYPOINT ["streamlit", "run", "yt_whisper/app.py", "--server.port=8504", "--server.address=0.0.0.0"]