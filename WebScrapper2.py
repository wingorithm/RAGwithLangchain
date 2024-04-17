import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import create_extraction_chain
import pprint
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_community.llms import HuggingFaceEndpoint

HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Define the repository ID for the Gemma 2b model
repo_id = "mistralai/Mistral-7B-Instruct-v0.2"

# Set up a Hugging Face Endpoint for Gemma 2b model
llm = HuggingFaceEndpoint(
    repo_id=repo_id, max_length=250, temperature=0.5, max_new_tokens=250, huggingfacehub_api_token="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"
)

schema = {
    "properties": {
        "news_feature_title": {"type": "string"},
        "news_feature_detail": {"type": "string"},
    },
    "required": ["news_feature_title", "news_feature_detail"],
}

def extract(content: str, schema: dict):
    return create_extraction_chain(schema=schema, llm=llm).run(content)

def scrape_with_playwright(urls, schema):
    loader = AsyncChromiumLoader(urls)
    docs = loader.load()
    bs_transformer = BeautifulSoupTransformer()
    docs_transformed = bs_transformer.transform_documents(
        docs, tags_to_extract=["span"]
    )
    print("Extracting content with LLM")

    # Grab the first 1000 tokens of the site
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=0
    )
    splits = splitter.split_documents(docs_transformed)

    # Process the first split
    extracted_content = extract(schema=schema, content=splits[0].page_content)
    pprint.pprint(extracted_content)
    return extracted_content

urls = ["https://www.commbank.com.au/banking.html"]
extracted_content = scrape_with_playwright(urls, schema=schema)
print()