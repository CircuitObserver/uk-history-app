import streamlit as st
import requests
from fpdf import FPDF
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="UK History Researcher", page_icon="🇬🇧")

# --- API SETUP ---
# Mistral is very reliable and NOT gated (no 404/Accept License needed)
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

def query_ai(year):
    if "HF_TOKEN" not in st.secrets:
        return "Error: HF_TOKEN missing from Secrets."
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    
    # Mistral uses a specific [INST] format for best results
    prompt = f"[INST] Provide a summary of the United Kingdom in the year {year}. Include major political, social, and cultural events. [/INST]"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 700, 
            "temperature": 0.7,
            "wait_for_model": True  # Tells HF to wait if model is loading
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=40)
        
        if response.status_code == 200:
            result = response.json()
            # Handle list vs dict return types
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', "No text found.")
            return str(result)
        
        elif response.status_code == 503:
            return "The AI is currently 'waking up'. Please wait 20 seconds and try again."
        else:
            return f"Error: {response.status_code} - {response.text}"
                
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- PDF GENERATION ---
def create_pdf(text, year):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"UK History Report: {year}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=11)
    # Filter out characters that FPDF (Latin-1) can't handle
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- UI ---
st.title("🇬🇧 UK History Researcher")
st.write("Enter a year to receive an AI-powered summary of events in the UK.")

year_input = st.number_input("Enter Year (e.g., 1945):", min_value=1, max_value=2026, value=2024)

if st.button("Give Info"):
    with st.spinner(f"Researching {year_input}..."):
        answer = query_ai(year_input)
        # Mistral often includes the prompt in the output; let's clean it if so
        if "[/INST]" in answer:
            answer = answer.split("[/INST]")[-1].strip()
        st.session_state['summary'] = answer

if 'summary' in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state['summary'])
    
    # Only show PDF button if response is valid
    if "Error" not in st.session_state['summary'] and len(st.session_state['summary']) > 50:
        pdf_data = create_pdf(st.session_state['summary'], year_input)
        st.download_button(
            label="📥 Download Research as PDF", 
            data=bytes(pdf_data), 
            file_name=f"UK_History_{year_input}.pdf",
            mime="application/pdf"
        )