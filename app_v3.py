import streamlit as st
import requests
from fpdf import FPDF

# --- PAGE CONFIG ---
st.set_page_config(page_title="UK History Researcher", page_icon="🇬🇧")

# --- VERIFIED 2026 ENDPOINT ---
# This is the dedicated serverless path that works with free tokens
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

def query_ai(year):
    if "HF_TOKEN" not in st.secrets:
        return "Error: HF_TOKEN missing from Streamlit Secrets."
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    
    # Qwen 2.5 expects a clear instruction format
    prompt = f"Provide a historical summary of the United Kingdom for the year {year}. Focus on Politics, Culture, and Economy."
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 800,
            "temperature": 0.5,
            "wait_for_model": True  # Crucial: Tells the server to 'warm up' the model if it's idle
        }
    }

    try:
        # Increased timeout to 60s because serverless models take time to 'spin up'
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            # Serverless API returns a list with a 'generated_text' key
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', "No content returned.")
            return str(result)
        
        elif response.status_code == 503:
            return "The AI is currently 'waking up' on Hugging Face's servers. Please wait 30 seconds and click 'Give Info' again."
        else:
            return f"Server Error {response.status_code}: {response.text}"
                
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- PDF GENERATION ---
def create_pdf(text, year):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"UK History: {year}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=11)
    # Clean text for PDF compatibility
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- UI ---
st.title("🇬🇧 UK History Researcher")
st.write("Enter a year to receive an AI-powered summary of events in the UK.")

year_input = st.number_input("Enter Year:", min_value=1, max_value=2026, value=2024)

if st.button("Give Info"):
    with st.spinner(f"Requesting data from {MODEL_ID}..."):
        answer = query_ai(year_input)
        st.session_state['summary'] = answer

if 'summary' in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state['summary'])
    
    # Show PDF button only if valid text was returned
    if "Error" not in st.session_state['summary'] and len(st.session_state['summary']) > 50:
        try:
            pdf_data = create_pdf(st.session_state['summary'], year_input)
            st.download_button(
                label="📥 Download Research as PDF", 
                data=bytes(pdf_data), 
                file_name=f"UK_History_{year_input}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.warning("PDF generation failed due to formatting, but you can read the text above.")