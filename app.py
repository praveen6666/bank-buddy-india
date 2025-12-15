import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- CONFIGURATION ---
st.set_page_config(page_title="BankBuddy India", page_icon="🏦", layout="wide")

# Hide default Streamlit elements for a cleaner look
st.markdown("""
<style>
    .main {background-color: #f5f7f9;}
    .stChatMessage {border-radius: 15px; padding: 10px;}
    h1 {color: #1e3a8a;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("BankBuddy India 🇮🇳")
    st.markdown("Your AI Financial Advisor.")
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    st.markdown("[Get Free Key Here](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.info("I search official bank websites for the latest rates.")

# --- SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- FUNCTIONS ---
def search_web(query):
    """Searches DuckDuckGo for Indian Bank Data."""
    try:
        # region="in-en" forces Indian results
        # timelimit="m" ensures data is from the last month
        results = DDGS().text(
            f"{query} current interest rates india official bank sites", 
            region='in-en', 
            max_results=5,
            timelimit='m'
        )
        if results:
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return None
    except:
        return None

def get_best_model(api_key):
    """Silently finds the best working model."""
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Priority list
        if "models/gemini-1.5-flash" in models: return "models/gemini-1.5-flash"
        if "models/gemini-pro" in models: return "models/gemini-pro"
        return models[0] if models else "models/gemini-pro"
    except:
        return "models/gemini-pro"

def get_gemini_response(user_query, search_context, api_key):
    try:
        model_name = get_best_model(api_key)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        context_text = f"REAL-TIME WEB DATA:\n{search_context}" if search_context else "Warning: Web search failed. Use internal knowledge."
        
        prompt = f"""
        You are BankBuddy, an expert Indian Banking AI Agent.
        USER QUESTION: {user_query}
        {context_text}
        
        INSTRUCTIONS:
        1. Compare bank products (Savings, Loans, FDs) in a clean Markdown Table.
        2. Use the web data to provide specific interest rates.
        3. Recommend the best option.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Error: {str(e)}"

# --- MAIN UI ---
st.header("Compare Savings, Loans & FDs 📊")

# Display History
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
user_input = st.chat_input("Ask about loans, savings, or FDs...")

if user_input:
    # Show User Message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # Process Message
    if not api_key:
        with st.chat_message("assistant"):
            st.error("Please enter your API Key in the sidebar.")
    else:
        with st.chat_message("assistant"):
            # Simple spinner, no text logs
            with st.spinner("Thinking..."):
                web_data = search_web(user_input)
                ai_response = get_gemini_response(user_input, web_data, api_key)
                st.markdown(ai_response)
                
                # Optional: Show sources in a collapsed box at the bottom
                if web_data:
                    with st.expander("View Data Sources"):
                        st.text(web_data)
            
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
