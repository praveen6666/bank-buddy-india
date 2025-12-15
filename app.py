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

# --- 2. ATTRACTIVE UI CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* Header Styling */
    .header-container {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .header-title { font-size: 2.5rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .header-subtitle { font-size: 1.1rem; opacity: 0.95; margin-top: 10px; font-weight: 400; }

    /* Ranked Table Styling */
    table { width: 100%; border-collapse: separate; border-spacing: 0; margin: 20px 0; border-radius: 12px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
    
    /* Header Row */
    thead tr { background-color: #1e3a8a; color: white; text-align: left; }
    th { padding: 15px; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px; }
    
    /* Data Rows */
    td { padding: 15px; border-bottom: 1px solid #f1f5f9; color: #334155; font-size: 0.95rem; }
    tbody tr:nth-of-type(even) { background-color: #f8fafc; }
    
    /* RANK 1 HIGHLIGHT (Gold Standard) */
    tbody tr:first-child { background-color: #fffbeb !important; }
    tbody tr:first-child td { color: #b45309; font-weight: 700; border-bottom: 1px solid #fcd34d; }
    tbody tr:first-child td:first-child { border-left: 5px solid #fbbf24; }

    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIC & API ---

# Secrets Management
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    has_secret_key = True
else:
    has_secret_key = False
    api_key = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def search_web(query):
    try:
        # We specifically ask for a 'list' to get rankable data
        search_query = f"{query} list of interest rates india banks comparison 2025"
        results = DDGS().text(search_query, region='in-en', max_results=6, timelimit='m')
        if results:
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return None
    except:
        return None

def get_gemini_response(user_query, search_context, api_key):
    genai.configure(api_key=api_key)
    
    context = f"WEB DATA:\n{search_context}" if search_context else "Web search failed. Use internal knowledge."
    
    # --- PROMPT: FORCING AUTOMATIC RANKING ---
    prompt = f"""
    You are BankBuddy, a Data-Driven Financial Analyst.
    
    USER QUERY: {user_query}
    LATEST DATA: {context}
    
    ### STRICT SORTING & RANKING RULES:
    1. **AUTOMATIC SORTING:** You MUST sort the table rows based on "User Benefit".
       - **Savings / FD / RD:** Sort High to Low (Highest Rate = Rank 1).
       - **Loans / Credit Cards:** Sort Low to High (Lowest Rate = Rank 1).
       
    2. **TABLE STRUCTURE:** 
       The first column MUST be **"Rank"**.
       | Rank 🏆 | Bank Name | Interest Rate | Key Feature / Processing Fee |
       |---------|-----------|---------------|------------------------------|
       | 1       | ...       | ...           | ...                          |
       | 2       | ...       | ...           | ...                          |
    
    3. **DATA SCOPE:** 
       - If the user asks generally (e.g. "Best Home Loan"), include the top 5-7 major banks (SBI, HDFC, ICICI, Axis, Kotak, BOB, PNB).
       - If specific banks are named, rank only those.
    
    4. **NO FILLER:** Do not write long introductions. Go straight to the Ranking Table.
    """
    
    # --- ROBUST RETRY LOGIC (ANTI-CRASH) ---
    # Rotates through models to find one that isn't busy
    model_list = [
        "models/gemini-1.5-flash", 
        "models/gemini-1.5-flash-001", 
        "models/gemini-1.5-flash-8b",
        "models/gemini-1.5-pro",
        "models/gemini-pro"
    ]
    
    for attempt in range(5):
        try:
            # Pick a model based on attempt number
            current_model = model_list[attempt % len(model_list)]
            model = genai.GenerativeModel(current_model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            # Handle Traffic Limits
            if "429" in error_msg or "quota" in error_msg.lower() or "503" in error_msg:
                time.sleep(3 + (attempt * 2)) # Wait 3s, 5s, 7s...
                continue
            return f"Error: {error_msg}"
            
    return "⚠️ High Traffic: Google's AI servers are busy. Please wait 30 seconds and try again."

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if not has_secret_key:
        api_key = st.text_input("🔑 API Key", type="password")
        st.caption("Enter key to start.")
    else:
        st.success("✅ Secure Connection")
    
    st.markdown("---")
    if st.button("🗑️ New Chat"):
        st.session_state.chat_history = []
        st.rerun()

# --- 5. MAIN INTERFACE ---
st.markdown("""
<div class="header-container">
    <div class="header-title">BankBuddy India 🇮🇳</div>
    <div class="header-subtitle">AI-Powered Rank & Comparison Engine</div>
</div>
""", unsafe_allow_html=True)

# Quick Start Buttons
if not st.session_state.chat_history:
    col1, col2, col3, col4 = st.columns(4)
    
    q = None
    if col1.button("🏆 Best FD Rates"): q = "Rank top 8 Indian banks by highest 1-Year FD interest rates"
    if col2.button("🏠 Home Loan Rank"): q = "Rank SBI, HDFC, ICICI, Axis, and Kotak by lowest Home Loan rates"
    if col3.button("🚗 Car Loan Rank"): q = "Rank banks offering the cheapest Car Loans in India right now"
    if col4.button("🏦 Savings Rank"): q = "Rank top banks by highest Savings Account Interest Rates"
    
    if q:
        st.session_state.chat_history.append({"role": "user", "content": q})
        with st.chat_message("user", avatar="👤"): st.write(q)
        if api_key:
            with st.chat_message("assistant", avatar="🏦"):
                with st.spinner("Analyzing market data & Ranking..."):
                    data = search_web(q)
                    res = get_gemini_response(q, data, api_key)
                    st.markdown(res)
                    st.session_state.chat_history.append({"role": "assistant", "content": res})

# Chat History Display
for msg in st.session_state.chat_history:
    avatar = "👤" if msg["role"] == "user" else "🏦"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# User Input
if user_input := st.chat_input("Ex: 'Compare Personal Loan rates of all banks'"):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"): st.write(user_input)
    
    if not api_key:
        st.error("⚠️ Please enter API Key.")
    else:
        with st.chat_message("assistant", avatar="🏦"):
            with st.spinner("Checking rates & Ranking results..."):
                data = search_web(user_input)
                res = get_gemini_response(user_input, data, api_key)
                st.markdown(res)
                st.session_state.chat_history.append({"role": "assistant", "content": res})
