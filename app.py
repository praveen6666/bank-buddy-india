import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- CONFIGURATION ---
# initial_sidebar_state="expanded" forces the sidebar to show up on load
st.set_page_config(
    page_title="BankBuddy India", 
    page_icon="🏦", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS (Removed the lines that hid the header/sidebar button)
st.markdown("""
<style>
    .main {background-color: #f5f7f9;}
    .stChatMessage {border-radius: 15px; padding: 10px;}
    h1 {color: #1e3a8a;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (Now Guaranteed to Show) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830284.png", width=50)
    st.title("BankBuddy India")
    st.markdown("**Setup**")
    
    # API Key Input
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    
    st.markdown("---")
    st.markdown("[👉 Get Free API Key](https://aistudio.google.com/app/apikey)")
    st.info("I search official bank websites for real-time rates.")

# --- LOGIC ---
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
        
        context_text = f"REAL-TIME WEB DATA:\n{search_context}" if search_context else "Warning: Web search failed
