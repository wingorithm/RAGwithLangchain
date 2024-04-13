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
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.vectorstores import Vectara
from openai import OpenAI

VECTARA_CUSTOMER_ID = os.getenv("VECTARA_CUSTOMER_ID")
VECTARA_CORPUS_ID = os.getenv("VECTARA_CORPUS_ID")
VECTARA_API_KEY = os.getenv("VECTARA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# def langchain_func(file):
#     loader = TextLoader(file, encoding='UTF-8')
#     documents = loader.load()
#     global vectara
#     vectara = Vectara.from_documents(documents, embedding=None)

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
    knowledge_content = ""
    for number, (score, doc) in enumerate(found_docs):
        knowledge_content += f"Document {number}: {found_docs[number][0].page_content}\n"
    return knowledge_content
    
# # Sidebar for txt upload and API keys
# with st.sidebar:
#     st.header("Configuration")
#     uploaded_file = st.file_uploader("Choose a TXT file", type=["txt"])
#     submit_button = st.button("Submit")

vectara_client = initialize_vectara()

prompt = PromptTemplate.from_template(
    """You are a professional and friendly Bank Customer Service and you are helping a client with bank knowledge. Just explain him in detail the answer and nothing else. This is the issue: {issue} 
    To assist him with his issue, you need to know the following information: {knowledge} 
    """
)

runnable = prompt | ChatOpenAI(streaming=True, callbacks=[StreamingStdOutCallbackHandler()], openai_api_key=OPENAI_API_KEY) | StrOutputParser()

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
    print("__________________ Start of knowledge content __________________")
    print(knowledge_content)
    response = runnable.invoke({"knowledge": knowledge_content, "issue": user_input})

    response_words = response.split()
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for word in response_words:
            full_response += word + " "
            time.sleep(0.05)
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