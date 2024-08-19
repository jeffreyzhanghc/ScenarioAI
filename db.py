import psycopg2, asyncpg, asyncio



async def get_comments(word):
    pool = await asyncpg.create_pool(
    host="scenario.c94y6o2med3l.us-west-2.rds.amazonaws.com",
    port="5432",
    database="scenario",
    user="contractor",
    password="123456789"
)
    try:
        async with pool.acquire() as connection:
            # First Query: Get aweme_id values

                query = f"SELECT t.aweme_id FROM tiktok_posts t WHERE hashtag_keyword = '{word}';"
                print(query)
                results = await connection.fetch(query)
                post_ids = [record['aweme_id'] for record in results]

                if not post_ids:
                    print("No results found for the first query.")
                    return []

                # Convert the list of IDs into a string for the SQL IN clause
                formatted_ids = ','.join(f"'{id}'" for id in post_ids)
                print(formatted_ids)

                # Second Query: Fetch data based on the aweme_id list
                query = f'''
                SELECT text, hashtag_keyword, aweme_id, cid, comment_language, digg_count 
                FROM tiktok_comments
                WHERE aweme_id in ({formatted_ids})
                '''
                rows = await connection.fetch(query)

                # Convert query result into a list of dictionaries
                comments = [dict(row) for row in rows]
                print(comments)

                return comments
    except Exception as e:
        print(f"Error during connection: {e}")
        return []

    finally:
        # Properly close the connection pool
        await pool.close()
