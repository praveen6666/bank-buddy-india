import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import time
import random

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="BankBuddy India", 
    page_icon="🏦", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* Header */
    .header-container {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .header-title { font-size: 2.5rem; font-weight: 800; margin: 0; letter-spacing: -1px; }
    .header-subtitle { font-size: 1.1rem; opacity: 0.9; margin-top: 8px; font-weight: 400; }

    /* Tables - Rank Wise Styling */
    table { width: 100%; border-collapse: separate; border-spacing: 0; margin: 20px 0; border-radius: 12px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
    thead tr { background-color: #1e3a8a; color: white; text-align: left; }
    th { padding: 15px; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px; }
    td { padding: 15px; border-bottom: 1px solid #f1f5f9; color: #334155; }
    tbody tr:nth-of-type(even) { background-color: #f8fafc; }
    tbody tr:hover { background-color: #f1f5f9; transition: 0.2s; }
    
    /* Gold Color for Rank 1 */
    tbody tr:first-child td { font-weight: bold; color: #1e3a8a; background-color: #fffbeb; border-left: 5px solid #fbbf24; }

    /* Chat Bubbles */
    .stChatMessage { background: white; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }

    /* Remove Default Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. API & LOGIC ---

# Check Secrets
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    has_secret_key = True
else:
    has_secret_key = False
    api_key = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def search_web(query):
    """
    Fetches more results (max_results=6) to allow better ranking.
    """
    try:
        # We append 'comparison table' to hint the search engine we want lists
        search_query = f"{query} comparison table interest rates india top banks 2025"
        results = DDGS().text(search_query, region='in-en', max_results=6, timelimit='m')
        if results:
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return None
    except:
        return None

def get_best_model(api_key):
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferences = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-001", "models/gemini-1.5-pro", "models/gemini-pro"]
        for p in preferences:
            if p in models: return p
        return models[0] if models else "models/gemini-pro"
    except:
        return "models/gemini-pro"

def get_gemini_response(user_query, search_context, api_key):
    model_name = get_best_model(api_key)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    context = f"WEB DATA:\n{search_context}" if search_context else "Web search failed. Use internal knowledge."
    
    # --- INTELLIGENT RANKING PROMPT ---
    prompt = f"""
    You are BankBuddy, India's Best Financial AI.
    USER QUERY: {user_query}
    {context}
    
    MANDATORY INSTRUCTIONS:
    1. **RANKING:** If the user asks to compare "all" or multiple banks, you MUST provide a Ranked Table.
       - **For Savings/FDs:** Rank #1 is the HIGHEST Interest Rate.
       - **For Loans:** Rank #1 is the LOWEST Interest Rate.
    
    2. **SCOPE:** If "all banks" is asked, limit comparison to these Top 7:
       - SBI, HDFC, ICICI, Axis, Kotak, IDFC First, PNB.
    
    3. **TABLE FORMAT:**
       | Rank 🏆 | Bank Name | Rate (%) | Key Feature/Processing Fee |
       |---------|-----------|----------|----------------------------|
       | 1       | ...       | ...      | ...                        |
    
    4. **VERDICT:** End with a bold "Winner" recommendation based on the data.
    """
    
    # Retry Logic for Rate Limits
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e):
                time.sleep(5 + (attempt * 5))
                continue
            return f"Error: {str(e)}"
    return "⚠️ Server busy. Please try again in 30 seconds."

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if not has_secret_key:
        api_key = st.text_input("🔑 API Key", type="password")
        st.markdown("[Get Free Key](https://aistudio.google.com/app/apikey)")
    else:
        st.success("✅ Connected")
    
    st.markdown("---")
    if st.button("🗑️ New Chat"):
        st.session_state.chat_history = []
        st.rerun()

# --- 5. MAIN UI ---
st.markdown("""
<div class="header-container">
    <div class="header-title">BankBuddy India 🇮🇳</div>
    <div class="header-subtitle">Rank-wise Comparisons for Loans, FDs & Savings</div>
</div>
""", unsafe_allow_html=True)

# Quick Actions
if not st.session_state.chat_history:
    col1, col2, col3, col4 = st.columns(4)
    prompt = None
    # Updated buttons to trigger ranking
    if col1.button("🏆 Rank FD Rates"): prompt = "Rank top 7 Indian banks by highest FD rates for 1 year tenure"
    if col2.button("🏠 Home Loan Rank"): prompt = "Compare and rank Home Loan rates of SBI, HDFC, ICICI, Axis"
    if col3.button("🚗 Car Loan Rank"): prompt = "Rank banks offering lowest Car Loan interest rates in India"
    if col4.button("🏦 Savings Rank"): prompt = "Rank IDFC, Kotak, SBI, and HDFC by Savings Account interest rates"
    
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"): st.write(prompt)
        if api_key:
            with st.chat_message("assistant", avatar="🏦"):
                with st.spinner("Analyzing & Ranking Banks..."):
                    data = search_web(prompt)
                    res = get_gemini_response(prompt, data, api_key)
                    st.markdown(res)
                    st.session_state.chat_history.append({"role": "assistant", "content": res})

# Chat Loop
for msg in st.session_state.chat_history:
    avatar = "👤" if msg["role"] == "user" else "🏦"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Input
if user_input := st.chat_input("Ex: 'Rank all banks for Personal Loan rates'"):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"): st.write(user_input)
    
    if not api_key:
        st.error("Please enter API Key.")
    else:
        with st.chat_message("assistant", avatar="🏦"):
            with st.spinner("Gathering data & Calculating ranks..."):
                data = search_web(user_input)
                res = get_gemini_response(user_input, data, api_key)
                st.markdown(res)
                st.session_state.chat_history.append({"role": "assistant", "content": res})
