from db import get_comments
from chat import get_response_from_llm
from utils import preprocess_comments
import openai, json, asyncio
import os
import os.path as osp
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
You are a helpful assistant in identification of product selling scenario. You will be given list of reviews from tiktok posts
under a specific keyword or hashtag, you need to read through the reviews carefully. Based on the review, you need to identify product selling
scenarios where creator and use them as a hook to create their content on TikTok. You analysis should not stay in shallow level, think
in deep resonation with human painpoints. For example, given reviews under specific shampoo product, a shallow reflection is to put 
content scenario in discuss of sculp problems, a deeper scenario is consider user's root reason to use the shampoo, which is to remove
the dandruff and excel their appearance. So the scenario generated under this case can be 'Target self-image during work'.

Here are keywords and list of reviews:
keyword: {keyword}
<review/>
{reviews}
</review>

Respond in the following format:
THOUGHT:
<THOUGHT>

Scenario JSON:
```json
<JSON>
```

In <THOUGHT>, first briefly discuss your intuitions and motivations for the idea. Detail your analysis on review, summary, and potential painpoints identified that lead to further analysis.

In <JSON>, provide the analyzed scenario for user painpoints:
- "scenario": A shortened description of a product selling scenario. 
- "reason": Provide detailed analytical reason for the selection of this scenario. You need to identify the target user, scenario, motivation
- "refer_comment": provide list of comments selected from given comments that have the most contribution on determining selling scenarios. You should provide at least 10 reference comment for each scenario, and do not consider subjectless comment like 'This is great!'
- "num_comments_referred": provide an integer that explain total numbers of comments among all comments you referred to generate this scenario.
- "hashtags": A list of hashtags according to the specific scenario identified, used to attached under tiktok video post to enhace search rate. The length of hashtags list should be less than 10, and each of them will be generated after deliberate consideration.
- "guidance": Provide a content guidance on potential schema on creating a new tiktok video posts, highlight your suggested main theme, key hook, and selling scenario. 
- "confidence_score": provide confidence score on scale of 1-10 representing your confidence regarding whether the scenario generated will be a good pinpoints for this product.
This JSON will be automatically parsed, so ensure the format is precise. Generate 10 Scenarios. Scenarios generated must be diverse and with DEEP INSIGHTS. 
"""


def generate_scenarios(
    save_dir,
    reviews,
    keyword,
    client,
    model,
    msg_history = []
):
    try:
        text, msg_history = get_response_from_llm(
            PROMPT.format(
                keyword = keyword,
                reviews = reviews
            ),
            client=client,
            model=model,
            msg_history=msg_history,
            system_message= "You are a helpful and smart assistant"
        )
        ## PARSE OUTPUT
        #json_output = extract_json_between_markers(text)
        #assert json_output is not None, "Failed to extract JSON from LLM output"
        print(text)

        # Iteratively improve task.
    except Exception as e:
        print(f"Failed to generate: {e}")
    ## SAVE IDEAS

    #with open(osp.join(save_dir, "scenario.json"), "w") as f:
        #json.dump(json_output, f, indent=4)


if __name__ == "__main__":
    
    client_model = "gpt-4o-2024-05-13"
    client = openai.OpenAI()
    comments = asyncio.run(get_comments(['Massage Devices', '#MassageTherapy', '#Relaxation']))
    comment_texts = [item['text'] for item in comments[:10000]]

    print("Preprocessing, translating, extracting emojis, and filtering comments...")
    preprocessed_comments = preprocess_comments(comment_texts,batch_size=200,max_workers=10)

    print(f"Filtered {len(comment_texts) - len(preprocessed_comments)} low-quality comments.")
    print(f"Proceeding with {len(preprocessed_comments)} meaningful comments.")

    processed_comment_texts = [item['original'] for item in preprocessed_comments]
    # Example usage
    long_text = ";".join(processed_comment_texts)

    #combined_embedding, attention_weights = combine_chunk_embeddings(long_text)
    #print(combined_embedding)

    generate_scenarios("./",comment_texts,"MassageDevice",client,client_model)