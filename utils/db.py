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

                query = f'''SELECT 
                            p.aweme_id AS post_id, p.description AS post_description, p.statistics_digg_count AS post_likes,
                            c.cid AS comment_id, c.text AS comments, c.digg_count AS comment_likes,
                            r.text AS replies, r.digg_count AS reply_likes
                            FROM tiktok_posts p
                            JOIN tiktok_comments c ON p.aweme_id = c.aweme_id
                            LEFT JOIN tiktok_comments_replies r ON c.cid = r.reply_id
                            WHERE p.hashtag_keyword in {sql_value} AND CAST(p.statistics_play_count AS INTEGER) >= 500000 AND CAST(c.digg_count AS INTEGER) >= 10
                            ORDER BY CAST(p.statistics_play_count AS INTEGER) DESC;'''
                #print(query)
                results = await connection.fetch(query)
                data = [dict(record) for record in results]
                df = pd.DataFrame.from_dict(data)
                df.to_csv("ge.csv")
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
        'post_likes': 0,  # Added for post likes
        'comments': defaultdict(lambda: {
            'text': '',
            'comment_likes': 0,  # Added for comment likes
            'replies': []  # Each reply will be a dictionary with text and likes
        })
    })

    for row in query_results:
        post_id = row['post_id']
        comment_id = row['comment_id']

        # Set post description and likes
        if not organized_data[post_id]['description']:
            organized_data[post_id]['description'] = row['post_description']
            organized_data[post_id]['post_likes'] = row['post_likes']
        
        # Add comment text and likes
        if comment_id and not organized_data[post_id]['comments'][comment_id]['text']:
            organized_data[post_id]['comments'][comment_id]['text'] = row['comments']
            organized_data[post_id]['comments'][comment_id]['comment_likes'] = row['comment_likes']
        
        # Add reply if it exists and is not already in the list
        if row['replies']:
            reply_data = {
                'text': row['replies'],
                'reply_likes': row['reply_likes']
            }
            if reply_data not in organized_data[post_id]['comments'][comment_id]['replies']:
                organized_data[post_id]['comments'][comment_id]['replies'].append(reply_data)

    return organized_data
