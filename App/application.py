import os
import tempfile
import time
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(dirname(__file__)), '.env')
load_dotenv(dotenv_path)


import streamlit as st
from dotenv import load_dotenv
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import LLMChain
from langchain_community.llms import HuggingFaceHub
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.vectorstores import Vectara
from langchain import hub
from langchain_community.chat_models import ChatOpenAI
# from openai import OpenAI

VECTARA_CUSTOMER_ID = os.getenv("VECTARA_CUSTOMER_ID")
VECTARA_CORPUS_ID = os.getenv("VECTARA_CORPUS_ID")
VECTARA_API_KEY = os.getenv("VECTARA_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN_CALVIN")
REPO_ID = os.getenv("REPO_ID")

def initialize_hf():
    hf = HuggingFaceHub(
    huggingfacehub_api_token = HF_TOKEN,
    repo_id=REPO_ID,
    task="text-generation",
    model_kwargs={
        "max_new_tokens": 500,
        "top_k": 30,
        "max_length": 400,
        "temperature": 0.1,
        "repetition_penalty": 1.03,
    })
    return hf

def initialize_vectara():
    vectara = Vectara(
                    vectara_customer_id=VECTARA_CUSTOMER_ID,
                    vectara_corpus_id=VECTARA_CORPUS_ID,
                    vectara_api_key=VECTARA_API_KEY
                )
    return vectara

def get_knowledge_content(vectara, query, threshold=0.5):
    found_docs = vectara.similarity_search_with_score(
        query,
        score_threshold=threshold,
    )
    return found_docs

vectara_client = initialize_vectara()
history_chat = []

def get_history():
    history = ""
    for hist in history_chat:
        history = history + "\n" + hist

    return history

prompt = PromptTemplate.from_template(
    """<s>[INST] You are a professional and friendly Bank Customer Service. Your task is to help a customer with a valid answer based on Commonwealth Bank knowledge. When a client ask related to banks, explain it briefly. 
    
    If a client doing small talk to you, answer it with human-like response so client will feel the human interaction.
    
    If the issue is not related to bank, just answer that you not capable of answering the client's issue. Dont give a misleading information to the client. 

    This is some knowledge that could help the client : {knowledge}. 

    The question is as follows: Hello[/INST]
    Welcome to CommonWealth Bank! How can I assist you today?</s>

    [INST]
    Question: {question}
    [/INST]
    """
)
hf = initialize_hf()

runnable = prompt=prompt | hf | StrOutputParser()

# Main Streamlit App
st.title("Bank Customer Service Chat")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Enter your issue:"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    knowledge_content = get_knowledge_content(vectara_client, user_input)
    map_prompt = hub.pull("rlm/map-prompt")
    map_chain =  map_prompt | hf | StrOutputParser()
    summarize = map_chain.invoke({"docs":knowledge_content})
    print("__________________ Start of knowledge content __________________")
    print(knowledge_content)

    response = runnable.invoke({"knowledge": knowledge_content, "history": get_history,"question": user_input})
   
    answer = response.split()
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for word in answer:
            full_response += word + " "
            time.sleep(0.01)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
