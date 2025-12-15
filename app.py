import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="BankBuddy India", page_icon="🏦", layout="wide")

st.markdown("""
<style>
    .main {background-color: #f5f7f9;}
    .stChatMessage {border-radius: 15px; padding: 10px;}
    .stMarkdown {font-family: 'Helvetica', sans-serif;}
    h1 {color: #1e3a8a;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("BankBuddy India 🇮🇳")
    st.markdown("Your AI Financial Advisor.")
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    st.markdown("[Get Free Key Here](https://aistudio.google.com/app/apikey)")
    st.warning("Please ensure your API Key is active and copied correctly.")
    st.divider()
    st.info("I search official bank websites (SBI, HDFC, ICICI, etc.) for real-time rates.")

# --- SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- FUNCTIONS ---
def search_web(query):
    """
    Searches the web using DuckDuckGo directly (No LangChain).
    """
    try:
        results = DDGS().text(f"{query} interest rates india official bank sites", max_results=4)
        if results:
            # Format results nicely
            search_text = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            return search_text
        return "No specific data found on the web."
    except Exception as e:
        return f"Search Error: {e}"

def get_gemini_response(user_query, search_context, api_key):
    """
    Directly connects to Google Gemini API.
    """
    try:
        # 1. Configure the API
        genai.configure(api_key=api_key)
        
        # 2. Select Model (Try Flash first, it's fast and free)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 3. Create Prompt
        prompt = f"""
        You are BankBuddy, an expert Indian Banking AI Agent.
        
        USER QUESTION: {user_query}
        
        REAL-TIME WEB DATA (Use this to answer):
        {search_context}
        
        INSTRUCTIONS:
        1. Compare bank products (Savings, Loans, FDs) in a clean Markdown Table.
        2. Highlight the "Best Choice" based on interest rates or benefits.
        3. If the web data contains specific rates (e.g., "7.2%"), USE THEM.
        4. Focus on major Indian banks: SBI, HDFC, ICICI, Axis, Kotak, IDFC.
        5. Be polite and professional.
        """
        
        # 4. Generate Content
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"**Connection Error:** {str(e)}\n\n*Tip: Check if your API Key is correct.*"

# --- MAIN UI ---
st.header("Compare Savings, Loans & FDs 📊")

# Display Chat History
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
user_input = st.chat_input("Ask about loans, savings, or FDs...")

if user_input:
    # 1. Show User Message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # 2. Process
    if not api_key:
        with st.chat_message("assistant"):
            st.error("Please enter your Google API Key in the sidebar to proceed.")
    else:
        with st.chat_message("assistant"):
            status_placeholder = st.empty()
            
            # Step A: Search
            status_placeholder.markdown("🔍 *Searching official bank websites...*")
            web_data = search_web(user_input)
            
            # Step B: Analyze
            status_placeholder.markdown("🧠 *Analyzing rates and features...*")
            ai_response = get_gemini_response(user_input, web_data, api_key)
            
            # Step C: Show Result
            status_placeholder.empty()
            st.markdown(ai_response)
            
            # Save to history
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
