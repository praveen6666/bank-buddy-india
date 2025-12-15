import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
from huggingface_hub import InferenceClient
import time
import datetime

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
    
    /* Table Styling */
    table { width: 100%; border-collapse: separate; border-spacing: 0; margin: 20px 0; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; background: white; }
    thead tr { background-color: #1e3a8a; color: white; text-align: left; }
    th { padding: 15px; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; }
    td { padding: 15px; border-bottom: 1px solid #f1f5f9; color: #334155; }
    
    /* Rank 1 Highlight */
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

# --- 4. OFFICIAL DOMAIN SEARCH ENGINE ---
def search_web(query):
    ddgs = DDGS()
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # LIST OF OFFICIAL INDIAN BANK DOMAINS
    # We explicitly tell DuckDuckGo to look ONLY inside these websites.
    official_domains = (
        "site:sbi.co.in OR "
        "site:hdfcbank.com OR "
        "site:icicibank.com OR "
        "site:axisbank.com OR "
        "site:kotak.com OR "
        "site:bankofbaroda.in OR "
        "site:pnbindia.in OR "
        "site:unionbankofindia.co.in OR "
        "site:canarabank.com OR "
        "site:idfcfirstbank.com OR "
        "site:indusind.com OR "
        "site:centralbankofindia.co.in OR "
        "site:indianbank.in" 
    )
    
    targeted_query = f"{query} interest rates {today} {official_domains}"
    
    try:
        # 1. Official Domain Search
        results = ddgs.text(targeted_query, region='in-en', max_results=7)
        if results:
            return "\n".join([f"- OFFICIAL SOURCE: {r['title']} \n  DATA: {r['body']}" for r in results])
    except:
        pass

    try:
        # 2. News Fallback (For very recent changes today)
        news_query = f"{query} interest rates india banks {today}"
        results = ddgs.news(news_query, region='in-en', max_results=4)
        if results:
            return "\n".join([f"- NEWS UPDATE: {r['title']} \n  DATA: {r['body']}" for r in results])
    except:
        pass

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
        response = client.text_generation(prompt, model="mistralai/Mistral-7B-Instruct-v0.3", max_new_tokens=1500)
        return f"**[Backup AI]**\n\n{response}"
    except:
        return None

# --- 7. MASTER LOGIC ---
def get_best_response(user_query, google_key, hf_key):
    
    # 1. Fetch Real-Time Data
    search_context = search_web(user_query)
    today_date = datetime.date.today().strftime("%d %B %Y")
    
    if search_context:
        context_msg = f"REAL-TIME OFFICIAL WEB DATA ({today_date}):\n{search_context}"
    else:
        context_msg = f"WARNING: Live search blocked. Provide estimated rates based on internal knowledge (2024/2025)."

    prompt = f"""
    Act as BankBuddy India.
    TODAY'S DATE: {today_date}
    
    USER QUERY: {user_query}
    
    OFFICIAL DATA SOURCES: 
    {context_msg}
    
    INSTRUCTIONS:
    1. **Create a Ranked Table** from the data.
    2. **STRICT RANKING:** 
       - Loans: Lowest Rate = Rank 1.
       - Savings/FD: Highest Rate = Rank 1.
    3. **VERIFY:** Only list banks found in the web data or major known banks.
    4. **NO DUPLICATES:** Do not list the same bank twice.
    """
    
    if google_key:
        res = ask_google(prompt, google_key)
        if res: return res

    res = ask_opensource(prompt, hf_key)
    if res: return res

    return "⚠️ **System Busy:** Unable to fetch live rates. Please wait 1 minute."

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
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

st.markdown("""
<div class="header-container">
    <div class="header-title">BankBuddy India 🇮🇳</div>
    <div class="header-subtitle">Real-Time Data from Official Bank Websites</div>
</div>
""", unsafe_allow_html=True)

# --- 9. DISPLAY CHAT HISTORY ---
for msg in st.session_state.chat_history:
    avatar = "👤" if msg["role"] == "user" else "🏦"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- 10. INPUT & PROCESS ---
user_input = None

col1, col2, col3, col4 = st.columns(4)
if col1.button("🏆 FD Rates"): user_input = "Get latest FD rates from official sbi.co.in, hdfcbank.com, icicibank.com"
if col2.button("🏠 Home Loans"): user_input = "Get latest Home Loan rates from official bankofbaroda.in, sbi.co.in, hdfcbank.com"
if col3.button("🚗 Car Loans"): user_input = "Get latest Car Loan rates from official bank websites"
if col4.button("🏦 Savings"): user_input = "Get latest Savings Account rates from official bank websites"

chat_val = st.chat_input("Ex: 'Latest SBI vs HDFC Home Loan rates'")
if chat_val: user_input = chat_val

if user_input:
    with st.chat_message("user", avatar="👤"):
        st.write(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant", avatar="🏦"):
        with st.spinner("Accessing Official Bank Domains (sbi.co.in, .bank.in, .com)..."):
            response = get_best_response(user_input, google_key, hf_token)
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
