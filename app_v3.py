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
    }
    .stButton>button:hover {
        background-color: #cf142b;
        color: white;
        border: 2px solid #00247d;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZE CLIENT ---
if "HF_TOKEN" in st.secrets:
    client = InferenceClient(api_key=st.secrets["HF_TOKEN"])
else:
    st.error("Missing HF_TOKEN in Secrets.")
    st.stop()

def query_ai(year):
    try:
        # FEATURE: Enhanced System Prompt to fix "Year 200" bug and prevent prompt injection
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a professional British historian. "
                        "Provide facts ONLY for the specific year requested. "
                        f"If the user asks for year {year}, do not assume they mean {year}0 or {year}00. "
                        "Format with headers for Politics, Culture, and Economy."
                    )
                },
                {"role": "user", "content": f"Provide a historical summary for the UK in the year {year} AD."}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"The AI is currently busy or waking up. Please try again in a few seconds. (Error: {str(e)})"

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

# --- UI ---
st.title("🇬🇧 UK Year Researcher")
st.write("Explore the rich history of the United Kingdom, one year at a time.")

# FEATURE: Layout columns for input and random button
col1, col2 = st.columns([2, 1])

with col1:
    year_input = st.number_input(
        "Enter Year (1 - 2026):", 
        min_value=1, 
        max_value=2026, 
        value=2024,
        format="%d"
    )

with col2:
    st.write("##") # Spacer
    if st.button("🎲 Random Year"):
        year_input = random.randint(1066, 2024)
        st.session_state['random_year'] = year_input
        # Trigger a rerun to update the number input visually
        st.rerun()

# Use the random year if it was just generated
current_year = st.session_state.get('random_year', year_input)

if st.button("📜 Reveal History"):
    with st.spinner(f"Consulting the archives for {current_year}..."):
        answer = query_ai(current_year)
        st.session_state['summary'] = answer
        st.session_state['last_year'] = current_year

# --- RESULTS DISPLAY ---
if 'summary' in st.session_state:
    st.markdown("---")
    st.info(f"### Historical Summary for {st.session_state['last_year']}")
    st.markdown(st.session_state['summary'])
    
    # Check for valid content before showing download/share
    if len(st.session_state['summary']) > 100:
        c1, c2 = st.columns(2)
        
        with c1:
            pdf_data = create_pdf(st.session_state['summary'], st.session_state['last_year'])
            st.download_button(
                label="📥 Download as PDF", 
                data=bytes(pdf_data), 
                file_name=f"UK_History_{st.session_state['last_year']}.pdf"
            )
        
        with c2:
            # FEATURE: Twitter Share Button
            share_text = f"I just discovered what happened in the UK in the year {st.session_state['last_year']} using this AI History tool! 🇬🇧"
            # Replace with your actual app URL
            app_url = "https://uk-history-app-mut9nsgjpmzgfaylrkw68d.streamlit.app/"
            encoded_text = urllib.parse.quote(share_text)
            encoded_url = urllib.parse.quote(app_url)
            twitter_url = f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_url}"
            
            st.markdown(f'''
                <a href="{twitter_url}" target="_blank">
                    <button style="width:100%; height:45px; border-radius:10px; background-color:#1DA1F2; color:white; border:none; cursor:pointer;">
                        🐦 Share on Twitter
                    </button>
                </a>
            ''', unsafe_allow_html=True)