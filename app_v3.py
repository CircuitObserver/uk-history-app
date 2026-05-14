import streamlit as st
import requests
from fpdf import FPDF

# --- PAGE CONFIG ---
st.set_page_config(page_title="UK History Researcher", page_icon="🇬🇧")

# --- 2026 ROUTER ENDPOINT ---
API_URL = "https://router.huggingface.co/hf-inference/v1/chat/completions"

def query_ai(year):
    if "HF_TOKEN" not in st.secrets:
        return "Error: HF_TOKEN missing from Streamlit Secrets."
    
    headers = {
        "Authorization": f"Bearer {st.secrets['HF_TOKEN']}",
        "Content-Type": "application/json"
    }
    
    # Llama-3.3-70B is the current high-stability model for the 2026 Router
    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct", 
        "messages": [
            {"role": "system", "content": "You are a professional British historian. Summarize the year in the UK with sections for Politics, Culture, and Economy."},
            {"role": "user", "content": f"What happened in the United Kingdom in {year}?"}
        ],
        "max_tokens": 1000,
        "temperature": 0.5
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=40)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            # This will show you exactly why it failed without crashing
            return f"Error {response.status_code}: {response.text}"
                
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
    # Strict cleaning for PDF (removing non-standard characters)
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- UI ---
st.title("🇬🇧 UK History Researcher")
st.write("Enter a year to receive a summary of UK historical events.")

year_input = st.number_input("Enter Year:", min_value=1, max_value=2026, value=2024)

if st.button("Give Info"):
    with st.spinner(f"Requesting data for {year_input}..."):
        answer = query_ai(year_input)
        st.session_state['summary'] = answer

if 'summary' in st.session_state:
    st.markdown("---")
    
    # Display the result
    st.markdown(st.session_state['summary'])
    
    # Only show PDF button if the response is actually content
    if len(st.session_state['summary']) > 60 and "Error" not in st.session_state['summary']:
        try:
            pdf_data = create_pdf(st.session_state['summary'], year_input)
            st.download_button(
                label="📥 Download Research as PDF", 
                data=bytes(pdf_data), 
                file_name=f"UK_History_{year_input}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF Error: {e}")