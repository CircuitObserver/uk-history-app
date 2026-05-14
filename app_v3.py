import streamlit as st
import requests
from fpdf import FPDF

# --- PAGE CONFIG ---
st.set_page_config(page_title="UK History Researcher", page_icon="🇬🇧")

# --- NEW 2026 ROUTER SETUP ---
# Instead of a specific model, we point to the Router and specify the model in the headers/body
API_URL = "https://router.huggingface.co/hf-inference/v1/chat/completions"

def query_ai(year):
    if "HF_TOKEN" not in st.secrets:
        return "Error: HF_TOKEN missing from Streamlit Secrets."
    
    headers = {
        "Authorization": f"Bearer {st.secrets['HF_TOKEN']}",
        "Content-Type": "application/json"
    }
    
    # We use the 'Chat' format which is more reliable in 2026
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "messages": [
            {"role": "system", "content": "You are a professional British historian."},
            {"role": "user", "content": f"Summarize the major events in the UK for the year {year}. Include Politics, Culture, and Economy."}
        ],
        "max_tokens": 800,
        "temperature": 0.7
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=40)
        
        if response.status_code == 200:
            result = response.json()
            # The Router returns a standard 'chat' response
            return result['choices'][0]['message']['content']
        
        elif response.status_code == 404:
            return "Error 404: The Router couldn't find the model. Please check your token permissions."
        elif response.status_code == 503:
            return "The AI is currently 'waking up'. Please wait 20 seconds and click 'Give Info' again."
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
    # Clean for PDF
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- UI ---
st.title("🇬🇧 UK History Researcher")
st.write("Enter a year to receive a summary of UK historical events.")

year_input = st.number_input("Enter Year:", min_value=1, max_value=2026, value=2024)

if st.button("Give Info"):
    with st.spinner(f"Querying the 2026 Router for {year_input}..."):
        answer = query_ai(year_input)
        st.session_state['summary'] = answer

if 'summary' in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state['summary'])
    
    if "Error" not in st.session_state['summary'] and len(st.session_state['summary']) > 20:
        pdf_data = create_pdf(st.session_state['summary'], year_input)
        st.download_button(
            label="📥 Download Research as PDF", 
            data=bytes(pdf_data), 
            file_name=f"UK_History_{year_input}.pdf",
            mime="application/pdf"
        )