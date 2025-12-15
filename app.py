import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import time

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
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .header-title { font-size: 2.5rem; font-weight: 800; margin: 0; }
    
    /* Tables */
    table { width: 100%; border-collapse: separate; border-spacing: 0; margin: 20px 0; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }
    thead tr { background-color: #1e3a8a; color: white; text-align: left; }
    th { padding: 15px; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; }
    td { padding: 15px; border-bottom: 1px solid #f1f5f9; color: #334155; }
    
    /* Rank 1 Highlight */
    tbody tr:first-child { background-color: #fffbeb !important; }
    tbody tr:first-child td { color: #b45309; font-weight: 700; }
    tbody tr:first-child td:first-child { border-left: 5px solid #fbbf24; }
    
    /* Footer/Header Hiding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---

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
        search_query = f"{query} comparison interest rates india banks list 2025"
        results = DDGS().text(search_query, region='in-en', max_results=5, timelimit='m')
        if results:
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return None
    except:
        return None

# --- BACKUP BRAIN (Llama 3 via DuckDuckGo) ---
def get_fallback_response(query, context):
    """
    This runs if Google is busy. It uses DuckDuckGo's free AI chat (Llama 3.1).
    No API Key required.
    """
    try:
        prompt = f"""
        Act as BankBuddy India.
        User Query: {query}
        Web Data: {context}
        
        Task: 
        1. Compare banks in a Rank-wise Table (Rank 1 = Best Rate).
        2. If Loan: Lowest rate first. If Savings/FD: Highest rate first.
        3. Be concise.
        """
        # "llama-3.1-70b" is free via DDG Chat
        results = DDGS().chat(prompt, model="llama-3.1-70b") 
        return f"**[Note: Google was busy, switched to Llama-3 Backup]**\n\n{results}"
    except Exception as e:
        return f"All systems busy. Please wait 1 minute. (Error: {e})"

# --- PRIMARY BRAIN (Google Gemini) ---
def get_agent_response(user_query, search_context, api_key):
    # 1. Try Google Gemini First
    genai.configure(api_key=api_key)
    
    context = f"WEB DATA:\n{search_context}" if search_context else "Web search failed. Use internal knowledge."
    
    prompt = f"""
    You are BankBuddy, India's Top Financial AI.
    USER QUERY: {user_query}
    LATEST DATA: {context}
    
    INSTRUCTIONS:
    1. **AUTO-RANK:** Sort the table.
       - Savings/FD: High to Low (Best Rate = Rank 1).
       - Loans: Low to High (Cheapest Rate = Rank 1).
    2. **FORMAT:** Column 1 must be "Rank 🏆".
    """
    
    models_to_try = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-8b", "models/gemini-pro"]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except:
            continue # If Flash fails, try Pro, etc.

    # 2. If ALL Google models fail, activate Fallback
    return get_fallback_response(user_query, search_context)

# --- 4. UI ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if not has_secret_key:
        api_key = st.text_input("🔑 API Key", type="password")
    else:
        st.success("✅ Secure Connection")
    
    st.markdown("---")
    if st.button("🗑️ New Chat"):
        st.session_state.chat_history = []
        st.rerun()

st.markdown("""
<div class="header-container">
    <div class="header-title">BankBuddy India 🇮🇳</div>
    <div class="header-subtitle">AI-Powered Rank & Comparison Engine</div>
</div>
""", unsafe_allow_html=True)

# Buttons
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
        if api_key:
            with st.chat_message("assistant", avatar="🏦"):
                with st.spinner("Analyzing..."):
                    d = search_web(q)
                    r = get_agent_response(q, d, api_key)
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
    
    if not api_key:
        st.error("Please enter API Key.")
    else:
        with st.chat_message("assistant", avatar="🏦"):
            with st.spinner("Processing (Checking Google & Backup AI)..."):
                d = search_web(user_input)
                r = get_agent_response(user_input, d, api_key)
                st.markdown(r)
                st.session_state.chat_history.append({"role": "assistant", "content": r})
