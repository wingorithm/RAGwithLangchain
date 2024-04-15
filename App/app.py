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
    
# # Sidebar for txt upload and API keys
# with st.sidebar:
#     st.header("Configuration")
#     uploaded_file = st.file_uploader("Choose a TXT file", type=["txt"])
#     submit_button = st.button("Submit")

vectara_client = initialize_vectara()

prompt = PromptTemplate.from_template(
  """You are a professional and friendly Bank Customer Service and you are helping a client with bank knowledge. If a client is asking about general question, answer it with human-like response. When a client asking an issue related to banks Just explain it in detail. This is the issue: {issue} 
    If the issue is related to the Bank, you need to know the following information will help solve the client's issue, this is the information: {knowledge} 

    If the issue is not related to bank, just answer that you not capable of answering the client's issue. Dont give a misleading information to the client

    ANSWER :
    """
)
hf = initialize_hf()

runnable = LLMChain(prompt=prompt, llm=hf)

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
    map_chain = LLMChain(llm=hf, prompt=map_prompt)
    summarize = map_chain.invoke({"docs":knowledge_content})
    print("__________________ Start of knowledge content __________________")
    print(knowledge_content)
    response = runnable.invoke({"knowledge": knowledge_content, "issue": user_input})

    response_words = response['text']
    answer_part = response_words.split("ANSWER :", 1)[1]

    # Optional: Remove any leading or trailing whitespace
    answer_part = answer_part.strip()
    answer = answer_part.split()

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for word in answer:
            full_response += word + " "
            time.sleep(0.01)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# # Run when the submit button is pressed
# if submit_button and uploaded_file:
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmpfile:
#         tmpfile.write(uploaded_file.getvalue())
#         tmp_filename = tmpfile.name

#     try:
#         vectara_client.add_files([tmp_filename])
#         st.sidebar.success("txt file successfully uploaded to Vectara!")
#     except Exception as e:
#         st.sidebar.error(f"An error occurred: {str(e)}")
#     finally:
#         os.remove(tmp_filename)

# def main(): 
#     start_dependencies()    
#     openai_api_key = os.getenv("OPENAI_API_KEY")
#     llm = OpenAI(api_key=openai_api_key)
#     retriever = vectara.as_retriever()
    
#     bot = ConversationalRetrievalChain.from_llm(
#         llm, retriever, memory=memory, verbose=False
#     )

#     query = "is there a minimum deposit?"
#     result = bot.invoke({"question": query})

#     print(result["answer"])
  
# if __name__=="__main__": 
#     main() 