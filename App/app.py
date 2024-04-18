import os
import tempfile
import time
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(dirname(__file__)), '.env')
load_dotenv(dotenv_path)


import streamlit as st
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.vectorstores import Vectara
from langchain_community.llms import HuggingFaceEndpoint
from langchain_community.vectorstores.vectara import SummaryConfig
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA
from langchain.chains import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import ConversationChain

VECTARA_CUSTOMER_ID = os.getenv("VECTARA_CUSTOMER_ID")
VECTARA_CORPUS_ID = os.getenv("VECTARA_CORPUS_ID")
VECTARA_API_KEY = os.getenv("VECTARA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Define the repository ID for the Gemma 2b model
repo_id = "mistralai/Mistral-7B-Instruct-v0.2"

# Set up a Hugging Face Endpoint for Gemma 2b model
llm = HuggingFaceEndpoint(
    repo_id=repo_id, max_length=250, temperature=0.5, max_new_tokens=250, huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN
)

#Class for initialize prompt name using gpt 4 turbo
summary_config = SummaryConfig(True, prompt_name='vectara-experimental-summary-ext-2023-12-11-large', max_results=10)

def initialize_vectara():
    vectara = Vectara(
                    vectara_customer_id=VECTARA_CUSTOMER_ID,
                    vectara_corpus_id=VECTARA_CORPUS_ID,
                    vectara_api_key=VECTARA_API_KEY
                )
    return vectara

def get_knowledge_content(vectara, query, summary_config, threshold=0.7):
    #get the summary of knowledge
    found_docs = vectara.similarity_search_with_score(
        query,
        score_threshold=threshold,
        summary_config=summary_config,
        n_sentence_context=3
    )
    print("KNOWLEDGE:")
    print(found_docs[-1][0].page_content)
    return found_docs[-1][0].page_content
    # knowledge_content = ""
    # for number, (score, doc) in enumerate(found_docs):
    #     knowledge_content += f"Document {number}: {found_docs[number][0].page_content}\n"
    # return knowledge_content

vectara_client = initialize_vectara()

custom_prompt_template = """
    <s>[INST] You are a professional and friendly Bank Customer Service. Your task is provide conversational services to answer the customer question based on Commonwealth Bank knowledge, apart from that, answer wisely without hallucinations. When the customer asks about the flow, explain it step by step. Greet the customer when they greet you. When the customer requests an explanation, provide a concise response.
    Commonwealth Bank knowledge: {knowledge}.
    The question is as follows: Hello[/INST]
    Welcome to CommonWealth Bank! How can I assist you today?</s>
    {chat_history}
    [INST]
    {question}
    [/INST]
    """

#Define Prompt by initialize 3 different variable
prompt = PromptTemplate(input_variables=["knowledge", "question", "chat_history"], template=custom_prompt_template)
retriever = vectara_client.as_retriever() 

memory = ConversationBufferMemory(memory_key="chat_history", input_key="question", return_messages=True)

#Conversational Chain for maintaning chat_history to feed into another question
runnable = ConversationalRetrievalChain.from_llm(
    llm, retriever, chain_type="stuff", verbose=False, memory = memory, combine_docs_chain_kwargs={"prompt": prompt, "document_variable_name":"knowledge"}
)

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

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

initial_message = generate_response_message(generate_initial_message()) 
st.session_state.messages.append({
    "role": "assistant",
    "content": initial_message
})

if user_input := st.chat_input("Enter your issue:"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    #1st preprocessing step
    # negative_words = ["no", "No.", "no.", "NO!", "NO", "no!"] 
    # Classification = runnable.invoke({"issue": user_input})
    # classification = Classification.lower()
    # print("Cjeck => " + Classification)
    
    #2nd preprocessing step
    print("__________________ Start of knowledge content __________________")
    response = runnable.invoke({"question": user_input})
    print(response)
    # response = runnable.invoke({"issue": user_input, "knowledge": summary, "adds_knowledge" : knowledge_content})
    # if Classification.startswith("no"):
    #     print("Other Information")
    #     runnable1 = prompt2 | llm_base | StrOutputParser()
    #     response = runnable1.invoke({"issue": user_input})
    # else:
    #     print("Bank Related Information")
    
    full_response = generate_response_message(response['answer'])
    st.session_state.messages.append({"role": "assistant", "content": full_response})