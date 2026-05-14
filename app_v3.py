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
    .stNumberInput div div input {
        border-radius: 10px;
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
                    "content": (
                        "You are a professional British historian. "
                        "Provide facts ONLY for the specific year requested. "
                        "If the user asks for a year like 200, do not assume they mean 2000. "
                        "Format with bold headers for Politics, Culture, and Economy."
                    )
                },
                {"role": "user", "content": f"Provide a historical summary for the UK in the year {year} AD."}
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
st.write("Enter a specific year or grab a random one to reveal the archives of British history.")

# Initialize the year in session state if it doesn't exist
if 'year_input_key' not in st.session_state:
    st.session_state['year_input_key'] = 2024

col_input, col_rand, col_reveal = st.columns([3, 1.2, 1.5], vertical_alignment="bottom")

with col_input:
    # We bind the value to session_state['year_input_key']
    year_val = st.number_input(
        "Enter Year (1 - 2026):", 
        min_value=1, 
        max_value=2026, 
        value=st.session_state['year_input_key'],
        format="%d",
        key="actual_year_input" # Static key for the widget
    )

with col_rand:
    if st.button("🎲 Random", use_container_width=True):
        # Update the state of the widget directly
        new_year = random.randint(1066, 2024)
        st.session_state['actual_year_input'] = new_year
        st.rerun()

with col_reveal:
    reveal_clicked = st.button("📜 Reveal History", use_container_width=True)

# Use the widget's current state value
current_year = st.session_state['actual_year_input']

if reveal_clicked:
    with st.spinner(f"Consulting the archives for {current_year}..."):
        answer = query_ai(current_year)
        st.session_state['summary'] = answer
        st.session_state['last_year'] = current_year

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
                st.download_button(
                    label="📥 Download PDF", 
                    data=bytes(pdf_data), 
                    file_name=f"UK_History_{st.session_state['last_year']}.pdf",
                    use_container_width=True
                )
            except:
                st.warning("PDF too complex to generate.")
        with c2:
            share_text = f"I just discovered what happened in the UK in {st.session_state['last_year']} using this AI tool! 🇬🇧"
            app_url = "https://uk-history-app-mut9nsgjpmzgfaylrkw68d.streamlit.app/"
            twitter_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(share_text)}&url={urllib.parse.quote(app_url)}"
            
            st.markdown(f'''
                <a href="{twitter_url}" target="_blank" style="text-decoration: none;">
                    <button style="width:100%; height:45px; border-radius:10px; background-color:#1DA1F2; color:white; border:none; cursor:pointer; font-weight:bold;">
                        🐦 Share on Twitter
                    </button>
                </a>
            ''', unsafe_allow_html=True)