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

# --- 4. ROBUST SEARCH ENGINE ---
def search_web(query):
    """
    Tries to fetch data. If blocked, returns None (Does NOT crash).
    """
    try:
        # Try simplified query to avoid blockers
        results = DDGS().text(f"{query} india interest rates 2025", region='in-en', max_results=4)
        if results:
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except:
        pass # Fail silently, let AI handle it
    return None

# --- 5. AI ENGINE 1: GOOGLE ---
def ask_google(prompt, api_key):
    genai.configure(api_key=api_key)
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
        response = client.text_generation(prompt, model="mistralai/Mistral-7B-Instruct-v0.3", max_new_tokens=1000)
        return f"**[Note: Google Busy. Answer via OpenSource]**\n\n{response}"
    except:
        return None

# --- 7. HARDCODED SNAPSHOT (LAST RESORT) ---
def get_static_fallback(query):
    return """
    ⚠️ **Live Connection Failed.**
    
    However, here is a **Snapshot of Recent Market Rates (Estimates)**:
    
    | Rank 🏆 | Bank Name | FD Rate (1 Yr) | Home Loan (Start) | Savings (Up to) |
    |---|---|---|---|---|
    | 1 | IDFC First | 7.50% | 8.85% | 7.00% |
    | 2 | IndusInd | 7.50% | 8.75% | 6.75% |
    | 3 | Kotak | 7.10% | 8.70% | 4.00% |
    | 4 | SBI | 6.80% | 8.50% | 2.70% |
    | 5 | HDFC | 6.60% | 8.50% | 3.00% |
    | 6 | ICICI | 6.70% | 8.75% | 3.00% |
    
    *Please verify directly with the bank as real-time search is currently blocked.*
    """

# --- 8. MASTER LOGIC ---
def get_best_response(user_query, google_key, hf_key):
    
    # 1. Try Search
    search_context = search_web(user_query)
    
    # 2. Prepare Context
    if search_context:
        context_msg = f"LIVE WEB DATA:\n{search_context}"
    else:
        context_msg = "WARNING: Web search blocked. Answer based on your INTERNAL KNOWLEDGE of Indian Banks."

    prompt = f"""
    Act as BankBuddy India.
    USER QUERY: {user_query}
    CONTEXT: {context_msg}
    
    TASK:
    1. Rank the banks in a Markdown Table.
    2. Rank 1 = Best Benefit.
    3. If web data is missing, ESTIMATE based on general knowledge (SBI~6.8%, IDFC~7.5%).
    4. Do not say "I cannot answer". Give the best estimate.
    """
    
    # 3. Try Google
    if google_key:
        res = ask_google(prompt, google_key)
        if res: return res

    # 4. Try Open Source
    res = ask_opensource(prompt, hf_key)
    if res: return res

    # 5. Total Failure -> Show Static Snapshot
    return get_static_fallback(user_query)

# --- 9. UI ---
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
        if not google_key and not hf_token:
             st.warning("⚠️ For best results, enter an API Key. Using backup mode...")
        
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
