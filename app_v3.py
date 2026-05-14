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
    /* Main Button Styling */
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
    /* Input box styling */
    .stNumberInput div div input {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZE CLIENT ---
if "HF_TOKEN" in st.secrets:
    client = InferenceClient(api_key=st.secrets["HF_TOKEN"])
else:
    st.error("Missing HF_TOKEN in Streamlit Secrets. Please add it to continue.")
    st.stop()

def query_ai(year):
    try:
        # Fenced prompt to handle small years (like 200) and prevent prompt injection
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a professional British historian. "
                        "Only provide facts about the United Kingdom for the specific year requested. "
                        "If the user asks for a year like 200, do not assume they mean 2000. "
                        "Format your response clearly with bold headers for Politics, Culture, and Economy."
                    )
                },
                {"role": "user", "content": f"The year is exactly {year} AD. Provide a historical summary for the UK."}
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
    # Removing non-ASCII characters for basic FPDF compatibility
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- UI LAYOUT ---
st.title("🇬🇧 UK Year Researcher")
st.write("Enter a specific year or grab a random one to reveal the archives of British history.")

# FEATURE: Professional One-Line Layout with Vertical Alignment
col_input, col_rand, col_reveal = st.columns([3, 1.2, 1.5], vertical_alignment="bottom")

with col_input:
    # We use a session state key for the value so the randomizer can update it
    year_input = st.number_input(
        "Enter Year (1 - 2026):", 
        min_value=1, 
        max_value=2026, 
        value=st.session_state.get('display_year', 2024),
        format="%d",
        key="year_box"
    )

with col_rand:
    if st.button("🎲 Random", use_container_width=True):
        st.session_state['display_year'] = random.randint(1, 2024)
        st.rerun()

with col_reveal:
    reveal_clicked = st.button("📜 Reveal History", use_container_width=True)

# Final variable to use for the AI query
current_year = st.session_state.get('year_box', year_input)

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
    
    # Show actions if content is substantial
    if len(st.session_state['summary']) > 100:
        c1, c2 = st.columns(2)
        
        with c1:
            try:
                pdf_data = create_pdf(st.session_state['summary'], st.session_state['last_year'])
                st.download_button(
                    label="📥 Download as PDF", 
                    data=bytes(pdf_data), 
                    file_name=f"UK_History_{st.session_state['last_year']}.pdf",
                    use_container_width=True
                )
            except:
                st.warning("PDF too complex to generate, please copy text.")
        
        with c2:
            # FEATURE: Twitter Share Button
            share_text = f"I just discovered what happened in the UK in the year {st.session_state['last_year']} using this AI History tool! 🇬🇧"
            # Your specific app URL
            app_url = "https://uk-history-app-mut9nsgjpmzgfaylrkw68d.streamlit.app/"
            encoded_text = urllib.parse.quote(share_text)
            encoded_url = urllib.parse.quote(app_url)
            twitter_url = f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_url}"
            
            # HTML Twitter Button
            st.markdown(f'''
                <a href="{twitter_url}" target="_blank" style="text-decoration: none;">
                    <button style="width:100%; height:45px; border-radius:10px; background-color:#1DA1F2; color:white; border:none; cursor:pointer; font-weight:bold;">
                        🐦 Share on Twitter
                    </button>
                </a>
            ''', unsafe_allow_html=True)