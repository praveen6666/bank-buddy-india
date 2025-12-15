import streamlit as st
import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

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
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.3)
    search = DuckDuckGoSearchResults(backend="news")
    
    # Simple RAG: Search then Answer
    try:
        search_data = search.run(f"{query} interest rates india official bank sites 2025")
    except:
        search_data = "No live data available."

    template = """
    You are BankBuddy, an Indian banking expert.
    User Question: {input}
    Real-time Search Data: {context}
    
    Instructions:
    1. Compare products in a Markdown Table.
    2. Only use official Indian banks (SBI, HDFC, ICICI, Axis, etc).
    3. Give a specific recommendation at the end.
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({"input": query, "context": search_data})
    return response.content

# --- UI ---
st.header("Compare Savings, Loans & FDs 📊")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask about loans, savings, or FDs...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Checking latest bank rates..."):
            response = get_response(user_input, api_key)
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
