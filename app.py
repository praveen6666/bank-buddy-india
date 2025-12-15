import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import time

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="BankBuddy India", 
    page_icon="🏦", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS (THE ATTRACTIVE UI) ---
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Background Color */
    .stApp {
        background-color: #f8fafc;
    }

    /* Header Styling */
    .header-container {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-top: 5px;
    }

    /* Chat Bubbles */
    .stChatMessage {
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #e2e8f0;
    }
    
    /* User Message Specifics (Streamlit doesn't allow direct CSS targeting of user bubble easily, 
       but we make the container consistent) */
       
    /* Tables */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 0.95em;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
    }
    thead tr {
        background-color: #1e3a8a;
        color: #ffffff;
        text-align: left;
        font-weight: bold;
    }
    th, td {
        padding: 12px 15px;
        border-bottom: 1px solid #dddddd;
    }
    tbody tr:nth-of-type(even) {
        background-color: #f3f4f6;
    }
    tbody tr:last-of-type {
        border-bottom: 2px solid #1e3a8a;
    }

    /* Quick Action Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 50px;
        background-color: #ffffff;
        color: #1e3a8a;
        border: 1px solid #cbd5e1;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #eff6ff;
        border-color: #1e3a8a;
        transform: translateY(-2px);
    }
    
    /* Remove default Streamlit Menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. API & LOGIC ---

# Secret Key Check
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
        results = DDGS().text(f"{query} interest rates india official bank sites", region='in-en', max_results=5, timelimit='m')
        if results:
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return None
    except:
        return None

def get_best_model(api_key):
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if "models/gemini-1.5-flash" in models: return "models/gemini-1.5-flash"
        return models[0] if models else "models/gemini-pro"
    except:
        return "models/gemini-pro"

def get_gemini_response(user_query, search_context, api_key):
    try:
        model_name = get_best_model(api_key)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        context = f"WEB DATA:\n{search_context}" if search_context else "Web search failed. Use internal knowledge."
        
        prompt = f"""
        You are BankBuddy, a professional Indian Financial AI.
        
        USER QUERY: {user_query}
        {context}
        
        FORMAT GUIDELINES:
        1. Start with a direct answer.
        2. Use a professional Markdown Table for comparisons (Bank | Rate | Details).
        3. Highlight the "Winner" or "Best Pick" in bold.
        4. Keep it concise and clean.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: #1e3a8a;'>⚙️ Settings</h2>", unsafe_allow_html=True)
    
    if not has_secret_key:
        api_key = st.text_input("🔑 Google API Key", type="password")
        st.caption("Enter key to activate agent.")
    else:
        st.success("✅ Secure Connection Active")
    
    st.markdown("---")
    st.info("💡 **Tip:** I search live data from SBI, HDFC, ICICI, and official sites.")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# --- 5. MAIN INTERFACE ---

# Custom Header
st.markdown("""
<div class="header-container">
    <div class="header-title">BankBuddy India 🇮🇳</div>
    <div class="header-subtitle">Your AI Financial Companion for Loans, Savings & FDs</div>
</div>
""", unsafe_allow_html=True)

# Quick Action Buttons
if len(st.session_state.chat_history) == 0:
    st.markdown("### 🚀 Quick Start")
    col1, col2, col3, col4 = st.columns(4)
    
    prompt = None
    if col1.button("💰 Best FD Rates"): prompt = "What are the current highest FD rates in India for 1 year tenure?"
    if col2.button("🏠 Home Loans"): prompt = "Compare home loan interest rates between SBI, HDFC, and ICICI."
    if col3.button("💳 Best Credit Card"): prompt = "Which is the best lifetime free credit card in India for rewards?"
    if col4.button("🏦 Savings Account"): prompt = "Compare Savings Account interest rates of IDFC First vs Kotak."
    
    if prompt:
        # Simulate user input
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.write(prompt)
            
        if not api_key:
            st.error("Please connect API Key.")
        else:
            with st.chat_message("assistant", avatar="🏦"):
                with st.spinner("Analyzing market rates..."):
                    web_data = search_web(prompt)
                    response = get_gemini_response(prompt, web_data, api_key)
                    st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})

# Chat Area
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🏦"):
            st.markdown(msg["content"])

# Input Box
user_input = st.chat_input("Type your financial question here...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.write(user_input)
    
    if not api_key:
        with st.chat_message("assistant", avatar="🏦"):
            st.error("⚠️ Setup Required: Please enter API Key in sidebar or secrets.")
    else:
        with st.chat_message("assistant", avatar="🏦"):
            with st.spinner("Thinking..."):
                web_data = search_web(user_input)
                ai_response = get_gemini_response(user_input, web_data, api_key)
                st.markdown(ai_response)
                
                if web_data:
                    with st.expander("🔍 View Data Sources"):
                        st.info(web_data)
            
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
