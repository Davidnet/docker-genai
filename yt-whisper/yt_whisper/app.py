import os
import tempfile
from pathlib import Path
from tempfile import mkdtemp

import pinecone
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pytube import YouTube
from pytube.exceptions import RegexMatchError
from streamlit.logger import get_logger

from yt_whisper.vtt_utils import merge_webvtt_to_list

load_dotenv(".env")

logger = get_logger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_TOKEN"))


@st.cache_resource
def load_pinecone(index_name="docker-genai"):
    # initialize pinecone
    pinecone.init(
        api_key=os.getenv("PINECONE_TOKEN"),
        environment=os.getenv("PINECONE_ENVIRONMENT"),
    )
    if index_name not in pinecone.list_indexes():
        # we create a new index
        pinecone.create_index(name=index_name, metric="cosine", dimension=1536)
    index = pinecone.Index(index_name)
    return index


@st.cache_data
def process_video(video_url: str) -> dict[str, str]:
    """Process the video and return the transcription"""
    try:
        yt_handler = YouTube(video_url)
    except RegexMatchError:
        st.error("Please enter a valid youtube url", icon="🚨")

    with st.spinner("Processing your video"):
        logger.info(f"Processing video: {yt_handler.watch_url}")
        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_stream = yt_handler.streams.filter(only_audio=True).first()
            audio_file = audio_stream.download(tmp_dir)
            file_stats = os.stat(audio_file)
            logger.info(f"File size: {file_stats.st_size}")
            logger.info(f"File name: {audio_file}")
            if file_stats.st_size > 24 * 1024 * 1024:  # 25 MB Limit check
                # TODO(davidnet): Split and process the video in chunks
                st.error(
                    "Please select a shorter video, OpenAI has a limit of 25 MB",
                    icon="🚨",
                )
                return
            with open(audio_file, "rb") as audio_file:
                whisper_transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="vtt",
                )
            logger.info("Transcription done")

            seconds_to_merge = 8

            transcript = merge_webvtt_to_list(whisper_transcript, seconds_to_merge)

            stride = 3
            video_data = []

            def _upload_to_pinecone(video_data):
                index = load_pinecone()
                batch_transcripts = [t["text"] for t in video_data]
                batch_ids = [t["id"] for t in video_data]
                batch_metadata = [
                    {
                        "initial_time": t["initial_time"],
                        "title": yt_handler.title,
                        "thumbnail": yt_handler.thumbnail_url,
                        "video_url": f"{video_url}&t={t['initial_time']}s",
                        "text": t["text"],
                    }
                    for t in video_data
                ]
                embeddings = client.embeddings.create(
                    input=batch_transcripts, model="text-embedding-ada-002"
                )
                batch_embeds = [e.embedding for e in embeddings.data]
                to_upsert = list(zip(batch_ids, batch_embeds, batch_metadata))
                index.upsert(to_upsert)

            for block in range(0, len(transcript), stride):
                initial_time = transcript[block]["initial_time_in_seconds"]
                id = f"{yt_handler.video_id}-t{initial_time}"
                text = " ".join(
                    [t["text"] for t in transcript[block : block + stride]]
                ).replace("\n", " ")
                video_data.append(
                    {"initial_time": initial_time, "text": text, "id": id}
                )
                if len(video_data) > 64:
                    _upload_to_pinecone(video_data)
                    video_data = []

            if len(video_data) > 0:
                _upload_to_pinecone(video_data)

            output_transcript_path: Path = (
                st.session_state.tempfolder / f"{yt_handler.video_id}.txt"
            )
            with open(output_transcript_path, "w") as transcript_file:
                transcript_file.write(whisper_transcript)

                return {
                    "video_id": yt_handler.video_id,
                    "title": yt_handler.title,
                    "thumbnail": yt_handler.thumbnail_url,
                }


def disable(b):
    st.session_state["processing"] = b


def main():
    logger.info("Rendering app")
    if "tempfolder" not in st.session_state:
        st.session_state.tempfolder = Path(mkdtemp(prefix="yt_transcription_"))
    if "videos" not in st.session_state:
        st.session_state.videos = []
    if "processing" not in st.session_state:
        st.session_state.processing = False

    # "state: ", st.session_state

    st.header("Chat with your youtube videos")
    st.write(
        "This app uses OpenAI's [Whisper](https://openai.com/blog/whisper/) model to generate a transcription of your videos and upload it to Pinecone."
    )

    yt_uri = st.text_input("Youtube URL", "https://www.youtube.com/watch?v=8CY2aq3tcXA")
    if st.button(
        "Submit",
        type="primary",
        on_click=disable,
        args=(True,),
        disabled=st.session_state.processing,
    ):
        result = process_video(yt_uri)
        st.session_state.videos.append(result)
        st.session_state.processing = False
        st.rerun()

    st.header("Processed videos:")
    st.write("Here are the videos you have processed so far:")
    st.write(
        "You can download the transcription of the video by clicking on the corresponding video below"
    )
    for video in st.session_state.videos:
        with st.container(border=True):
            st.title(video["title"])
            st.image(video["thumbnail"], width=320)
            if st.button("Download transcription"):
                with open(
                    st.session_state.tempfolder / f"{video['video_id']}.txt"
                ) as transcript_file:
                    st.download_button(
                        f"Download transcription {video['video_id']}",
                        transcript_file,
                        file_name=video["video_id"],
                    )


if __name__ == "__main__":
    main()
