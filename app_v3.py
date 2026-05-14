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
    
    # Using Qwen 2.5 - It is currently the most compatible model for the Router
    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct", 
        "messages": [
            {"role": "system", "content": "You are a professional British historian providing concise summaries."},
            {"role": "user", "content": f"Summarize the major events in the UK for the year {year}. Focus on Politics, Culture, and Economy."}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=40)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        
        # If Qwen fails, this error handling will tell us exactly why
        elif response.status_code == 400:
            return f"Error 400: The server didn't like the request. Details: {response.text}"
        elif response.status_code == 503:
            return "The AI is currently 'waking up'. Please wait 30 seconds and click 'Give Info' again."
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
    # Filter text for PDF
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
    st.markdown(st.session_state['summary'])
    
    # Check if the summary looks like actual content before showing PDF
    if len(st.session_state['summary']) > 50 and "Error" not in st.session_state['summary']:
        pdf_data = create_pdf(st.session_state['summary'], year_input)
        st.download_button(
            label="📥 Download Research as PDF", 
            data=bytes(pdf_data), 
            file_name=f"UK_History_{year_input}.pdf",
            mime="application/pdf"
        )