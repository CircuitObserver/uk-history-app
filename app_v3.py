import streamlit as st
import requests
from fpdf import FPDF

st.set_page_config(page_title="UK History Researcher", page_icon="🇬🇧")

# --- 2026 ROUTER SETUP ---
ROUTER_URL = "https://router.huggingface.co/hf-inference/v1/chat/completions"

# This list contains the most likely 'Active' models for the 2026 free tier
CANDIDATE_MODELS = [
    "meta-llama/Llama-3.2-3B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "microsoft/Phi-3-mini-4k-instruct",
    "Qwen/Qwen2.5-72B-Instruct"
]

def check_available_models():
    """Diagnostic tool to find which model actually works with your token."""
    if "HF_TOKEN" not in st.secrets:
        return None
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    working_model = None
    
    for model_id in CANDIDATE_MODELS:
        try:
            # Send a tiny 'Hello' request to see if the model is supported
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5
            }
            res = requests.post(ROUTER_URL, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                working_model = model_id
                break
        except:
            continue
    return working_model

def query_ai(year, model_to_use):
    headers = {
        "Authorization": f"Bearer {st.secrets['HF_TOKEN']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_to_use,
        "messages": [
            {"role": "system", "content": "You are a professional British historian."},
            {"role": "user", "content": f"Summarize the major events in the UK for the year {year}."}
        ],
        "max_tokens": 800
    }
    response = requests.post(ROUTER_URL, headers=headers, json=payload, timeout=40)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    return f"Error {response.status_code}: {response.text}"

# --- UI ---
st.title("🇬🇧 UK History Researcher")

# SIDEBAR DIAGNOSTICS
with st.sidebar:
    st.header("⚙️ System Status")
    if st.button("Run System Check"):
        with st.spinner("Finding a working model..."):
            found = check_available_models()
            if found:
                st.success(f"Connected! Using: {found}")
                st.session_state['active_model'] = found
            else:
                st.error("No compatible models found. Check your token permissions!")

# MAIN APP
year_input = st.number_input("Enter Year:", min_value=1, max_value=2026, value=2024)

if st.button("Give Info"):
    # Default to a model if they haven't run the check
    model_to_use = st.session_state.get('active_model', "meta-llama/Llama-3.2-3B-Instruct")
    
    with st.spinner(f"Using {model_to_use}..."):
        answer = query_ai(year_input, model_to_use)
        st.session_state['summary'] = answer

if 'summary' in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state['summary'])