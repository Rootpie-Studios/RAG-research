import sys
import os
# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openai import OpenAI
from config import LOCAL_BASE_URL#, get_client

def generate_partial_context(question, relevant_chunks, sys_prompt):
    context = "\n\n".join(relevant_chunks)
    # context = normalize_spaces(context)
    # client = get_client()
    client = OpenAI(base_url=LOCAL_BASE_URL, api_key="not-needed")
    response = client.chat.completions.create(
        model="gpt-4.1-nano",  # Add proper model name if not using local model, 'gpt-4.1-nano' for example
        messages=[
            {
                "role": "system",
                "content": sys_prompt,
            },
            {
                "role": "user",
                "content": "\originaldokumentet:\n" + context + "\ntextutdrag:\n" + question,
            },
        ],
    )

    answer = response.choices[0].message.content
    return answer

def generate_response_from_context(question, relevant_chunks, sys_prompt):
    context = "\n\n".join(relevant_chunks)
    # context = normalize_spaces(context)
    prompt = (
        sys_prompt + "\nKontext:\n" + context
    )
    # client = get_client()
    client = OpenAI(base_url=LOCAL_BASE_URL, api_key="not-needed")
    response = client.chat.completions.create(
        model="local",  # Add proper model name if not using local model, 'gpt-4.1-nano' for example
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    answer = response.choices[0].message.content
    return answer