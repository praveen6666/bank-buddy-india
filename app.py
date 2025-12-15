import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
from huggingface_hub import InferenceClient
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
    .header-subtitle { color: #cbd5e1; font-size: 1.1rem; }
    
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

# --- 4. TIME-AWARE SEARCH ENGINE ---
def search_web(query):
    ddgs = DDGS()
    
    # Get Current Timeline (e.g., "December 2025")
    now = datetime.datetime.now()
    current_month_year = now.strftime("%B %Y")
    current_year = now.strftime("%Y")
    
    # 1. STRICT FRESHNESS QUERY
    # We force the search engine to look for the CURRENT Month/Year text on the page.
    # We restrict official domains.
    fresh_query = f"{query} interest rates {current_month_year} site:co.in OR site:bank"
    
    # 2. NEWS QUERY (For Revision Announcements)
    news_query = f"{query} rate hike {current_month_year} India"

    search_results = []

    try:
        # SEARCH 1: TEXT with 'w' (Past Week) limit
        # This is the key fix. It forces data indexed in the last 7 days.
        results = ddgs.text(fresh_query, region='in-en', max_results=5, timelimit='w')
        if results:
            search_results.append("\n".join([f"- [LATEST UPDATE] {r['title']}: {r['body']}" for r in results]))
    except:
        pass

    try:
        # SEARCH 2: NEWS (Always fresh)
        results = ddgs.news(news_query, region='in-en', max_results=3)
        if results:
            search_results.append("\n".join([f"- [NEWS] {r['title']}: {r['body']}" for r in results]))
    except:
        pass
        
    if not search_results:
        # Fallback: Try "Past Month" if "Past Week" failed
        try:
            results = ddgs.text(f"{query} rates {current_year} India", region='in-en', max_results=5, timelimit='m')
            if results:
                search_results.append("\n".join([f"- [MONTHLY DATA] {r['title']}: {r['body']}" for r in results]))
        except:
            pass

    return "\n".join(search_results) if search_results else None

# --- 5. AI ENGINES ---
def ask_google(prompt, api_key):
    genai.configure(api_key=api_key)
    for model_name in ["models/gemini-1.5-flash", "models/gemini-1.5-flash-8b", "models/gemini-pro"]:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except:
            continue
    return None

def ask_opensource(prompt, token=None):
    try:
        client = InferenceClient(token=token)
        response = client.text_generation(prompt, model="mistralai/Mistral-7B-Instruct-v0.3", max_new_tokens=1000)
        return response
    except:
        return None

# --- 6. MASTER LOGIC ---
def get_best_response(user_query, google_key, hf_key):
    # 1. Search Web (With Time Filter)
    search_context = search_web(user_query)
    today_date = datetime.datetime.now().strftime("%d %B %Y")
    
    # 2. Build Prompt
    if search_context:
        context_msg = f"FRESH WEB DATA ({today_date}):\n{search_context}"
        fallback_instruction = ""
    else:
        # IMPORTANT: If search fails, do NOT use hardcoded numbers. 
        # Tell AI to estimate ranges based on market knowledge.
        context_msg = "Live search blocked. Use your internal knowledge of Late 2024/2025 market standards."
        fallback_instruction = "Since live data is missing, provide EXPECTED RATE RANGES (e.g., '8.50% - 9.00%') instead of exact numbers to avoid misleading the user."

    prompt = f"""
    Act as BankBuddy India.
    CURRENT DATE: {today_date}
    USER QUERY: {user_query}
    DATA: {context_msg}
    
    INSTRUCTIONS:
    1. **Rank the banks** in a clean Markdown Table.
    2. **Freshness Check:** Look for dates in the data. If data mentions {today_date.split()[-1]} (Current Year), prioritize it.
    3. **Official Data:** Use the exact rates found in the text.
    4. **Loans:** Sort Low to High. **Savings:** Sort High to Low.
    5. **Clean UI:** No URLs in the table.
    6. {fallback_instruction}
    """
    
    # 3. Try Google
    if google_key:
        res = ask_google(prompt, google_key)
        if res: return res

    # 4. Try Open Source
    res = ask_opensource(prompt, hf_key)
    if res: return res

    # 5. Last Resort (Safe Message)
    return """
    ⚠️ **Live Data Unavailable**
    
    I am currently unable to verify the *exact* rates for today due to network restrictions.
    
    To avoid showing you old data, please check the official websites directly.
    """

# --- 7. UI ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if not google_key:
        google_key = st.text_input("🔑 Google Key", type="password")
    else:
        st.success("✅ Google: Active")
    if not hf_token:
        hf_token = st.text_input("🗝️ HuggingFace", type="password")
    else:
        st.success("✅ Backup: Active")
    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

st.markdown("""
<div class="header-container">
    <div class="header-title">BankBuddy India 🇮🇳</div>
    <div class="header-subtitle">Real-Time Fresh Data (Past Week)</div>
</div>
""", unsafe_allow_html=True)

# History
for msg in st.session_state.chat_history:
    avatar = "👤" if msg["role"] == "user" else "🏦"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Input
user_input = None
col1, col2, col3, col4 = st.columns(4)
if col1.button("🏆 FD Rates"): user_input = "Get latest FD rates for 1 year from sbi.co.in, hdfcbank.com, icicibank.com"
if col2.button("🏠 Home Loans"): user_input = "Get latest Home Loan rates from bankofbaroda.in, sbi.co.in, hdfcbank.com"
if col3.button("🚗 Car Loans"): user_input = "Get latest Car Loan rates from official bank websites"
if col4.button("🏦 Savings"): user_input = "Get latest Savings Account rates from official bank websites"

chat_val = st.chat_input("Ex: 'Latest SBI vs HDFC Home Loan rates'")
if chat_val: user_input = chat_val

if user_input:
    with st.chat_message("user", avatar="👤"):
        st.write(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant", avatar="🏦"):
        with st.spinner(f"Scanning for data updates (Last 7 Days)..."):
            response = get_best_response(user_input, google_key, hf_token)
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
