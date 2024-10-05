from openai import OpenAI
import numpy as np, os, pinecone, pandas as pd, time,asyncio
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import logging

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)


load_dotenv()
client = OpenAI()
# Initialize Pinecone
pinecone_api_key = os.getenv('PINECONE_API_KEY')
cloud = os.environ.get('PINECONE_CLOUD') or 'aws'
region = os.environ.get('PINECONE_REGION') or 'us-east-1'
spec = ServerlessSpec(cloud=cloud, region=region)
index_name = 'tiktok-data'
pc = Pinecone(api_key=pinecone_api_key )
existing_indexes = [
    index_info["name"] for index_info in pc.list_indexes()
]

# check if index already exists (it shouldn't if this is first time)
if index_name not in existing_indexes:
    # if does not exist, create index
    pc.create_index(
        index_name,
        dimension=1536,  # dimensionality of minilm
        metric='dotproduct',
        spec=spec
    )
    # wait for index to be initialized
    while not pc.describe_index(index_name).status['ready']:
        time.sleep(1)
index = pc.Index(index_name)

def create_chunks_from_df(df):
    # Ensure IDs are strings
    #logger.debug()
    df['post_id'] = df['post_id'].astype(str)
    df['comment_id'] = df['comment_id'].astype(str)
    
    chunks = []
    
    # Process posts
    posts_df = df[['post_id', 'post_description', 'post_likes']].drop_duplicates('post_id')
    for _, row in posts_df.iterrows():
        chunks.append({
            'chunk_id': row['post_id'],
            'parent_id': None,
            'level': 'post',
            'text': row['post_description'],
            'likes': row['post_likes'],
            'indices': {
                'post_id': row['post_id']
            }
        })
    
    # Process comments
    comments_df = df[['post_id', 'comment_id', 'comments', 'comment_likes']].drop_duplicates('comment_id')
    for _, row in comments_df.iterrows():
        chunks.append({
            'chunk_id': f"{row['post_id']}_{row['comment_id']}",
            'parent_id': row['post_id'],
            'level': 'comment',
            'text': str(row['comments']),
            'likes': row['comment_likes'],
            'indices': {
                'post_id': row['post_id'],
                'comment_id': row['comment_id']
            }
        })
    
    # Process replies
    replies_df = df[['post_id', 'comment_id', 'replies', 'reply_likes']].dropna(subset=['replies'])
    replies_df = replies_df.drop_duplicates(['comment_id', 'replies'])
    for idx, row in replies_df.iterrows():
        reply_id = f"reply_{idx}"
        chunks.append({
            'chunk_id': f"{row['post_id']}_{row['comment_id']}_{reply_id}",
            'parent_id': f"{row['post_id']}_{row['comment_id']}",
            'level': 'reply',
            'text': str(row['replies']),
            'likes': row['reply_likes'],
            'indices': {
                'post_id': row['post_id'],
                'comment_id': row['comment_id'],
                'reply_id': reply_id
            }
        })
    
    chunks_df = pd.DataFrame(chunks)

    chunks_df = chunks_df[chunks_df['text'].notna() & (chunks_df['text'] != '')]
    #chunks_df.to_csv("results.csv")
    
    return chunks_df




def get_embeddings(texts, model = "text-embedding-3-small",  batch_size = 100):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        max_retries = 5
        for retry in range(max_retries):
            try:
                response = client.embeddings.create(input=batch_texts, model=model)
                #breakpoint()
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                break
            except Exception as e:
                if retry < max_retries - 1:
                    time.sleep(2 ** retry)
                else:
                    print(f"Error generating embeddings for batch starting at index {i}: {e}")
                    raise e
    return embeddings


async def upsert_embeddings_to_pinecone(chunks_df,batch_size = 300):
    # Generate embeddings
    texts = [str(text) for text in chunks_df['text'].tolist() if str(text).strip()]
    embeddings = get_embeddings(texts)
    chunks_df['embedding'] = embeddings

    # Prepare data for upsert
    vectors = []
    metadata_cols = ['chunk_id', 'parent_id', 'level', 'likes', 'text']
    chunks_df['parent_id'] = chunks_df['parent_id'].fillna('')
    chunks_df['likes'] = chunks_df['likes'].fillna(0)
    chunks_df['text'] = chunks_df['text'].fillna('')

    # Convert DataFrame to list of records
    records = chunks_df.to_dict('records')

    # Create the list of vectors
    vectors = [
        {
            "id": record['chunk_id'],
            "values": record['embedding'],
            "metadata": {
                'chunk_id': record['chunk_id'],
                'parent_id': record['parent_id'],
                'level': record['level'],
                'likes': record['likes'],
                'text': record['text']
            }
        }
        for record in records
    ]

    # Upsert to Pinecone in batches
    
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)





async def query_pinecone_async(vector, top_k=10):
    executor = ThreadPoolExecutor(max_workers=5)
    loop = asyncio.get_event_loop()
    func = partial(index.query, vector=vector, top_k=top_k, includeMetadata = True)
    response = await loop.run_in_executor(executor, func)
    return response

async def query_pinecone(query_text, top_k=10):
    # Get embedding for the query text
    query_embedding = get_embeddings(query_text)
    # Query Pinecone
    tasks = [query_pinecone_async(query,top_k) for query in query_embedding]
    responses = await asyncio.gather(*tasks)
    
    return responses

def rerank_results(results, likes_weight=0.5, similarity_weights=0.5):
    # Convert results to DataFrame
    data = []
    for match in results['matches']:
        metadata = match['metadata']
        score = match['score']
        data.append({
            'chunk_id': metadata['chunk_id'],
            'text': metadata['text'],
            'level': metadata['level'],
            'likes': metadata['likes'],
            'score': score,
            'parent_id': metadata['parent_id']
        })
    results_df = pd.DataFrame(data)
    
    # Rerank based on combined score (you can adjust weights as needed)
    
    results_df['normalized_likes'] = (results_df['likes'] - results_df['likes'].min()) / (results_df['likes'].max() - results_df['likes'].min())
    results_df['combined_score'] = likes_weight * results_df['normalized_likes'] + results_df['score'] * similarity_weights
    
    return results_df

def reconstruct_context(row, chunks_df):
    context_pieces = []
    current_row = row.copy()  # Create a copy to avoid modifying the original row
    visited_ids = set()
    
    accumulated_score = current_row['combined_score']
    
    while True:
        context_pieces.insert(0, current_row['text'])
        parent_id = current_row.get('parent_id')
        
        # Check for termination conditions
        if not parent_id or parent_id == current_row['chunk_id'] or parent_id in visited_ids:
            break
        
        # Find the parent row
        parent_rows = chunks_df[chunks_df['chunk_id'] == parent_id]
        if parent_rows.empty:
            #print(f"Warning: Parent chunk with ID {parent_id} not found for chunk {current_row['chunk_id']}")
            break
        
        current_row = parent_rows.iloc[0]
        visited_ids.add(parent_id)
        # Accumulate the score
        accumulated_score += current_row['normalized_likes']
    
    full_context = '\n'.join(context_pieces)
    return full_context, accumulated_score

def get_full_contexts(results_df, chunks_df):
    # Apply the reconstruction and get both context and accumulated score
    results = results_df.apply(lambda row: reconstruct_context(row, chunks_df), axis=1)
    
    # Unpack the results
    results_df['full_context'], results_df['accumulated_score'] = zip(*results)

    return results_df




