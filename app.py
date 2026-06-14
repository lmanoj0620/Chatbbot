import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os  # (kept for future use if you want to set env vars)

st.title('ITKannadigaru ChatBot')

# --- Prompt Template ---
prompt = ChatPromptTemplate.from_messages([
    ('system', 'Hey, you are an AI assistant. Give clear and correct answers.'),
    ('user', 'Question: {question}')
])

# --- Sidebar Settings ---
st.sidebar.title('⚙️ Settings')
api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7)
tokens = st.sidebar.slider("Max Tokens", 50, 500, 100)
engine = st.sidebar.selectbox("Select engine", ["gpt-4.1-2025-04-14", "gpt-5-mini", "gpt-4o-mini", "gpt-4-turbo","gpt-4"])

# --- Function to Generate Response ---
def generate_response(question, api_key, temperature, tokens, engine):
    #  Pass API key directly into ChatOpenAI
    chat_model = ChatOpenAI(
        api_key=api_key,
        model=engine,
        temperature=temperature,
        max_tokens=tokens
    )

    parser = StrOutputParser()
    chain = prompt | chat_model | parser
    response = chain.invoke({"question": question})
    return response

# --- Main Input/Output ---
st.write("### Enter your question:")
user_input = st.text_input("Ask anything you want:")

if user_input and api_key:
    try:
        answer = generate_response(user_input, api_key, temperature, tokens, engine)
        st.success(answer)
    except Exception as e:
        st.error(f"Error: {e}")
elif user_input:
    st.warning("Please enter your API key.")
else:
    st.info("Type a question above to get started.")
