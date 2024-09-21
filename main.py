from utils.db import get_data
from utils.chat import get_response_from_llm
from utils.utils import preprocess_tiktok_data, analyze_hashtags, extract_json_from_text
from rag.chunk import create_chunks_from_df, upsert_embeddings_to_pinecone, query_pinecone, rerank_results, get_full_contexts
import openai, json, asyncio
import os
import os.path as osp
from dotenv import load_dotenv
import numpy as np, pandas as pd
load_dotenv()

PROMPT = """
You are an expert AI assistant specializing in content strategy and market analysis. Your task is to analyze a large dataset of social media interactions to identify compelling product usage scenarios for TikTok content creation. You will be provided with a productkeyword and a structured dataset of posts, comments, and replies from TikTok.
When crafting scenarios, consider the following:

1. Target Audience (WHO): Identify specific user personas or demographics that would benefit from the product.
2. Need or Desire (WHAT): Pinpoint the exact problem solved or desire fulfilled by the product.
3. Context (WHERE): Describe the situation or environment where the product would be most valuable.
4. Emotional Resonance: Tap into the underlying emotions, aspirations, or identity of the target audience.
5. Storytelling Potential: Create a narrative that can be easily translated into engaging TikTok content.

<example>
For example, when selling a neck massager, a compelling scenario could be:

WHO: Hardworking professionals with physically demanding jobs
WHAT: Quick, effective stress relief and muscle relaxation
WHERE: In their vehicle after a long workday

Scenario: "The Tough Guy's Secret Weapon"
Content Idea: A robust, masculine worker climbs into his truck after a grueling shift. The caption reads: "Tough life for strong men, easy life for weak men!" Instead of complaining, he confidently applies a neck massager, showcasing that even the toughest individuals prioritize self-care. This scenario resonates with male customers who value strength but also seek practical solutions for physical stress.

Your task is to generate similarly deep, emotionally resonant scenarios based on the provided data, ensuring each scenario has clear potential for engaging TikTok content.
</example>

## reivew Data Structure
The input data is a list of text sorted by the number of likes and relevance to keyword in descending order. 

## Input:
<keyword> {keyword} </keyword>

<review>
{reviews}
</review>

#Instructions for Analysis:
1. Analyze the reviews data comprehensively, considering the hierarchical relationship between posts, comments, and replies.
2. Identify recurring themes, pain points, and user motivations across multiple posts and comments. Provide the estimation on frequency of these painpoints.
3. Look for connections between these pain points and the <keyword>.
4. Deduce selling scenarios/content creation scenarios that deeply resonate with users.
5. Consider the number of likes as a weight for the importance of each text.
6. Pay special attention to emotional language, repeated concerns, and unique user experiences.
7. Look for underlying motivations that might not be explicitly stated.

Respond in the following format:
THOUGHT:
<THOUGHT>

Scenario JSON:
```json
[
  {{
    "scenario": "Concise description of a product selling scenario",
    "reason": "Detailed analysis of the patterns, sentiments, and insights from the data that led to this scenario",
    "hashtags": [
      "#RelevantHashtag1",
      "#RelevantHashtag2",
      "..."
    ],
    "content_guidance": {{
      "main_theme": "Central theme of the proposed TikTok content",
      "hook": "Attention-grabbing element to use in the first few seconds",
      "key_points": [
        "Important point 1 to cover in the video",
        "Important point 2 to cover in the video",
        "..."
      ],
      "visuals": [
        "Suggestion for visual element 1",
        "Suggestion for visual element 2",
        "..."
      ],
      "call_to_action": "Proposed call to action for the end of the video"
    }}
  }}
]
```

In <THOUGHT>, provide:
- State the <keyword>, and corresponding space of search
- Key themes and patterns observed in the data, and a comprehensive analysis of your findings
- Unexpected insights or connections you've identified
- How different levels of the data contributed to your understanding
- The process of moving from surface-level observations to deeper insights
- Any challenges encountered in the analysis and how you addressed them.
- Confirmation that all insights are based strictly on the provided data, with no fabrication

In the JSON, provide analyzed scenarios for user pain points. Ensure that:
- Scenarios are diverse and offer deep insights into user needs and motivations as in <example>
- Each scenario is based on patterns/insights from multiple data points
- The "reason" field provides a thorough explanation of the data analysis, referencing specific indices
- "hashtags" are relevant, trendy, and likely to enhance discoverability (5-7 hashtags, can be lower/upper cases)
- "content_guidance" offers practical and creative suggestions for TikTok video creation, based on the referenced content

The scenario should be genrate based on common shared painpoints, and the more people discuss about it, the more important it is. So generating such scenario should based on more reference. Based on this rule, generate high-qulified scenrios.

Remember to focus on uncovering deep, resonant scenarios that go beyond surface-level observations, emphasizing the underlying emotions, aspirations, and pain points that drive user behavior and engagement with the product. Always base your insights strictly on the provided data.

After generating the scenarios, do the following steps to reflect and revise the scenarios in 3 turns, and be very strict with the quality of generation:
1. As a different kind of user, do I think the content is resonant with me? if not, how to improve it?
2. As a creator, do I think the content is tightly connected to the keyword product?
3. As a tiktok marketer, do I think the content is attractive to the target audience?
4. Do I use enought reference to genrate the scenario?


write down your thoughts in <relfections >and revise the scenarios based on your thoughts.
"""




        
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
    keyword = "Neck Massager"
    input_hashtags = ['#footmassager', '#neckmassager','Massage Devices','Neck Massager']
    #print(keyword,input_hashtags)
    # Fetch and process data

    #'''
    # Step 0: Get data from postgres
    raw_data = asyncio.run(get_data(input_hashtags))

    # Step 1: Create chunks
    chunks_df = create_chunks_from_df(raw_data)
    
    # Step 2: Upsert embeddings to Pinecone
    upsert_embeddings_to_pinecone(chunks_df)
    
    # Step 3: Query Pinecone with input query
    query_text = "Neck Massager"
    results = query_pinecone(query_text, top_k=400)
    
    # Step 4: Rerank results
    results_df = rerank_results(results)
    
    # Step 5: Reconstruct full contexts
    results_df = get_full_contexts(results_df, chunks_df)
    #'''
    #df = pd.read_csv('results.csv')
    

    #hierarchical_data = build_hierarchical_data(raw_data)
    #chunks_df = flatten_and_chunk_data(hierarchical_data)
    #chunks_df['embedding'] = chunks_df['text'].apply(get_embedding)
    #faiss_index = save_embeddings_to_faiss(chunks_df)

    #query_text = 'Neck Massager'  
    #query_embedding = get_embedding(query_text)
    #query_embedding = np.array([query_embedding]).astype('float32')

    # Retrieve relevant chunks
    #retrieved_chunks = retrieve_chunks(query_embedding, faiss_index, chunks_df)
    #retrieved_chunks.sort_values(by=['distance', 'likes'], ascending=[True, False], inplace=True)

    #retrieved_chunks['full_context'] = retrieved_chunks.apply(lambda row: get_full_context(row, chunks_df), axis=1)
    #reviews = construct_prompt(retrieved_chunks,query_text)
    #breakpoint()


    '''
    organized_data = transform_tiktok_data(raw_data)
    total_texts = sum(len(post['comments']) + sum(len(comment['replies']) for comment in post['comments'].values()) for post in organized_data.values())
    print(f"Processing {total_texts} total comments and replies...")
    top_hashtags = analyze_hashtags(organized_data)
    processed_data = preprocess_tiktok_data(organized_data, batch_size=1000, max_workers=10)
    print(f"Retained {sum(len(post['comments']) + sum(len(comment['replies']) for comment in post['comments'].values()) for post in processed_data.values())} meaningful comments and replies.")
    '''

    breakpoint()
    results = generate_scenarios("./", df['full_context'], keyword, client, client_model)
    print(results)
    

    scenarios = extract_json_from_text(results)
    

    response = {
        'scenarios': scenarios
    }
    
    return response

if __name__ == "__main__":
    generate()