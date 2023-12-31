import json
from math import floor
import os 

from dotenv import load_dotenv
import openai
from openai.embeddings_utils import get_embedding
import pandas as pd
import tiktoken

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# embedding model parameters
embedding_model = "text-embedding-ada-002"
embedding_encoding = "cl100k_base"  # this the encoding for text-embedding-ada-002
max_tokens = 8000  # the maximum for text-embedding-ada-002 is 8191
encoding = tiktoken.get_encoding(embedding_encoding)

def embed_job_from_dict(job_dict):
    full_info_token_length = len(encoding.encode(job_dict['info']))
    full_info_cost = _cost_from_num_tokens(full_info_token_length)
    if job_dict['info'] and full_info_token_length <= max_tokens:
        return get_embedding(job_dict['info'], engine=embedding_model), full_info_cost
    elif full_info_token_length > max_tokens:
        three_fourths = job_dict['info'][:floor(len(job_dict['info']) * 3 / 4)]
        three_fourths_token_length = len(encoding.encode(three_fourths))
        three_fourths_cost = _cost_from_num_tokens(three_fourths_token_length)
        if three_fourths_token_length <= max_tokens:
            return get_embedding(three_fourths, engine=embedding_model), three_fourths_cost

    return None

def _cost_from_num_tokens(n):
    # $0.0001 per 1000 tokens
    return n / 1000 * 0.0001