import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
from huggingface_hub import InferenceClient
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="BankBuddy India", 
    page_icon="🏦", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. PROFESSIONAL UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    .header-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .header-title { font-size: 2.5rem; font-weight: 800; margin: 0; }
    .header-subtitle { color: #cbd5e1; font-size: 1.1rem; }
    
    /* Ranked Tables */
    table { width: 100%; border-collapse: separate; border-spacing: 0; margin: 20px 0; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; background: white; }
    thead tr { background-color: #1e3a8a; color: white; text-align: left; }
    th { padding: 15px; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; }
    td { padding: 15px; border-bottom: 1px solid #f1f5f9; color: #334155; }
    
    /* Rank 1 Gold Highlight */
    tbody tr:first-child { background-color: #fffbeb !important; }
    tbody tr:first-child td { color: #b45309; font-weight: 700; }
    tbody tr:first-child td:first-child { border-left: 5px solid #fbbf24; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. API KEY MANAGEMENT ---
if "GOOGLE_API_KEY" in st.secrets:
    google_key = st.secrets["GOOGLE_API_KEY"]
else:
    google_key = None

# Optional: Add HF Token in secrets for backup (HUGGINGFACE_TOKEN)
if "HUGGINGFACE_TOKEN" in st.secrets:
    hf_token = st.secrets["HUGGINGFACE_TOKEN"]
else:
    hf_token = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 4. LIVE DATA ENGINE ---
def search_web(query):
    """
    Fetches real-time data from DuckDuckGo.
    """
    try:
        # We ask for 'comparison table' to get structured data
        search_query = f"{query} current interest rates india comparison 2025"
        # timelimit='m' ensures data is from the LAST MONTH
        results = DDGS().text(search_query, region='in-en', max_results=6, timelimit='m')
        if results:
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return None
    except:
        return None

# --- 5. BRAIN 1: GOOGLE GEMINI (PRIMARY) ---
def ask_google(prompt, api_key):
    genai.configure(api_key=api_key)
    # Cycle through models to avoid traffic jams
    models = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-001", "models/gemini-1.5-flash-8b", "models/gemini-pro"]
    
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except:
            continue
    return None # All Google models failed

# --- 6. BRAIN 2: OPEN SOURCE (BACKUP via Hugging Face) ---
def ask_opensource(prompt, token=None):
    """
    Uses Mistral-7B via Hugging Face Inference API.
    Works even if Google is down.
    """
    try:
        # If no token provided, it uses the public free tier (rate limited but works)
        client = InferenceClient(token=token)
        
        # We use Mistral-7B-Instruct (Very smart open source model)
        model_id = "mistralai/Mistral-7B-Instruct-v0.3"
        
        response = client.text_generation(
            prompt, 
            model=model_id, 
            max_new_tokens=1000, 
            temperature=0.3
        )
        return f"**[Note: Google Busy. Answered by OpenSource Mistral AI]**\n\n{response}"
    except Exception as e:
        return None

# --- 7. MASTER ORCHESTRATOR ---
def get_best_response(user_query, search_context, google_key, hf_key):
    
    context = f"WEB DATA:\n{search_context}" if search_context else "Web search failed. Use internal knowledge."
    
    # Universal Prompt for both AIs
    prompt = f"""
    Act as BankBuddy India.
    
    USER QUESTION: {user_query}
    LIVE DATA: {context}
    
    TASK:
    1. Rank the banks in a Markdown Table.
    2. Rank 1 = Best Benefit (High Interest for Savings/FD, Low Interest for Loans).
    3. Column 1 MUST be "Rank 🏆".
    4. Focus on major Indian banks.
    """
    
    # Attempt 1: Google Gemini
    if google_key:
        response = ask_google(prompt, google_key)
        if response: return response

    # Attempt 2: Open Source (Hugging Face)
    # Even if HF key is missing, it tries public API
    response = ask_opensource(prompt, hf_key)
    if response: return response

    # Attempt 3: Raw Data Fallback
    if search_context:
        return f"⚠️ **AI Servers Busy:** Both Google and OpenSource AI are overloaded.\n\n**Here is the raw data I found:**\n\n{search_context}"
    
    return "⚠️ **System Offline:** Unable to connect to Search or AI. Please try again in 1 minute."

# --- 8. SIDEBAR UI ---
with st.sidebar:
    st.markdown("### 🧠 AI Engine Settings")
    
    if not google_key:
        google_key = st.text_input("🔹 Google Gemini Key", type="password")
        st.markdown("[Get Free Google Key](https://aistudio.google.com/app/apikey)")
    else:
        st.success("✅ Google Gemini: Active")

    # Option to add Hugging Face Key for better Backup performance
    if not hf_token:
        st.markdown("---")
        hf_token = st.text_input("🔸 Hugging Face Token (Optional Backup)", type="password")
        st.markdown("[Get Free HF Token](https://huggingface.co/settings/tokens)")
        st.caption("Add this for robust backup.")
    else:
        st.success("✅ OpenSource Backup: Active")
        
    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# --- 9. MAIN INTERFACE ---
st.markdown("""
<div class="header-container">
    <div class="header-title">BankBuddy India 🇮🇳</div>
    <div class="header-subtitle">Powered by Google Gemini + Open Source Mistral AI</div>
</div>
""", unsafe_allow_html=True)

# Quick Start
if not st.session_state.chat_history:
    col1, col2, col3, col4 = st.columns(4)
    q = None
    if col1.button("🏆 FD Ranks"): q = "Rank top 8 Indian banks by highest 1-Year FD rates"
    if col2.button("🏠 Home Loans"): q = "Rank SBI, HDFC, ICICI, Axis by lowest Home Loan rates"
    if col3.button("🚗 Car Loans"): q = "Rank banks offering cheapest Car Loans in India"
    if col4.button("🏦 Savings"): q = "Rank top banks by highest Savings Account Interest Rates"
    
    if q:
        st.session_state.chat_history.append({"role": "user", "content": q})
        with st.chat_message("user", avatar="👤"): st.write(q)
        if google_key:
            with st.chat_message("assistant", avatar="🏦"):
                with st.spinner("Analyzing Market Data..."):
                    d = search_web(q)
                    r = get_best_response(q, d, google_key, hf_token)
                    st.markdown(r)
                    st.session_state.chat_history.append({"role": "assistant", "content": r})

# Chat Loop
for msg in st.session_state.chat_history:
    avatar = "👤" if msg["role"] == "user" else "🏦"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if user_input := st.chat_input("Ex: 'Rank all banks for Personal Loan rates'"):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"): st.write(user_input)
    
    if not google_key:
        st.warning("Please enter at least a Google API Key in the sidebar.")
    else:
        with st.chat_message("assistant", avatar="🏦"):
            with st.spinner("Checking Live Rates..."):
                d = search_web(user_input)
                # Master Function calls Google -> Then OpenSource -> Then Raw Data
                r = get_best_response(user_input, d, google_key, hf_token)
                st.markdown(r)
                st.session_state.chat_history.append({"role": "assistant", "content": r})
