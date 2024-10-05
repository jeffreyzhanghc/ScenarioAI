import psycopg2, asyncpg, asyncio, os, pandas as pd
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()


# Database configuration
HOST = os.getenv('HOST_POSTGRE')
PORT = os.getenv('PORT_POSTGRE')  # Default PostgreSQL port
DATABASE = os.getenv('DB_POSTGRE')
USER = os.getenv('USER_POSTGRE')
PASSWORD = os.getenv('password')


async def create_pool():
    return await asyncpg.create_pool(
        host=HOST,
        port=PORT,
        database=DATABASE,
        user=USER,
        password=PASSWORD,
        min_size=1,
        max_size=10
    )

async def get_data(words, min_play_count=50000, min_comment_likes=5):
    # Prepare SQL query with joins
    query = '''
        SELECT 
            p.aweme_id AS post_id,
            p.description AS post_description,
            p.statistics_digg_count AS post_likes,
            c.cid AS comment_id,
            c.text AS comments,
            c.digg_count AS comment_likes,
            r.text AS replies,
            r.digg_count AS reply_likes
        FROM tiktok_posts p
        LEFT JOIN tiktok_comments c ON p.aweme_id = c.aweme_id AND c.digg_count >= $3
        LEFT JOIN tiktok_comments_replies r ON c.cid = r.reply_id
        WHERE p.hashtag_keyword = ANY($1)
          AND p.statistics_play_count >= $2
        ORDER BY p.statistics_play_count DESC
    '''

    pool = await create_pool()
    try:
        async with pool.acquire() as connection:
            # Fetch all records
            records = await connection.fetch(query, words, min_play_count, min_comment_likes)
            if not records:
                return pd.DataFrame()

            # Convert records to list of dictionaries
            data = [dict(record) for record in records]

            # Create DataFrame
            df = pd.DataFrame(data)

            # Handle missing values (if any)
            df.to_csv("results.csv")
            return df

    except Exception as e:
        print(f"Error during data retrieval: {e}")
        return pd.DataFrame()
    finally:
        await pool.close()





