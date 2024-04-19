import argparse
import json
import logging
import sys
import requests
import os

from langchain.vectorstores import Vectara
from langchain_community.vectorstores.vectara import SummaryConfig, MMRConfig, VectaraQueryConfig

VECTARA_CUSTOMER_ID = os.getenv("VECTARA_CUSTOMER_ID")
VECTARA_CORPUS_ID = os.getenv("VECTARA_CORPUS_ID")
VECTARA_API_KEY = os.getenv("VECTARA_API_KEY")

#Init Vectara Connection
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
        score_threshold=threshold
    )
    knowledge_content = ""
    for number, (score, doc) in enumerate(found_docs):
        knowledge_content += f"Document {number}: {found_docs[number][0].page_content}\n"
    return found_docs


#retrieve context from VECTARA corpus
def get_knowledge(user_query, vectorstore):
    
    query_config = VectaraQueryConfig(
        k=7,
        # lambda_val=0.5,  
        # filter="doc.category='news' and doc.lang='en'",
        score_threshold=0.7,
        n_sentence_context=2,
        # mmr_config=MMRConfig(diversity_bias=0.8),
        summary_config=SummaryConfig(is_enabled=True),
    )

    '''LangChain version OF QUERY'''
    response = vectorstore.vectara_query(
        user_query, 
        config = query_config
    )

    '''Native version OF QUERY'''
    # response = query(VECTARA_CUSTOMER_ID, 
    #         VECTARA_CORPUS_ID,
    #         "api.vectara.io", 
    #         VECTARA_API_KEY,
    #         user_query
    #         )

    knowledge_content = ""
    summary_content = ""
    for number, (score, doc) in enumerate(response):
        if response[number][0].metadata.get('summary'):
            summary_content += f"{response[number][0].page_content}\n"
        else:
            knowledge_content += f"{response[number][0].page_content}\n"

    # response_set = response[0]["responseSet"][0]
    # knowledge_content += f"{response_set['summary'][0]['text']}\n"
    # knowledge_content += f"{response_set['summary'][0]['text']}\n\nOTHER INFORMATION:\n"
    # for i in range(7):
    #     knowledge_content += f"{response_set['response'][i]['text']}\n"

    return knowledge_content, summary_content

#upload file to corpus
def upload_all_file(path, vectara_client):
    files = os.listdir(path)

    for file in files:
        full_path = os.path.join(path, file)
        vectara_client.add_files([fr"{full_path}"])

def _get_query_json(customer_id: int, corpus_id: int, query_value: str):
    """Returns a query JSON."""
    query = {            
        "query": [
            {
            "query": query_value,
            "start": 0,
            "numResults": 7,
            "contextConfig": {
                "sentences_before": 5,
                "sentences_after": 5,
                "start_tag": "<b>",
                "end_tag": "</b>"
            },
            "corpusKey": [
                {
                    "customer_id": customer_id, 
                    "corpus_id": corpus_id,
                    "semantics": 0,
                    "metadataFilter": "",
                    "lexicalInterpolationConfig": {
                        "lambda": 0.025
                    },
                }
            ],
            "summary": [
                {
                    "summarizerPromptName": "vectara-summary-ext-v1.2.0",
                    "responseLang": "en",
                    "maxSummarizedResults": 5
                }
            ],
            }
        ]
        
    }
    
    return json.dumps(query)


def query(customer_id: int, corpus_id: int, query_address: str, api_key: str, query: str):
    """Queries the data.

    Args:
        customer_id: Unique customer ID in vectara platform.
        corpus_id: ID of the corpus to which data needs to be indexed.
        query_address: Address of the querying server. e.g., api.vectara.io
        api_key: A valid API key with query access on the corpus.

    Returns:
        (response, True) in case of success and returns (error, False) in case of failure.
    """
    post_headers = {
        "customer-id": f"{customer_id}",
        "x-api-key": api_key
    }

    response = requests.post(
        f"https://{query_address}/v1/query",
        data=_get_query_json(customer_id, corpus_id, query),
        verify=True,
        headers=post_headers)

    if response.status_code != 200:
        logging.error("Query failed with code %d, reason %s, text %s",
                       response.status_code,
                       response.reason,
                       response.text)
        return response, False

    message = response.json()
    if (message["status"] and
        any(status["code"] != "OK" for status in message["status"])):
        logging.error("Query failed with status: %s", message["status"])
        return message["status"], False

    for response_set in message["responseSet"]:
        for status in response_set["status"]:
            if status["code"] != "OK":
                return status, False

    return message, True


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser(
                description="Vectara rest example (With API Key authentication.")

    parser.add_argument("--customer-id", type=int, help="Unique customer ID in Vectara platform.")
    parser.add_argument("--corpus-id",
                        type=int,
                        help="Corpus ID to which data will be indexed and queried from.")

    parser.add_argument("--serving-endpoint", help="The endpoint of querying server.",
                        default="api.vectara.io")
    parser.add_argument("--api-key", help="API key retrieved from Vectara console.")
    parser.add_argument("--query", help="Query to run against the corpus.", default="Test query")

    args = parser.parse_args()

    if args:
        response, status = query(args.customer_id,
                                 args.corpus_id,
                                 args.serving_endpoint,
                                 args.api_key,
                                 args.query)
        logging.info("Query response: %s", response)
        if not status:
            sys.exit(1)