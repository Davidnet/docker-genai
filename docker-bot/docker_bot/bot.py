import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from streamlit.logger import get_logger

load_dotenv(".env")

logger = get_logger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_TOKEN"))


@st.cache_resource
def load_pinecone(index_name="docker-genai"):
    # initialize pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_TOKEN"))

    if index_name not in pc.list_indexes().names():
        logger.info(f"Creating index {index_name}, therefore there are no videos yet.")
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-west-2"),
        )
    index = pc.Index(index_name)
    return index


def generate_response(input_text):
    question_embedding = client.embeddings.create(
        input=[input_text], model="text-embedding-3-small"
    )
    num_embeddings = list(question_embedding.data[0].embedding)
    # print(list(question_embedding.data[0].embedding))
    res_contex = load_pinecone().query(
        vector=num_embeddings,
        top_k=5,
        include_metadata=True,
    )

    matches = res_contex["matches"]

    context = (
        "The following are the top 5 videos transcription that match your query: \n"
    )
    references = ""
    for match in matches:
        context += "Title: " + match.metadata["title"] + "\n"
        context += "Transcription: " + match.metadata["text"] + "\n"
        references += "\n - " + match.metadata["video_url"] + "\n"

    primer = """You are Q&A bot. A highly intelligent system that answers 
    user questions based on the information provided by videos transcriptions. You can use your inner knowledge,
    but consider more with emphasis the information provided. Put emphasis on the transcriptions provided. If you see titles repeated, you can assume it is the same video.
    Provide samples of the transcriptions that are important to your query.
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": primer},
            {
                "role": "user",
                "content": context,
            },
            {"role": "user", "content": input_text},
        ],
        model="gpt-4-turbo-preview",
    )
    response = chat_completion.choices[0].message.content

    # Add video references
    response += "\n Click on the following for more information: " + references

    return response


logger = get_logger(__name__)


# Streamlit UI
styl = """
<style>
    /* not great support for :has yet (hello FireFox), but using it for now */
    .element-container:has([aria-label="Select RAG mode"]) {{
      position: fixed;
      bottom: 33px;
      background: white;
      z-index: 101;
    }}
    .stChatFloatingInputContainer {{
        bottom: 20px;
    }}

    /* Generate ticket text area */
    textarea[aria-label="Description"] {{
        height: 200px;
    }}
</style>
"""
st.markdown(styl, unsafe_allow_html=True)


def chat_input():
    user_input = st.chat_input("What you want to know about your videos?")

    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            st.caption("Dockerbot")
            # result = output_function(
            #     {"question": user_input, "chat_history": []}, callbacks=[stream_handler]
            # )["answer"]
            result = generate_response(user_input)
            # result = "I am a bot. I am still learning."
            output = result
            st.session_state["user_input"].append(user_input)
            st.session_state["generated"].append(output)
            st.rerun()


def display_chat():
    # Session state
    if "generated" not in st.session_state:
        st.session_state["generated"] = []

    if "user_input" not in st.session_state:
        st.session_state["user_input"] = []

    if st.session_state["generated"]:
        size = len(st.session_state["generated"])
        # Display only the last three exchanges
        for i in range(max(size - 3, 0), size):
            with st.chat_message("user"):
                st.write(st.session_state["user_input"][i])

            with st.chat_message("assistant"):
                # st.caption(f"RAG: {st.session_state['rag_mode'][i]}")
                st.caption("Dockerbot")
                st.write(st.session_state["generated"][i])

        with st.container():
            st.write("&nbsp;")


display_chat()
chat_input()
