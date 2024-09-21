from db import get_comments, transform_tiktok_data
from chat import get_response_from_llm
from utils import preprocess_tiktok_data, analyze_hashtags, extract_json_from_text
import openai, json, asyncio
import os
import os.path as osp
from dotenv import load_dotenv

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
The input data is a nested dictionary representing TikTok posts, comments, and replies. Each post has a unique post_id and contains:
- Description: A brief text description of the post
- Post Likes: Number of likes the post received
- Comments: A dictionary of comments, each with a unique comment_id
  - Text: The comment's content
  - Comment Likes: Number of likes the comment received
  - Replies: A list of reply dictionaries, each containing:
    - Text: The reply's content
    - Reply Likes: Number of likes the reply received

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
json
[
  {{
    "scenario": "Concise description of a product selling scenario",
    "reason": "Detailed analysis of the patterns, sentiments, and insights from the data that led to this scenario",
    "referenced_posts": [
      "unique_post_id1",
      ...
    ],
    "referenced_comments": [
      "unique_comment_id1",
      ...
    ],
    "data_points": {{
      "posts": X,
      "comments": Y,
      "replies": Z
    }},
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


In <THOUGHT>, provide:
- State the <keyword>, and corresponding space of search
- Key themes and patterns observed in the data, and a comprehensive analysis of your findings
- Unexpected insights or connections you've identified
- How different levels of the data contributed to your understanding
- The process of moving from surface-level observations to deeper insights
- Any challenges encountered in the analysis and how you addressed them
- If the context is too long to process in one go:
    1. Divide the data into manageable chunks.
    2. Analyze each chunk separately, keeping track of key insights and patterns.
    3. After analyzing all chunks, synthesize the findings to create comprehensive scenarios.
    4. If you reach your output limit before completing all scenarios, indicate where you left off and that the analysis is incomplete.
- Confirmation that all insights are based strictly on the provided data, with no fabrication

In the JSON, provide analyzed scenarios for user pain points. Ensure that:
- Scenarios are diverse and offer deep insights into user needs and motivations as in <example>
- Each scenario is based on patterns/insights from multiple data points
- The "reason" field provides a thorough explanation of the data analysis, referencing specific indices
- "referenced_posts" includes indices of all useful post ids. 
- "referenced_comments" includes indices of all useful comment ids. 
- "data_points" accurately reflect the number of posts, comments, and replies referenced
- "hashtags" are relevant, trendy, and likely to enhance discoverability (5-7 hashtags, can be lower/upper cases)
- "content_guidance" offers practical and creative suggestions for TikTok video creation, based on the referenced content

The scenario should be genrate based on common shared painpoints, and the more people discuss about it, the more important it is. So generating such scenario should based on more reference. Based on this rule, generate high-qulified scenrios.

Remember to focus on uncovering deep, resonant scenarios that go beyond surface-level observations, emphasizing the underlying emotions, aspirations, and pain points that drive user behavior and engagement with the product. Always base your insights strictly on the provided data.
"""

GRADER_PROMPT = """
You are a responsible in judgeing a work created by another assistant, the guide I provided to another assistant is as followed:
<guide>
You are a helpful assistant in identification of product selling scenario. You will be given list of reviews from tiktok posts
under a specific keyword or hashtag, you need to read through the reviews carefully. Based on the review, you need to identify product selling
scenarios where creator and use them as a hook to create their content on TikTok. You analysis should not stay in shallow level, think
in deep resonation with human painpoints. For example, given reviews under specific shampoo product, a shallow reflection is to put 
content scenario in discuss of sculp problems, a deeper scenario is consider user's root reason to use the shampoo, which is to remove
the dandruff and excel their appearance. So the scenario generated under this case can be 'Target self-image during work'.

In <JSON>, provide the analyzed scenario for user painpoints:
- "scenario": A shortened description of a product selling scenario. 
- "reason": Analyse the pattern, sentiment, insights from given data, and then provide reason for choosing this scenario
- "num_comments_referred": provide an integer that explain total numbers of comments among all comments you referred to generate this scenario. 
- "example": provide examples of comments that you saw connected with scenario.
- "hashtags": A list of hashtags according to the specific scenario identified, used to attached under tiktok video post to enhace search rate. The length of hashtags list should be less than 10, and each of them will be generated after deliberate consideration.
- "guidance": Provide a content guidance on potential schema on creating a new tiktok video posts, highlight your suggested main theme, key hook, and selling scenario. 
- "confidence_score": provide confidence score on scale of 1-10 representing your confidence regarding whether the scenario generated will be a good pinpoints for this product. Be strict, only those truly oustanding can be rated with high score.
This JSON will be automatically parsed, so ensure the format is precise. Generate 5-10 Scenarios. Scenarios generated must be diverse and with DEEP INSIGHTS. 
</guide>

Here are the results they generated
<results/>
{results}
</results>

Be strict and analyze whether there is hallucination based on the comments referred and results generated, provide detailed analysis in <analysis> section. 
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
            prompt = GRADER_PROMPT.format(
                results = results
            )
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
        ## PARSE OUTPUT
        #json_output = extract_json_between_markers(text)
        #assert json_output is not None, "Failed to extract JSON from LLM output"
        print(text)
        return text

        # Iteratively improve task.
    except Exception as e:
        print(f"Failed to generate: {e}")
    ## SAVE IDEAS

    #with open(osp.join(save_dir, "scenario.json"), "w") as f:
        #json.dump(json_output, f, indent=4)
        


if __name__ == "__main__":
    client_model = "gpt-4o-2024-05-13"
    client = openai.OpenAI()
    raw_data = asyncio.run(get_comments(['#neckmassager','#footmassager','#shouldermassager']))[:10000]
    
    # Transform the raw data into the nested structure
    organized_data = transform_tiktok_data(raw_data)
    top_hashtags = analyze_hashtags(organized_data)

    print("Top 10 hashtags",top_hashtags)
    total_texts = sum(len(post['comments']) + sum(len(comment['replies']) for comment in post['comments'].values()) for post in organized_data.values())

    print(f"Processing {total_texts} total comments and replies...")
    #print(organized_data)
    processed_data = preprocess_tiktok_data(organized_data, batch_size=1000, max_workers=10)

    
    print(f"Retained {sum(len(post['comments']) + sum(len(comment['replies']) for comment in post['comments'].values()) for post in processed_data.values())} meaningful comments and replies.")

    #processed_comment_texts = [item['original'] for item in processed_comments]
    #long_text = ";".join(processed_comment_texts)

    results = generate_scenarios("./", processed_data, "neck massager", client, client_model)
    #generate_scenarios("./", processed_data, "MassageDevice", client, client_model, True, results)
    output = extract_json_from_text(results)