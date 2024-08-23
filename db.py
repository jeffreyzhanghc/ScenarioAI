import psycopg2, asyncpg, asyncio, os, pandas as pd
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()


host = os.getenv('host')
pw = os.getenv('password')
async def get_comments(words: list):
    pool = await asyncpg.create_pool(
    host=host,
    port="5432",
    database="scenario",
    user="contractor",
    password= pw
)
    sql_value = "(" + ", ".join(map(repr, words)) + ")"
    try:
        async with pool.acquire() as connection:
            # First Query: Get aweme_id values

                query = f'''SELECT p.aweme_id AS post_id, p.description AS post_description, c.cid AS comment_id, c.text AS comments, r.text AS replies
                            FROM tiktok_posts p
                            JOIN tiktok_comments c ON p.aweme_id = c.aweme_id
                            LEFT JOIN tiktok_comments_replies r ON c.cid = r.reply_id
                            WHERE p.hashtag_keyword in {sql_value};'''
                #print(query)
                results = await connection.fetch(query)
                data = [dict(record) for record in results]
                return data
        
    except Exception as e:
        print(f"Error during connection: {e}")
        return []

    finally:
        # Properly close the connection pool
        await pool.close()

def transform_tiktok_data(query_results):
    organized_data = defaultdict(lambda: {
        'description': '',
        'comments': defaultdict(lambda: {'text': '', 'replies': []})
    })

    for row in query_results:
        post_id = row['post_id']
        comment_id = row['comment_id']
        
        # Set post description
        if not organized_data[post_id]['description']:
            organized_data[post_id]['description'] = row['post_description']
        
        # Add comment
        if comment_id and not organized_data[post_id]['comments'][comment_id]['text']:
            organized_data[post_id]['comments'][comment_id]['text'] = row['comments']
        
        # Add reply if it exists and is not already in the list
        if row['replies'] and row['replies'] not in organized_data[post_id]['comments'][comment_id]['replies']:
            organized_data[post_id]['comments'][comment_id]['replies'].append(row['replies'])

    return dict(organized_data)
