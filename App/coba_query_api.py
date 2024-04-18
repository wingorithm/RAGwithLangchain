import requests
import json

url = "https://api.vectara.io/v1/query"

payload = json.dumps({
  "query": [
    {
      "query": "How to car loans?",
      "start": 0,
      "numResults": 10,
      "contextConfig": {
        "sentences_before": 3,
        "sentences_after": 3,
        "start_tag": "<b>",
        "end_tag": "</b>"
      },
      "corpusKey": [
        {
          "corpus_id": 3
        }
      ],
      "summary": [
        {
          "max_summarized_results": 10,
          "response_lang": "en",
          "summarizerPromptName":"vectara-experimental-summary-ext-2023-12-11-large",
          "promptText":"""[
            {"role": "system", "content": "You are a professional and friendly Bank Customer Service. Your task is provide conversational services to answer the customer question based on Commonwealth Bank knowledge, apart from that, answer wisely without hallucinations. When the customer asks about the flow, explain it step by step. Greet the customer when they greet you. When the customer requests an explanation, provide a concise response."},
            #foreach ($qResult in $vectaraQueryResults)
              {"role": "user", "content": "Give me the $vectaraIdxWord[$foreach.index] search result."},
              {"role": "assistant", "content": "${qResult.getText()}" },
            #end
            {"role": "user", "content": "Generate a summary for the query '${vectaraQuery}' based on the above results. You must only use information from the provided."}
          ]"""
        }
      ]
    }
  ]
})
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'x-api-key': 'zwt_g_5hai2h6tiMYpQcRbwz081eidP-rWXpufLIfA',
  'customer-id': '2214486378'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)