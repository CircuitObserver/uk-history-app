import streamlit as st
import requests
from fpdf import FPDF

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="UK History Researcher",
    page_icon="🇬🇧",
    layout="centered"
)

# --- API SETUP ---
# Using a very stable, highly-available model
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-v0.1"

try:
    if "HF_TOKEN" in st.secrets:
        headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    else:
        st.error("Admin Note: Please add HF_TOKEN to your Streamlit Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

def query_ai(prompt):
    # We simplified the prompt format to be more universal
    payload = {
        "inputs": f"Summarize the history of the United Kingdom in the year {prompt}. List political and cultural events:",
        "parameters": {"max_new_tokens": 500, "wait_for_model": True}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        # If the model is not found, we try one backup model automatically
        if response.status_code == 404:
            backup_url = "https://api-inference.huggingface.co/models/gpt2"
            response = requests.post(backup_url, headers=headers, json=payload, timeout=30)

        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get('generated_text', "No text generated.")
        elif isinstance(result, dict) and "error" in result:
            return f"AI says: {result['error']}"
        else:
            return "The AI returned an empty response. Try clicking the button again."
            
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
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- UI ---
st.title("🇬🇧 UK Year Researcher")
st.write("Enter a year to get a summary of what happened in the UK.")

target_year = st.number_input("Year:", min_value=1, max_value=2026, value=2024)

if st.button("Give Info"):
    with st.spinner("Talking to the AI..."):
        answer = query_ai(str(target_year))
        st.session_state['summary_text'] = answer
        st.session_state['searched_year'] = target_year

# --- DISPLAY ---
if 'summary_text' in st.session_state:
    st.markdown("---")
    output = st.session_state['summary_text']
    st.write(output)
    
    if "Error" not in output and "AI says" not in output:
        pdf_output = create_pdf(output, st.session_state['searched_year'])
        st.download_button(
            label="Download PDF",
            data=bytes(pdf_output),
            file_name=f"UK_{st.session_state['searched_year']}.pdf",
            mime="application/pdf"
        )