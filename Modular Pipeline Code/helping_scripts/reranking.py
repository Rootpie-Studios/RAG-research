import requests
import cohere
# import torch
from transformers import AutoModelForSequenceClassification
from config import COHERE_KEY, JINA_KEY


# COHERE RERANK
cohere_client = cohere.ClientV2(api_key=COHERE_KEY)

def rerank_cohere(query_for_rerank, docs_to_rerank, n_results):
    response = cohere_client.rerank(
        model="rerank-v3.5",
        query=query_for_rerank,
        documents=docs_to_rerank,
        top_n=n_results,
    )
    reranked_results = [docs_to_rerank[x.index] for x in response.results]
    return reranked_results


# JINA API RERANK

def rerank_jina_api(query_for_rerank, docs_to_rerank, n_results):
    url = "https://api.jina.ai/v1/rerank"
    headers = {
        "Content-Type": "application/json",
        "Authorization": JINA_KEY,
    }
    data = {
        "model": "jina-reranker-v2-base-multilingual",
        "query": query_for_rerank,
        "top_n": n_results,
        "documents": docs_to_rerank,
        "return_documents": False,
    }
    response = requests.post(url, headers=headers, json=data)
    rank_data = response.json()["results"]
    reranked_results = [docs_to_rerank[result["index"]] for result in rank_data]
    return reranked_results


# LOCAL JINA MODEL RERANK

def rerank_jina_local(query_for_rerank, docs_to_rerank, n_results):
    model = AutoModelForSequenceClassification.from_pretrained(
        "jinaai/jina-reranker-v2-base-multilingual",
        torch_dtype="auto",
        use_flash_attn=False,
        trust_remote_code=True,
    )
    model.to("cpu")  # or 'cpu' if no GPU is available
    model.eval()
    reranked_results = model.rerank(
        query_for_rerank,
        docs_to_rerank,
        max_query_length=512,
        max_length=2048,
        top_n=n_results,
    )
    only_docs = [d.get("document") for d in reranked_results]
    # print(only_docs)
    return only_docs
