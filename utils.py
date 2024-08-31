import openai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import asyncio
from collections import defaultdict, Counter
from typing import List, Dict, Tuple
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
import emoji
import re
import spacy
from concurrent.futures import ProcessPoolExecutor, as_completed


# Load a small spaCy model for efficient processing
nlp = spacy.load("en_core_web_sm", disable=["ner", "textcat"])

# Set a larger cache size for language detection
CACHE_SIZE = 1000000

def is_meaningful_comment(comment: str) -> bool:
    # Remove emojis for text analysis
    text_without_emoji = emoji.replace_emoji(comment, replace='')
    
    # Check if the comment is primarily emojis
    if len(text_without_emoji.strip()) / len(comment) < 0.2:
        return False
    
    # Check comment length
    if len(text_without_emoji.split()) < 2:
        return False
    
    # List of generic, low-information phrases
    generic_phrases = {"this is great", "love it", "awesome", "nice", "cool", "good"}
    if text_without_emoji.lower().strip() in generic_phrases:
        return False
    
    # Use spaCy for linguistic analysis
    doc = nlp(text_without_emoji)
    
    # Check for presence of verb
    has_verb = any(token.pos_ == "VERB" for token in doc)
    
    # Check for presence of noun or pronoun (could be subject or object)
    has_noun_or_pronoun = any(token.pos_ in ["NOUN", "PROPN", "PRON"] for token in doc)
    
    # Check for presence of adjective or adverb (indicates descriptive content)
    has_modifier = any(token.pos_ in ["ADJ", "ADV"] for token in doc)
    
    # Check for dependency structure
    has_subject = any(token.dep_ in ["nsubj", "nsubjpass"] for token in doc)
    has_object = any(token.dep_ in ["dobj", "pobj", "iobj"] for token in doc)
    
    # Determine if the comment is meaningful based on linguistic structure
    is_meaningful = (has_verb and has_noun_or_pronoun) or (has_subject and has_object) or (has_modifier and has_noun_or_pronoun)
    
    return is_meaningful

def process_text_batch(texts: List[Tuple[str, str, str, str, int]]) -> List[Dict[str, str]]:
    processed_texts = []
    for id, parent_id, text_type, text, likes in texts:  # Include 'likes' in the unpacking
        if is_meaningful_comment(text):
            processed_texts.append({
                'id': id,
                'parent_id': parent_id,
                'type': text_type,
                'text': text,
                'likes': likes  # Include likes in the resulting dictionary
            })
    return processed_texts

def preprocess_tiktok_data(data: Dict[str, Dict], batch_size: int = 1000, max_workers: int = None) -> Dict[str, Dict]:
    all_texts = []
    
    # Flatten the data structure for parallel processing
    for post_id, post_data in data.items():
        all_texts.append((post_id, None, 'post', post_data['description'], post_data['post_likes']))
        for comment_id, comment_data in post_data['comments'].items():
            all_texts.append((comment_id, post_id, 'comment', comment_data['text'], comment_data['comment_likes']))
            for reply in comment_data['replies']:
                all_texts.append((f"reply_{len(all_texts)}", comment_id, 'reply', reply['text'], reply['reply_likes']))
    
    # Remove duplicates
    unique_texts = list(set(all_texts))
    
    # Split texts into batches
    batches = [unique_texts[i:i + batch_size] for i in range(0, len(unique_texts), batch_size)]
    
    processed_texts = []
    
    # Process batches in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {executor.submit(process_text_batch, batch): batch for batch in batches}
        for future in as_completed(future_to_batch):
            processed_texts.extend(future.result())
    
    # Reconstruct the nested structure with filtered texts and include likes
    filtered_data = defaultdict(lambda: {
        'description': '', 'post_likes': 0,
        'comments': defaultdict(lambda: {'text': '', 'comment_likes': 0, 'replies': []})
    })
    
    # Create a mapping of comment_ids to post_ids for faster lookup
    comment_to_post = {item['id']: item['parent_id'] for item in processed_texts if item['type'] == 'comment'}
    
    for item in processed_texts:
        if item['type'] == 'post':
            filtered_data[item['id']]['description'] = item['text']
            filtered_data[item['id']]['post_likes'] = item['likes']
        elif item['type'] == 'comment':
            post_id = item['parent_id']
            comment_id = item['id']
            filtered_data[post_id]['comments'][comment_id]['text'] = item['text']
            filtered_data[post_id]['comments'][comment_id]['comment_likes'] = item['likes']
        elif item['type'] == 'reply':
            comment_id = item['parent_id']
            post_id = comment_to_post.get(comment_id)
            if post_id:
                filtered_data[post_id]['comments'][comment_id]['replies'].append({
                    'text': item['text'],
                    'reply_likes': item['likes']
                })
            else:
                print(f"Warning: Could not find parent post for reply {item['id']}")
    
    return dict(filtered_data)

def extract_hashtags(text):
    words = text.split()
    hashtags = [re.sub(r'[^\w#]', '', word) for word in words if word.startswith('#')]
    return hashtags

def analyze_hashtags(organized_data):
    all_hashtags = []
    
    for post_data in organized_data.values():
        description = post_data['description']
        hashtags = extract_hashtags(description)
        all_hashtags.extend(hashtags)
    
    # Count the occurrences of each hashtag
    hashtag_counts = Counter(all_hashtags)
    if '#' in hashtag_counts:
        del hashtag_counts['#']
    # Get the top 10 most common hashtags
    top_10_hashtags = hashtag_counts.most_common(10)
    
    return top_10_hashtags

def extract_json_from_text(text):
    # Find content between triple backticks
    json_match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
    
    if json_match:
        json_string = json_match.group(1)
        try:
            # Parse the JSON string
            json_data = json.loads(json_string)
            return json_data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None
    else:
        print("No JSON found in the text")
        return None