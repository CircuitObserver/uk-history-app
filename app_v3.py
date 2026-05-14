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

def query_ai(year, era):
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a professional British historian. "
                        "Provide a detailed summary with bold headers for Politics/Power, Culture, and Economy/Life. "
                        "If the year is BCE, focus on archaeology and tribal movements (e.g., Celts, Romans). "
                        "ALSO, at the end, provide a catchy one-sentence summary for a tweet preceded by [TWEET]."
                    )
                },
                {"role": "user", "content": f"Provide a historical/archaeological summary for the UK in the year {year} {era}."}
            ],
            max_tokens=1100
        )
        full_text = response.choices[0].message.content
        if "[TWEET]" in full_text:
            summary_part, tweet_part = full_text.split("[TWEET]")
            return summary_part.strip(), tweet_part.strip()
        return full_text, f"Checking out the year {year} {era} in UK history!"
    except Exception as e:
        return f"AI is currently unavailable. (Error: {str(e)})", "Error."

# --- PDF GENERATION ---
def create_pdf(text, year, era):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"UK History Report: {year} {era}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=11)
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 8, clean_text)
    return pdf.output()

# --- UI LAYOUT ---
st.title("🇬🇧 UK History Researcher")
st.write("Explore British history from Ancient BCE tribes to modern 2026.")

if 'target_year' not in st.session_state:
    st.session_state['target_year'] = 2024
if 'target_era' not in st.session_state:
    st.session_state['target_era'] = "AD"

# Swapping Order: Input -> Era -> Reveal -> Random
col_input, col_era, col_reveal, col_rand = st.columns([2, 1, 1.5, 1.2], vertical_alignment="bottom")

with col_input:
    year_val = st.number_input("Year:", min_value=1, max_value=5000, value=st.session_state['target_year'], format="%d")
    st.session_state['target_year'] = year_val

with col_era:
    era_val = st.selectbox("Era:", ["AD", "BCE"], index=0 if st.session_state['target_era'] == "AD" else 1)
    st.session_state['target_era'] = era_val

run_search = False

with col_reveal:
    if st.button("📜 Reveal", use_container_width=True):
        run_search = True

with col_rand:
    if st.button("🎲 Random", use_container_width=True):
        # Weighted random: 80% AD, 20% BCE for better variety
        if random.random() > 0.2:
            st.session_state['target_year'] = random.randint(1066, 2024)
            st.session_state['target_era'] = "AD"
        else:
            st.session_state['target_year'] = random.randint(50, 3000)
            st.session_state['target_era'] = "BCE"
        run_search = True

if run_search:
    with st.spinner(f"Consulting archives for {st.session_state['target_year']} {st.session_state['target_era']}..."):
        summary, tweet_snippet = query_ai(st.session_state['target_year'], st.session_state['target_era'])
        st.session_state['summary'] = summary
        st.session_state['tweet_snippet'] = tweet_snippet
        st.session_state['last_year'] = f"{st.session_state['target_year']} {st.session_state['target_era']}"
    st.rerun()

# --- RESULTS ---
if 'summary' in st.session_state:
    st.markdown("---")
    st.info(f"### 🏛️ Historical Summary: {st.session_state['last_year']}")
    st.markdown(st.session_state['summary'])
    
    if len(st.session_state['summary']) > 100:
        c1, c2 = st.columns(2)
        with c1:
            try:
                pdf_data = create_pdf(st.session_state['summary'], st.session_state['target_year'], st.session_state['target_era'])
                st.download_button("📥 Download PDF", data=bytes(pdf_data), file_name=f"UK_{st.session_state['last_year'].replace(' ','_')}.pdf", use_container_width=True)
            except: st.warning("PDF Error.")
        with c2:
            snippet = st.session_state.get('tweet_snippet', "Discovering UK history!")
            app_url = "https://uk-history-app-mut9nsgjpmzgfaylrkw68d.streamlit.app/"
            twitter_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(snippet + ' 🇬🇧')}&url={urllib.parse.quote(app_url)}"
            st.markdown(f'<a href="{twitter_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:45px; border-radius:10px; background-color:#1DA1F2; color:white; border:none; cursor:pointer; font-weight:bold;">🐦 Tweet Result</button></a>', unsafe_allow_html=True)

st.markdown("---")
st.caption("⚠️ **Disclaimer:** This application uses AI to generate historical and archaeological summaries. Accuracy for ancient dates (BCE) is based on archaeological estimates. Please verify facts with primary sources.")