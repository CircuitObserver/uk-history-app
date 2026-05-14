import streamlit as st
import requests
from fpdf import FPDF

st.set_page_config(page_title="UK History Researcher", page_icon="🇬🇧")

# --- THE 2026 STABLE ENDPOINT ---
# DeepSeek-V3 is the current 'Always On' model for the free Inference Providers
API_URL = "https://router.huggingface.co/hf-inference/v1/chat/completions"
MODEL_ID = "deepseek-ai/DeepSeek-V3"

def query_ai(year):
    if "HF_TOKEN" not in st.secrets:
        return "Error: HF_TOKEN missing from Secrets."
    
    headers = {
        "Authorization": f"Bearer {st.secrets['HF_TOKEN']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": "You are a British history expert."},
            {"role": "user", "content": f"Summarize the year {year} in the United Kingdom. Focus on Politics, Culture, and Economy."}
        ],
        "max_tokens": 900,
        "stream": False
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            # If DeepSeek fails, it's likely a token issue or temporary downtime
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
    # Removing special characters to prevent PDF crashes
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
    
    if len(st.session_state['summary']) > 50 and "Error" not in st.session_state['summary']:
        pdf_data = create_pdf(st.session_state['summary'], year_input)
        st.download_button("📥 Download PDF", data=bytes(pdf_data), file_name=f"UK_{year_input}.pdf")