import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import streamlit as st
st.set_page_config(page_title="Legal AI Chatbot", layout="wide")

import json
import datetime
from agents.query_engine import LegalQueryEngine
from agents.summarizer_agent import SummarizerAgent
from pathlib import Path
from tkinter import Tk, filedialog

# -------------------- Full Session Reset --------------------
if st.sidebar.button("🧹 Clear Session"):
    st.cache_resource.clear()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# -------------------- Session Defaults --------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.model_source = "ollama"
    st.session_state.model_name = ""
    st.session_state.api_keys = {"gemini": "", "openai": "", "groq": ""}
    st.session_state.selected_model = ""
    st.session_state.available_models = []

# -------------------- Caching Components --------------------
@st.cache_resource(show_spinner=False)
def load_engine():
    query_engine = LegalQueryEngine()
    query_engine.load_chunks()
    query_engine.load_index()
    return query_engine

# -------------------- UI Setup --------------------
st.title("⚖️ Legal Assistant Chatbot")

st.sidebar.header("Model Settings")

# Select model source
model_source = st.sidebar.selectbox("Select Model Provider", ["ollama", "gemini", "openai", "groq"], key="model_source_selector")
st.session_state.model_source = model_source

# Enter API key if needed
if model_source in ["openai", "gemini", "groq"]:
    st.session_state.api_keys[model_source] = st.sidebar.text_input(f"{model_source.capitalize()} API Key", value=st.session_state.api_keys.get(model_source, ""), type="password", key=f"{model_source}_api_key")

# Fetch and list available models
if model_source == "gemini" and st.session_state.api_keys["gemini"]:
    import google.generativeai as genai
    try:
        genai.configure(api_key=st.session_state.api_keys["gemini"])
        models = list(genai.list_models())
        st.session_state.available_models = [m.name for m in models if "generateContent" in m.supported_generation_methods]
    except Exception as e:
        st.sidebar.warning(f"Gemini error: {str(e)}")

elif model_source == "openai" and st.session_state.api_keys["openai"]:
    import openai
    try:
        openai.api_key = st.session_state.api_keys["openai"]
        models = openai.Model.list()
        st.session_state.available_models = [m.id for m in models.data]
    except Exception as e:
        st.sidebar.warning(f"OpenAI error: {str(e)}")

elif model_source == "groq" and st.session_state.api_keys["groq"]:
    try:
        from groq import Groq
        client = Groq(api_key=st.session_state.api_keys["groq"])
        models = client.models.list().data
        st.session_state.available_models = [m.id for m in models]
    except Exception as e:
        st.sidebar.warning(f"Groq error: {str(e)}")

elif model_source == "ollama":
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True)
        lines = result.stdout.decode().splitlines()[1:]
        st.session_state.available_models = [line.split()[0] for line in lines if line.strip()]
    except Exception as e:
        st.sidebar.warning(f"Ollama error: {str(e)}")

# Dropdown to select specific model name and store separately
if st.session_state.available_models:
    st.session_state.selected_model = st.sidebar.selectbox("Select Model", st.session_state.available_models, key="model_selector")
    st.session_state.model_name = st.session_state.selected_model

# Upload session
uploaded_session = st.sidebar.file_uploader("Upload saved session (.json)", type=["json"])
if uploaded_session:
    loaded_data = json.load(uploaded_session)
    st.session_state.chat_history = loaded_data.get("chat_history", [])
    st.session_state.model_source = loaded_data.get("model", "ollama")
    st.session_state.api_keys = loaded_data.get("api_keys", {})
    st.sidebar.success("Session loaded! Please reselect model/API key to activate.")

# Save session using file dialog
st.sidebar.markdown("---")
if st.sidebar.button("💾 Save Session To File"):
    root = Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    root.destroy()
    if filename:
        with open(filename, "w") as f:
            json.dump({
                "model": st.session_state.model_source,
                "api_keys": st.session_state.api_keys,
                "chat_history": st.session_state.chat_history
            }, f, indent=2)
        st.sidebar.success(f"Session saved to {filename}")

# -------------------- Chat UI --------------------
user_query = st.text_input("Type your legal question:")
submit = st.button("Ask")

if submit and user_query:
    with st.spinner("Analyzing legal content and summarizing..."):
        query_engine = load_engine()
        results = query_engine.query(user_query, top_k=3)
        top_chunks = [text for text, meta in results]
        sources = [f"{meta['source']} (Chunk #{meta['chunk_id']})" for _, meta in results]

        context = ""
        if len(st.session_state.chat_history) > 0:
            last_chat = st.session_state.chat_history[-1]
            context += f"Previous Q: {last_chat['question']}\nPrevious A: {last_chat['summary']}\n"

        summarizer = SummarizerAgent(
            model=st.session_state.model_source,
            gemini_key=st.session_state.api_keys.get("gemini"),
            openai_key=st.session_state.api_keys.get("openai"),
            groq_key=st.session_state.api_keys.get("groq"),
            model_name=st.session_state.model_name
        )

        summary = summarizer.summarize(top_chunks, context=context, user_query=user_query)

        st.session_state.chat_history.append({
            "question": user_query,
            "chunks": sources,
            "summary": summary
        })

# -------------------- Display Chat History --------------------
for i, chat in enumerate(reversed(st.session_state.chat_history)):
    with st.expander(f"❓ {chat['question']}"):
        st.markdown("**📘 Legal Sections Referenced:**")
        for src in chat["chunks"]:
            st.markdown(f"✅ `{src}`")

        st.markdown("**📝 AI Summary:**")
        formatted_summary = chat["summary"].replace("\n", "<br>").replace("**", "")
        st.markdown(f"<div style='margin-left: 10px; line-height: 1.6;'>{formatted_summary}</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

