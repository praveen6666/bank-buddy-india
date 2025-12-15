import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- CONFIGURATION ---
st.set_page_config(page_title="BankBuddy India", page_icon="🏦", layout="wide")

st.markdown("""
<style>
    .main {background-color: #f5f7f9;}
    .stChatMessage {border-radius: 15px; padding: 10px;}
    h1 {color: #1e3a8a;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("BankBuddy India 🇮🇳")
    st.markdown("Your AI Financial Advisor.")
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    st.markdown("[Get Free Key Here](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.info("I search official bank websites for real-time rates.")

# --- SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- FUNCTIONS ---
def search_web(query):
    """Searches DuckDuckGo."""
    try:
        results = DDGS().text(f"{query} interest rates india official bank sites", max_results=4)
        if results:
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return "No specific web data found."
    except Exception as e:
        return f"Search Error: {e}"

def get_best_model_name(api_key):
    """
    Asks Google which models are available and picks the best one.
    """
    try:
        genai.configure(api_key=api_key)
        # Get list of all models available to this key
        models = list(genai.list_models())
        
        # Filter for models that generate content
        available_names = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        # Priority list (Try to find these in the available list)
        preferences = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]
        
        # Return the first preference that exists in the available list
        for pref in preferences:
            if pref in available_names:
                return pref
        
        # If none of our preferences match, just take the first available one
        if available_names:
            return available_names[0]
            
        return None
    except Exception as e:
        # If listing fails, fallback to the most standard name
        return "models/gemini-pro"

def get_gemini_response(user_query, search_context, api_key):
    try:
        # 1. Find the correct model name
        model_name = get_best_model_name(api_key)
        if not model_name:
            return "Error: Your API Key is valid, but no text-generation models were found associated with it."

        # 2. Configure and Generate
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        You are BankBuddy, an expert Indian Banking AI Agent.
        
        USER QUESTION: {user_query}
        
        REAL-TIME WEB DATA:
        {search_context}
        
        INSTRUCTIONS:
        1. Compare bank products (Savings, Loans, FDs) in a clean Markdown Table.
        2. Give a "Best Choice" recommendation.
        3. Use the web data for rates.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"**System Error:** {str(e)}\n\n*Note: If you just updated the app, please wait 1 minute and refresh.*"

# --- MAIN UI ---
st.header("Compare Savings, Loans & FDs 📊")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask about loans, savings, or FDs...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    if not api_key:
        with st.chat_message("assistant"):
            st.error("Please enter your API Key in the sidebar.")
    else:
        with st.chat_message("assistant"):
            status_box = st.empty()
            
            status_box.markdown("🔍 *Searching web...*")
            web_data = search_web(user_input)
            
            status_box.markdown("🧠 *Connecting to Google AI...*")
            ai_response = get_gemini_response(user_input, web_data, api_key)
            
            status_box.empty()
            st.markdown(ai_response)
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
