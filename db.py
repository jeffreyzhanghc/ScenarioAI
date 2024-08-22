import psycopg2, asyncpg, asyncio, os
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

                query = f"SELECT t.aweme_id FROM tiktok_posts t WHERE hashtag_keyword in {sql_value};"
                #print(query)
                results = await connection.fetch(query)
                post_ids = [record['aweme_id'] for record in results]

                if not post_ids:
                    print("No results found for the first query.")
                    return []

                # Convert the list of IDs into a string for the SQL IN clause
                formatted_ids = ','.join(f"'{id}'" for id in post_ids)
                #print(formatted_ids)

                # Second Query: Fetch data based on the aweme_id list
                query = f'''
                SELECT text, hashtag_keyword, aweme_id, cid, comment_language, digg_count 
                FROM tiktok_comments
                WHERE aweme_id in ({formatted_ids})
                '''
                rows = await connection.fetch(query)

                # Convert query result into a list of dictionaries
                comments = [dict(row) for row in rows]
                #print(comments)

                return comments
    except Exception as e:
        print(f"Error during connection: {e}")
        return []

    finally:
        # Properly close the connection pool
        await pool.close()
