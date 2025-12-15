import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
from huggingface_hub import InferenceClient
import time
import random

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="BankBuddy India", 
    page_icon="🏦", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. CSS STYLING ---
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
    }
    .header-title { font-size: 2.5rem; font-weight: 800; margin: 0; }
    
    table { width: 100%; border-collapse: separate; border-spacing: 0; margin: 20px 0; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; background: white; }
    thead tr { background-color: #1e3a8a; color: white; text-align: left; }
    th { padding: 15px; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; }
    td { padding: 15px; border-bottom: 1px solid #f1f5f9; color: #334155; }
    tbody tr:first-child { background-color: #fffbeb !important; }
    tbody tr:first-child td { color: #b45309; font-weight: 700; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. API KEYS ---
if "GOOGLE_API_KEY" in st.secrets:
    google_key = st.secrets["GOOGLE_API_KEY"]
else:
    google_key = None

if "HUGGINGFACE_TOKEN" in st.secrets:
    hf_token = st.secrets["HUGGINGFACE_TOKEN"]
else:
    hf_token = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 4. ANTI-BLOCK SEARCH ENGINE ---
def search_web(query):
    """
    Tries 3 different search strategies to bypass blocks.
    """
    ddgs = DDGS()
    
    # Strategy 1: Specific Indian Search (Last Month)
    try:
        results = ddgs.text(f"{query} current interest rates india 2025", region='in-en', max_results=5, timelimit='m')
        if results: return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except:
        pass
        
    # Strategy 2: Global Search (Relaxed constraints)
    try:
        time.sleep(1) # Pause to avoid spam detection
        results = ddgs.text(f"{query} bank interest rates india", max_results=5)
        if results: return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except:
        pass

    # Strategy 3: News Search (Often unblocked)
    try:
        time.sleep(1)
        results = ddgs.news(f"{query} India Banks", max_results=3)
        if results: return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except:
        pass

    return None

# --- 5. AI ENGINE 1: GOOGLE ---
def ask_google(prompt, api_key):
    genai.configure(api_key=api_key)
    # Smart Fallback Models
    models = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-8b", "models/gemini-pro"]
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except:
            continue
    return None

# --- 6. AI ENGINE 2: OPEN SOURCE ---
def ask_opensource(prompt, token=None):
    try:
        client = InferenceClient(token=token)
        # Using Mistral 7B (Very reliable)
        response = client.text_generation(prompt, model="mistralai/Mistral-7B-Instruct-v0.3", max_new_tokens=1500)
        return f"**[Note: Google Busy. Answered by OpenSource AI]**\n\n{response}"
    except:
        return None

# --- 7. MASTER LOGIC ---
def get_best_response(user_query, google_key, hf_key):
    
    # 1. Try Search
    search_context = search_web(user_query)
    
    # 2. Smart Context Construction
    if search_context:
        context_msg = f"REAL-TIME WEB DATA:\n{search_context}"
    else:
        # CRITICAL FIX: If search fails, we tell AI to use INTERNAL MEMORY, not fail.
        context_msg = "NOTICE: Real-time search is currently blocked. You MUST use your internal training data (up to late 2024/2025) to provide the best estimated rates."

    prompt = f"""
    Act as BankBuddy India.
    USER QUERY: {user_query}
    CONTEXT: {context_msg}
    
    TASK:
    1. Rank the banks in a Markdown Table.
    2. Rank 1 = Best Benefit (High Interest for Savings/FD, Low Interest for Loans).
    3. Column 1 MUST be "Rank 🏆".
    4. If Web Data is present, use it.
    5. If Web Data is missing, ESTIMATE the rates based on major bank standards (e.g. SBI, HDFC standards).
    """
    
    # 3. Try Google
    if google_key:
        res = ask_google(prompt, google_key)
        if res: return res

    # 4. Try Open Source
    res = ask_opensource(prompt, hf_key)
    if res: return res

    # 5. Ultimate Fallback (If NO API keys work)
    return """
    ⚠️ **Configuration Error:**
    
    I cannot generate a response because:
    1. **Search is blocked** by the cloud server.
    2. **No valid API Key** (Google or HuggingFace) provided.
    
    *Please enter a Google API Key in the sidebar to activate the AI Brain.*
    """

# --- 8. UI ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if not google_key:
        google_key = st.text_input("🔑 Google Key", type="password")
    else:
        st.success("✅ Google: Active")
        
    if not hf_token:
        hf_token = st.text_input("🗝️ HuggingFace (Backup)", type="password")
    else:
        st.success("✅ Backup: Active")
        
    st.markdown("---")
    if st.button("🗑️ Reset"):
        st.session_state.chat_history = []
        st.rerun()

st.markdown("""
<div class="header-container">
    <div class="header-title">BankBuddy India 🇮🇳</div>
    <div class="header-subtitle">Always-On Financial AI</div>
</div>
""", unsafe_allow_html=True)

# Buttons
if not st.session_state.chat_history:
    col1, col2, col3, col4 = st.columns(4)
    q = None
    if col1.button("🏆 FD Ranks"): q = "Rank top banks by FD rates"
    if col2.button("🏠 Home Loans"): q = "Rank banks by Home Loan rates"
    if col3.button("🚗 Car Loans"): q = "Rank banks by Car Loan rates"
    if col4.button("🏦 Savings"): q = "Rank banks by Savings rates"
    
    if q:
        st.session_state.chat_history.append({"role": "user", "content": q})
        with st.chat_message("user", avatar="👤"): st.write(q)
        
        with st.chat_message("assistant", avatar="🏦"):
            with st.spinner("Analyzing..."):
                r = get_best_response(q, google_key, hf_token)
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
    
    with st.chat_message("assistant", avatar="🏦"):
        with st.spinner("Processing..."):
            r = get_best_response(user_input, google_key, hf_token)
            st.markdown(r)
            st.session_state.chat_history.append({"role": "assistant", "content": r})
