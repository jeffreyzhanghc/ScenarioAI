import openai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import asyncio
from collections import defaultdict
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

def process_text_batch(texts: List[Tuple[str, str, str, str]]) -> List[Dict[str, str]]:
    processed_texts = []
    for id, parent_id, text_type, text in texts:
        if is_meaningful_comment(text):
            processed_texts.append({
                'id': id,
                'parent_id': parent_id,
                'type': text_type,
                'text': text
            })
    return processed_texts

def preprocess_tiktok_data(data: Dict[str, Dict], batch_size: int = 1000, max_workers: int = None) -> Dict[str, Dict]:
    all_texts = []
    
    # Flatten the data structure for parallel processing
    for post_id, post_data in data.items():
        all_texts.append((post_id, None, 'post', post_data['description']))
        for comment_id, comment_data in post_data['comments'].items():
            all_texts.append((comment_id, post_id, 'comment', comment_data['text']))
            for reply in comment_data['replies']:
                all_texts.append((f"reply_{len(all_texts)}", comment_id, 'reply', reply))
    
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
    
    # Reconstruct the nested structure with filtered texts
    filtered_data = defaultdict(lambda: {'description': '', 'comments': defaultdict(lambda: {'text': '', 'replies': []})})
    
    # Create a mapping of comment_ids to post_ids for faster lookup
    comment_to_post = {item['id']: item['parent_id'] for item in processed_texts if item['type'] == 'comment'}
    
    for item in processed_texts:
        if item['type'] == 'post':
            filtered_data[item['id']]['description'] = item['text']
        elif item['type'] == 'comment':
            post_id = item['parent_id']
            comment_id = item['id']
            filtered_data[post_id]['comments'][comment_id]['text'] = item['text']
        elif item['type'] == 'reply':
            comment_id = item['parent_id']
            post_id = comment_to_post.get(comment_id)
            if post_id:
                filtered_data[post_id]['comments'][comment_id]['replies'].append(item['text'])
            else:
                print(f"Warning: Could not find parent post for reply {item['id']}")
    
    return dict(filtered_data)


