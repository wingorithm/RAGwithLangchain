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

summary_config = SummaryConfig(True, prompt_name='vectara-experimental-summary-ext-2023-12-11-large', max_results=10)

def initialize_vectara():
    vectara = Vectara(
                    vectara_customer_id=VECTARA_CUSTOMER_ID,
                    vectara_corpus_id=VECTARA_CORPUS_ID,
                    vectara_api_key=VECTARA_API_KEY
                )
    return vectara

def get_knowledge_content(vectara, query, summary_config, threshold=0.7):
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

prompt = PromptTemplate.from_template(
    """
    <s>[INST] You are a professional and friendly Bank Customer Service. Your task is provide conversational services to answer the customer question based on Commonwealth Bank knowledge, apart from that, answer wisely without hallucinations. When the customer asks about the flow, explain it step by step. Greet the customer when they greet you. When the customer requests an explanation, provide a concise response.
    Commonwealth Bank knowledge: {knowledge}. 
    The question is as follows: Hello[/INST]
    Welcome to CommonWealth Bank! How can I assist you today?</s>
    [INST]
    {question}
    [/INST]
    """
)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# retriever = vectara_client.as_retriever(search_type="similarity_score_threshold", search_kwargs={'score_threshold': 0.6})

runnable = ConversationalRetrievalChain.from_llm(
    llm, vectara_client, memory=memory, verbose=False, combine_docs_chain_kwargs={"prompt": prompt}
)
# runnable = prompt | llm | StrOutputParser()

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
    
    knowledge_content = get_knowledge_content(vectara_client, user_input, summary_config)
    print("__________________ Start of knowledge content __________________")
    # print(knowledge_content)
    response = runnable.invoke({"knowledge": knowledge_content, "question": user_input})
    print("RESPONSE:")
    print(response)
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