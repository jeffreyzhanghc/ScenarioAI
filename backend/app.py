from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from utils.db import get_data
from utils.chat import get_response_from_llm
from utils.utils import preprocess_tiktok_data, analyze_hashtags, extract_json_from_text
from rag.chunk import create_chunks_from_df, upsert_embeddings_to_pinecone, query_pinecone, rerank_results, get_full_contexts
from utils.prompts import PROMPT, SUMMARY_GUIDE
import openai
import json
import asyncio
import os
import re
import ast
from dotenv import load_dotenv
import numpy as np
import pandas as pd

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class GenerateRequest(BaseModel):
    keyword: str
    hashtags: Optional[List[str]] = []

class Scenario(BaseModel):
    scenario: str
    reason: str
    hashtags: List[str]
    content_guidance: dict

class GenerateResponse(BaseModel):
    scenarios: List[Scenario]

async def query_rephrase(
    query: str,
    model: str,
    client: openai.OpenAI,
    msg_history: List = []
) -> Optional[List[str]]:
    try:
        prompt = SUMMARY_GUIDE.format(query=query)
        text, msg_history = get_response_from_llm(
            msg=prompt,
            client=client,
            model=model,
            msg_history=msg_history,
            system_message="You are a helpful and smart assistant"
        )
        
        query_content_match = re.search(r'<query>\s*(.*?)\s*</query>', text, re.DOTALL)
        if not query_content_match:
            raise ValueError("No content found within <query> tags.")
        
        query_content = query_content_match.group(1)
        list_match = re.search(r'\[.*\]', query_content, re.DOTALL)
        if not list_match:
            raise ValueError("No list found within the <query> content.")
        
        list_str = list_match.group(0)
        revised_query_list = ast.literal_eval(list_str)
        return revised_query_list
    except Exception as e:
        print(f"Failed to generate: {e}")
        return None

async def generate_scenarios(
    save_dir: str,
    reviews: pd.DataFrame,
    keyword: str,
    client: openai.OpenAI,
    model: str,
    assess: bool = False,
    results: Optional[dict] = None,
    msg_history: List = []
) -> Optional[str]:
    try:
        if not assess:
            prompt = PROMPT.format(
                keyword=keyword,
                reviews=reviews
            )
        text, msg_history = get_response_from_llm(
            prompt,
            client=client,
            model=model,
            msg_history=msg_history,
            system_message="You are a helpful and smart assistant"
        )
        return text
    except Exception as e:
        print(f"Failed to generate: {e}")
        return None

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    print(request)
    client_model = "gpt-4o-2024-05-13"
    client = openai.OpenAI()
    
    # Step 0: Get data from postgres
    raw_data = await get_data(request.hashtags)

    # Step 1: Create chunks
    chunks_df = create_chunks_from_df(raw_data)
    #chunks_df = pd.read_csv("results.csv")
    chunks_df['normalized_likes'] = (chunks_df['likes'] - chunks_df['likes'].min()) / (chunks_df['likes'].max() - chunks_df['likes'].min())

    # Step 2: Upsert embeddings to Pinecone
    await upsert_embeddings_to_pinecone(chunks_df)
    
    # Step 3: Query Pinecone with input query
    query_text = await query_rephrase(request.keyword, client_model, client)
    if not query_text:
        raise HTTPException(status_code=500, detail="Failed to rephrase query")
    
    results = await query_pinecone(query_text, top_k=400)
    
    # Step 4: Rerank results and reconstruct full contexts
    merged_df = pd.DataFrame()
    for res in results:
        results_df = rerank_results(res)
        results_df = get_full_contexts(results_df, chunks_df)
        merged_df = pd.concat([merged_df, results_df])
    
    merged_df = merged_df.drop_duplicates(subset=['chunk_id'], keep='first')
    merged_df = merged_df.sort_values(by='combined_score', ascending=False)
    merged_df.to_csv('merge.csv')
    
    # Step 5: Generate scenarios
    results = await generate_scenarios("./", merged_df['full_context'], request.keyword, client, client_model)
    if results is None:
        raise HTTPException(status_code=500, detail="Failed to generate scenarios")
    
    #breakpoint()

    scenarios = extract_json_from_text(results)
    if scenarios is None:
        raise HTTPException(status_code=500, detail="Failed to extract scenarios from generated text")
    

    return GenerateResponse(scenarios=scenarios)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug = True)