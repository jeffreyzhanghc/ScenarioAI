from db import get_comments, transform_tiktok_data
from chat import get_response_from_llm
from utils import preprocess_tiktok_data
import openai, json, asyncio
import os
import os.path as osp
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
You are a helpful assistant in identification of product selling scenario. You will be given list of reviews from tiktok posts
under a list of keywords, you need to read through the reviews carefully. Based on the review, you need to identify product selling
scenarios where creator and use them as a hook to create their content on TikTok. You analysis should not stay in shallow level, think
in deep resonation with human painpoints. For example, given reviews under specific shampoo product, a shallow reflection is to put 
content scenario in discuss of sculp problems, a deeper scenario is consider user's root reason to use the shampoo, which is to remove
the dandruff and excel their appearance. So the scenario generated under this case can be 'Target self-image during work'.

Here are keywords and list of reviews:
keyword: {keyword}
<review/>
{reviews}
</review>

The review data is structured as follows:
- Outermost level: Post descriptions
- Middle level: Comments on posts
- Innermost level: Replies to comments

Instructions for Analysis:
1. Carefully read and analyze the entire dataset, considering the context at each level (post, comment, reply).
2. Identify recurring themes, pain points, and user motivations across multiple posts and comments.
3. Look for unexpected or non-obvious connections between user experiences and product benefits.
4. Consider the broader lifestyle and emotional context in which users are engaging with the product.
5. Aim for a mix of practical, emotional, and aspirational scenarios.

Respond in the following format:
THOUGHT:
<THOUGHT>

Scenario JSON:
```json
<JSON>
```

In <THOUGHT>, Provide a comprehensive analysis of your findings. Discuss:
- Key themes and patterns observed in the data
- Unexpected insights or connections you've identified
- How different levels of the data (posts, comments, replies) contributed to your understanding
- The process of moving from surface-level observations to deeper insights

In <JSON>, provide the analyzed scenario for user painpoints:
- "scenario": Concise description of a product selling scenario.
- "reason": Detailed analysis explaining: 1)Target user profile; 2)Specific user pain points or desires addressed; 3) How the product solves a problem or fulfills a need; 4) Why this scenario is particularly compelling or unique
- "refer_content": Provided referred content with same format as input reviews, select those you used to generate this scenario
- "num_comments_referred": provide an integer that explain total numbers of posts, comments, and replies referred
- "hashtags": A list of hashtags according to the specific scenario identified, used to attached under tiktok video post to enhace search rate. The length of hashtags list should be less than 10, and each of them will be generated after deliberate consideration.
- "guidance": Provide a content guidance on potential schema on creating a new tiktok video posts, highlight your suggested main theme, key hook, key points to cover, and suggested visuals or demonstrations
- "confidence_score": provide confidence score on scale of 1-10 representing your confidence regarding whether the scenario generated will be a good pinpoints for this product. Be strict, only those truly oustanding can be rated with high score.
This JSON will be automatically parsed, so ensure the format is precise. Generate 5-10 Scenarios. Scenarios generated must be diverse and with DEEP INSIGHTS. 
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
- "reason": Provide detailed analytical reason for the selection of this scenario. You need to identify the target user, scenario, motivation
- "refer_comment": provide list of comments selected from given comments that have the most contribution on determining selling scenarios. You should provide at least 10 reference comment for each scenario, and do not consider subjectless comment like 'This is great!'
- "num_comments_referred": provide an integer that explain total numbers of comments among all comments you referred to generate this scenario. 
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
    raw_data = asyncio.run(get_comments(['Massage Devices', '#MassageTherapy', '#Relaxation']))[:9000]
    
    # Transform the raw data into the nested structure
    organized_data = transform_tiktok_data(raw_data)
    total_texts = sum(len(post['comments']) + sum(len(comment['replies']) for comment in post['comments'].values()) for post in organized_data.values())

    print(f"Processing {total_texts} total comments and replies...")
    #print(organized_data)
    processed_data = preprocess_tiktok_data(organized_data, batch_size=1000, max_workers=10)

    
    print(f"Retained {sum(len(post['comments']) + sum(len(comment['replies']) for comment in post['comments'].values()) for post in processed_data.values())} meaningful comments and replies.")

    #processed_comment_texts = [item['original'] for item in processed_comments]
    #long_text = ";".join(processed_comment_texts)

    results = generate_scenarios("./", processed_data, "MassageDevice", client, client_model)
    generate_scenarios("./", processed_data, "MassageDevice", client, client_model, True, results)