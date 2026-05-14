import streamlit as st
from huggingface_hub import InferenceClient
from fpdf import FPDF
import random
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="UK History Researcher",
    page_icon="🇬🇧",
    layout="centered"
)

# --- CUSTOM BRITISH STYLING ---
st.markdown("""
    <style>
    .stButton>button {
        background-color: #00247d;
        color: white;
        border-radius: 10px;
        border: 2px solid #cf142b;
        height: 3rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #cf142b;
        color: white;
        border: 2px solid #00247d;
    }
    /* Fixed height for the column area to prevent jumping */
    [data-testid="column"] {
        display: flex;
        align-items: flex-end;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZE CLIENT ---
if "HF_TOKEN" in st.secrets:
    client = InferenceClient(api_key=st.secrets["HF_TOKEN"])
else:
    st.error("Missing HF_TOKEN in Streamlit Secrets.")
    st.stop()

def query_ai(year):
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional British historian. Provide facts ONLY for the year requested. Format with bold headers."
                },
                {"role": "user", "content": f"Historical summary for the UK in the year {year} AD."}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"The AI is busy. Please try again. (Error: {str(e)})"

# --- PDF GENERATION ---
def create_pdf(text, year):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"UK History Report: {year}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=11)
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- UI LAYOUT ---
st.title("🇬🇧 UK Year Researcher")
st.write("Enter a year or click Random to instantly reveal British history archives.")

if 'target_year' not in st.session_state:
    st.session_state['target_year'] = 2024

# Create columns for the interface
col_input, col_rand, col_reveal = st.columns([3, 1.2, 1.5], vertical_alignment="bottom")

with col_input:
    year_val = st.number_input(
        "Enter Year (1 - 2026):", 
        min_value=1, 
        max_value=2026, 
        value=st.session_state['target_year'],
        format="%d"
    )
    st.session_state['target_year'] = year_val

# Flags to trigger AI search outside the column block
run_search = False

with col_rand:
    if st.button("🎲 Random", use_container_width=True):
        st.session_state['target_year'] = random.randint(1066, 2024)
        run_search = True

with col_reveal:
    if st.button("📜 Reveal", use_container_width=True):
        run_search = True

# --- AI LOGIC (OUTSIDE COLUMNS TO PREVENT MISALIGNMENT) ---
if run_search:
    with st.spinner(f"Consulting archives for {st.session_state['target_year']}..."):
        st.session_state['summary'] = query_ai(st.session_state['target_year'])
        st.session_state['last_year'] = st.session_state['target_year']
    st.rerun()

# --- RESULTS DISPLAY ---
if 'summary' in st.session_state:
    st.markdown("---")
    st.info(f"### 🏛️ Historical Summary for Year {st.session_state['last_year']}")
    st.markdown(st.session_state['summary'])
    
    if len(st.session_state['summary']) > 100:
        c1, c2 = st.columns(2)
        with c1:
            try:
                pdf_data = create_pdf(st.session_state['summary'], st.session_state['last_year'])
                st.download_button("📥 Download PDF", data=bytes(pdf_data), file_name=f"UK_{st.session_state['last_year']}.pdf", use_container_width=True)
            except:
                st.warning("PDF too complex.")
        with c2:
            share_text = f"I discovered UK history for {st.session_state['last_year']}! 🇬🇧"
            app_url = "https://uk-history-app-mut9nsgjpmzgfaylrkw68d.streamlit.app/"
            twitter_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(share_text)}&url={urllib.parse.quote(app_url)}"
            st.markdown(f'<a href="{twitter_url}" target="_blank"><button style="width:100%; height:45px; border-radius:10px; background-color:#1DA1F2; color:white; border:none; cursor:pointer; font-weight:bold;">🐦 Tweet Result</button></a>', unsafe_allow_html=True)

# --- FOOTER / DISCLAIMER ---
st.markdown("---")
st.caption("⚠️ **Disclaimer:** This application uses Artificial Intelligence to generate historical summaries. While we strive for accuracy, AI can occasionally produce incorrect dates or events. Users are encouraged to verify important information with primary historical sources.")