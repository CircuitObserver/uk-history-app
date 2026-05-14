import streamlit as st
from huggingface_hub import InferenceClient
from fpdf import FPDF

# --- PAGE CONFIG ---
st.set_page_config(page_title="UK History Researcher", page_icon="🇬🇧")

# --- INITIALIZE CLIENT ---
# This client automatically finds the correct 2026 endpoint for any model
if "HF_TOKEN" in st.secrets:
    client = InferenceClient(api_key=st.secrets["HF_TOKEN"])
else:
    st.error("Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

def query_ai(year):
    try:
        # We use the official chat completion method
        # If Qwen is busy, you can swap the model ID here to 'meta-llama/Llama-3.1-8B-Instruct'
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[
                {"role": "system", "content": "You are a British historian."},
                {"role": "user", "content": f"Summarize the year {year} in the UK. Focus on Politics, Culture, and Economy."}
            ],
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"TECHNICAL ERROR: {str(e)}"

# --- PDF GENERATION ---
def create_pdf(text, year):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"UK History: {year}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=11)
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- UI ---
st.title("🇬🇧 UK History Researcher")
year_input = st.number_input("Enter Year:", min_value=1, max_value=2026, value=2024)

if st.button("Give Info"):
    with st.spinner("Accessing Hugging Face Inference..."):
        answer = query_ai(year_input)
        st.session_state['summary'] = answer

if 'summary' in st.session_state:
    st.markdown("---")
    # This shows EXACTLY what the AI returned, errors and all
    st.info(st.session_state['summary'])
    
    if len(st.session_state['summary']) > 50 and "TECHNICAL ERROR" not in st.session_state['summary']:
        pdf_data = create_pdf(st.session_state['summary'], year_input)
        st.download_button("Download PDF", data=bytes(pdf_data), file_name=f"UK_{year_input}.pdf")