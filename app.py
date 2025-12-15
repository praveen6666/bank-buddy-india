import streamlit as st
import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

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
    st.info("I search official bank websites (SBI, HDFC, ICICI, etc.)")

# --- LOGIC ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def get_response(query, api_key):
    if not api_key:
        return "Please enter your API Key in the sidebar."
    
    # 1. Setup LLM
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.3)
    except Exception as e:
        return f"Error connecting to Google AI: {str(e)}"

    # 2. Safe Search Execution
    search_data = "Search unavailable (Using internal knowledge)."
    try:
        # Import inside function to prevent app-wide crash
        from langchain_community.tools import DuckDuckGoSearchResults
        search = DuckDuckGoSearchResults(backend="news")
        search_data = search.run(f"{query} interest rates india official bank sites 2025")
    except ImportError:
        print("Library 'duckduckgo-search' missing. Please add it to requirements.txt")
    except Exception as e:
        print(f"Search failed: {e}")

    # 3. Prompt Construction
    template = """
    You are BankBuddy, an Indian banking expert.
    
    User Question: {input}
    
    Latest Web Search Data (Use this if available): 
    {context}
    
    Instructions:
    1. Compare products in a clean Markdown Table.
    2. Focus on official Indian banks (SBI, HDFC, ICICI, Axis, etc).
    3. Give a specific recommendation at the end.
    4. If search data is missing, use your general knowledge but mention rates may vary.
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    try:
        response = chain.invoke({"input": query, "context": search_data})
        return response.content
    except Exception as e:
        return f"An error occurred during processing: {str(e)}"

# --- UI ---
st.header("Compare Savings, Loans & FDs 📊")

# Display History
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input Area
user_input = st.chat_input("Ask about loans, savings, or FDs...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing bank rates..."):
            response = get_response(user_input, api_key)
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
