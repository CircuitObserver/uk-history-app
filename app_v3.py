import streamlit as st
import requests
from fpdf import FPDF
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="UK History Researcher", page_icon="🇬🇧")

# --- API SETUP ---
# Using a model that is almost always online
API_URL = "https://api-inference.huggingface.co/models/google/gemma-7b-it"

def query_ai(prompt):
    if "HF_TOKEN" not in st.secrets:
        return "Error: HF_TOKEN missing from Secrets."
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": f"Provide a short summary of the United Kingdom in the year {prompt}. Mention one political and one cultural event.",
        "parameters": {"max_new_tokens": 500, "return_full_text": False}
    }

    # Try up to 3 times if we get a blank response
    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', "No text found.")
                return "AI returned an empty list. Retrying..."
            
            elif response.status_code == 503:
                time.sleep(5) # Wait for model to load
                continue
            else:
                return f"Server Error: {response.status_code}"
                
        except Exception:
            time.sleep(2)
            continue
            
    return "The AI server is currently overloaded. Please try again in 1 minute."

# --- PDF GENERATION ---
def create_pdf(text, year):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"UK History: {year}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=11)
    # Filter out characters that FPDF can't handle
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- UI ---
st.title("🇬🇧 UK History Researcher")
year_input = st.number_input("Enter Year:", min_value=1, max_value=2026, value=2024)

if st.button("Give Info"):
    with st.spinner("Searching..."):
        answer = query_ai(str(year_input))
        st.session_state['summary'] = answer

if 'summary' in st.session_state:
    st.markdown("---")
    st.write(st.session_state['summary'])
    
    if "Error" not in st.session_state['summary'] and "Server" not in st.session_state['summary']:
        pdf_data = create_pdf(st.session_state['summary'], year_input)
        st.download_button("Download PDF", data=bytes(pdf_data), file_name="UK_History.pdf")