from utils.db import get_data
from utils.chat import get_response_from_llm
from utils.utils import preprocess_tiktok_data, analyze_hashtags, extract_json_from_text
from rag.chunk import create_chunks_from_df, upsert_embeddings_to_pinecone, query_pinecone, rerank_results, get_full_contexts
from utils.prompts import PROMPT,SUMMARY_GUIDE
import openai, json, asyncio, os, re, ast
import os.path as osp
from dotenv import load_dotenv
import numpy as np, pandas as pd
load_dotenv()



def query_rephrase(
    query: str,
    model,
    client,
    msg_history = []
):
    try:
        prompt = SUMMARY_GUIDE.format(query=query)
        text, msg_history = get_response_from_llm(
            msg = prompt,
            client=client,
            model=model,
            msg_history=msg_history,
            system_message= "You are a helpful and smart assistant"
        )
        
        # Step 1: Extract the content within the <query> tags
        query_content_match = re.search(r'<query>\s*(.*?)\s*</query>', text, re.DOTALL)
        if query_content_match:
            query_content = query_content_match.group(1)
        else:
            raise ValueError("No content found within <query> tags.")

        # Step 2: Identify and extract the list from the extracted content
        list_match = re.search(r'\[.*\]', query_content, re.DOTALL)
        if list_match:
            list_str = list_match.group(0)
        else:
            raise ValueError("No list found within the <query> content.")

        # Step 3: Convert the string representation of the list into an actual Python list
        try:
            revised_query_list = ast.literal_eval(list_str)
        except Exception as e:
            raise ValueError(f"Error parsing list: {e}")

        return revised_query_list
    except Exception as e:
        print(f"Failed to generate: {e}")
        return None  # Return None instead of not returning anything


        
def generate_scenarios(
    save_dir,
    reviews,
    keyword,
    client,
    model,
    assess = False,
    results = None,
    msg_history = []
):
    try:
        if assess:
            pass
        else:
            prompt = PROMPT.format(
                keyword = keyword,
                reviews = reviews
            )
        text, msg_history = get_response_from_llm(
            prompt,
            client=client,
            model=model,
            msg_history=msg_history,
            system_message= "You are a helpful and smart assistant"
        )
        return text
    except Exception as e:
        print(f"Failed to generate: {e}")
        return None  # Return None instead of not returning anything


def generate():
    client_model = "gpt-4o-2024-05-13"
    client = openai.OpenAI()
    keyword = "tote bag"
    input_hashtags  = [
    "#FashionBags", "#Bags", "#Backpack", "#Handbag", "#ToteBag", 
    "#ShoulderBag", "#CanvasBag","quality bags", "latest bag trends", "handbag", "tote bag"]

    # Step 0: Get data from postgres
    raw_data = asyncio.run(get_data(input_hashtags))

    #Step 1: Create chunks
    chunks_df = create_chunks_from_df(raw_data)
    chunks_df = pd.read_csv("results.csv")
    #add normalized likes for final accumulated score calculation
    chunks_df['normalized_likes'] = (chunks_df['likes'] - chunks_df['likes'].min()) / (chunks_df['likes'].max() - chunks_df['likes'].min())

    # Step 2: Upsert embeddings to Pinecone
    upsert_embeddings_to_pinecone(chunks_df)
    
    # Step 3: Query Pinecone with input query
    #query_summary phase **
    query_text = query_rephrase(keyword,client_model,client)
    print(query_text)
    results = asyncio.run(query_pinecone(query_text, top_k=400))
    
    # Step 4: Rerank results
    merged_df = pd.DataFrame()
    for res in results:
        results_df = rerank_results(res)
        # Step 5: Reconstruct full contexts
        results_df = get_full_contexts(results_df, chunks_df)
        merged_df = pd.concat([merged_df, results_df])
    merged_df = merged_df.drop_duplicates(subset=['chunk_id'], keep='first')
    merged_df = merged_df.sort_values(by='combined_score', ascending=False)
    merged_df.to_csv('merge.csv')
    
    results = generate_scenarios("./", merged_df['full_context'], keyword, client, client_model)
    print(results)
    
    scenarios = extract_json_from_text(results)
    response = {
        'scenarios': scenarios
    } 
    return response

if __name__ == "__main__":
    response = generate()
    print(response)
