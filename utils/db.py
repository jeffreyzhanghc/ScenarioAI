import psycopg2, asyncpg, asyncio, os, pandas as pd
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()


host = os.getenv('host')
pw = os.getenv('password')

# Database configuration
HOST = os.getenv('host')
PORT = "5432"  # Default PostgreSQL port
DATABASE = "scenario"
USER = "contractor"
PASSWORD = os.getenv('password')

async def create_pool():
    return await asyncpg.create_pool(
        host=HOST,
        port=PORT,
        database=DATABASE,
        user=USER,
        password=PASSWORD,
        min_size=1,
        max_size=10  # Adjust based on your application's needs
    )

async def fetch_in_batches(connection, query, params=None, batch_size=10000):
    async with connection.transaction():
        cursor = await connection.cursor(query, *params)
        while True:
            records = await cursor.fetch(batch_size)
            if not records:
                break
            yield [dict(record) for record in records]

async def get_data(words, min_play_count=50000, min_comment_likes=5):
    # Prepare SQL queries
    posts_query = '''
        SELECT 
            p.aweme_id AS post_id,
            p.description AS post_description,
            p.statistics_digg_count::INTEGER AS post_likes
        FROM tiktok_posts p
        WHERE p.hashtag_keyword = ANY($1)
          AND p.statistics_play_count::INTEGER >= $2
        ORDER BY p.statistics_play_count::INTEGER DESC
    '''

    comments_query = '''
        SELECT 
            c.aweme_id AS post_id,
            c.cid AS comment_id,
            c.text AS comments,
            c.digg_count::INTEGER AS comment_likes
        FROM tiktok_comments c
        WHERE c.aweme_id = ANY($1)
          AND c.digg_count::INTEGER >= $2
    '''

    replies_query = '''
        SELECT 
            r.reply_id AS comment_id,
            r.text AS replies,
            r.digg_count::INTEGER AS reply_likes
        FROM tiktok_comments_replies r
        WHERE r.reply_id = ANY($1)
    '''

    pool = await create_pool()
    try:
        async with pool.acquire() as connection:
            # Fetch posts
            posts = []
            async for batch in fetch_in_batches(connection, posts_query, (words, min_play_count)):
                posts.extend(batch)
            if not posts:
                return pd.DataFrame()

            posts_df = pd.DataFrame(posts)
            post_ids = posts_df['post_id'].tolist()

            # Fetch comments in batches
            comments = []
            if post_ids:
                async for batch in fetch_in_batches(connection, comments_query, (post_ids, min_comment_likes)):
                    comments.extend(batch)

            if not comments:
                # No comments found
                posts_df['comment_id'] = None
                posts_df['comments'] = None
                posts_df['comment_likes'] = None
                posts_df['replies'] = None
                posts_df['reply_likes'] = None
                return posts_df

            comments_df = pd.DataFrame(comments)
            comment_ids = comments_df['comment_id'].tolist()

            # Fetch replies in batches
            replies = []
            if comment_ids:
                async for batch in fetch_in_batches(connection, replies_query, (comment_ids,)):
                    replies.extend(batch)
                if replies:
                    replies_df = pd.DataFrame(replies)
                else:
                    replies_df = pd.DataFrame(columns=['comment_id', 'replies', 'reply_likes'])
            else:
                replies_df = pd.DataFrame(columns=['comment_id', 'replies', 'reply_likes'])

            # Merge dataframes
            data = posts_df.merge(comments_df, on='post_id', how='left')
            if not replies_df.empty:
                data = data.merge(replies_df, on='comment_id', how='left')
            else:
                data['replies'] = None
                data['reply_likes'] = None

            return data

    except Exception as e:
        print(f"Error during data retrieval: {e}")
        return pd.DataFrame()
    finally:
        await pool.close()





