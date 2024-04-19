import os
import tempfile
import time
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(dirname(__file__)), '.env')
load_dotenv(dotenv_path)

import streamlit as st

from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import StrOutputParser
from vectaraIntegration import query, get_knowledge, initialize_vectara, upload_all_file
from langchain_community.llms import HuggingFaceEndpoint

HF_TOKEN = os.getenv("HF_TOKEN")
REPO_ID = "mistralai/Mistral-7B-Instruct-v0.2"


llm_base = HuggingFaceEndpoint(
    repo_id=REPO_ID,
    max_new_tokens=512,
    top_k=10,
    top_p=0.95,
    typical_p=0.95,
    temperature=0.01,
    repetition_penalty=1.03,
    huggingfacehub_api_token=HF_TOKEN
)

vectara_client = initialize_vectara()

prompt = PromptTemplate.from_template(
  """You are a professional and friendly "CommonWealth" Bank Customer Service and you are helping a client with provided bank knowledge. 
  
    If a client query is a question related to banks explain it in detail.
    If a client query is about general things answer it with human-like response, no long-winded way! and no more than 3 sentences! 
    
    This is the client Query: {issue} 
    If the query is related to the Bank, you need to know the following information to solve the client's query, this is the INFORMATION KNOWLEDGE: {knowledge} 
    ADDITIONAL INFORMATION that may complement: {adds_knowledge}

    If the issue is not related to bank, just answer that you not capable of answering the client's issue. Dont give a misleading information to the client

    ANSWER :
    """
)

runnable = LLMChain(llm=llm_base, prompt=prompt)
global_flag = False

def generate_initial_message(): 
    initial_prompt = "Welcome to CommonWealth Bank! How can I assist you today?"
    return initial_prompt

def generate_response_message(response):
    full_response = ""
    response_words = response.split()
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        for word in response_words:
            full_response += word + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    return full_response

st.title("Bank Customer Service Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": generate_initial_message()
        })

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
print(st.session_state.messages)


if user_input := st.chat_input("Enter your issue:"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    print(st.session_state.messages)
    print("__________________ Start of knowledge content __________________")
    knowledge_content, summary = get_knowledge(user_input, vectara_client) #-> get documents from vectara Corpus
    print(summary)
    # print(knowledge_content)
    response = runnable.invoke({"issue": user_input, "knowledge": summary, "adds_knowledge" : knowledge_content})

    full_response = generate_response_message(str(response['text']))
    print(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
