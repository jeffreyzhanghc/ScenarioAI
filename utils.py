import openai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import asyncio
from typing import List, Dict, Tuple
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
import emoji
import re
import spacy
from concurrent.futures import ProcessPoolExecutor, as_completed

nlp = spacy.load("en_core_web_sm")

def is_meaningful_comment(comment: str, nlp) -> bool:
    # Remove emojis for text analysis
    text_without_emoji = emoji.replace_emoji(comment, replace='')
    
    # Check if the comment is primarily emojis
    if len(text_without_emoji.strip()) / len(comment) < 0.2:
        return False
    
    # Check comment length
    if len(text_without_emoji.split()) < 3:
        return False
    
    # List of generic, low-information phrases
    generic_phrases = {"this is great", "love it", "awesome", "nice", "cool", "good"}
    if text_without_emoji.lower().strip() in generic_phrases:
        return False
    
    # Use spaCy for linguistic analysis
    doc = nlp(text_without_emoji)
    
    # Check if the comment has a subject and a verb
    has_subject = any(token.dep_ == "nsubj" for token in doc)
    has_verb = any(token.pos_ == "VERB" for token in doc)
    
    # Check for named entities (might indicate more specific content)
    has_named_entity = len(doc.ents) > 0
    
    return (has_subject and has_verb) or has_named_entity

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return 'unknown'

def translate_text(text: str, dest='en') -> str:
    try:
        translator = GoogleTranslator(source='auto', target=dest)
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails

def process_comment_batch(comments: List[str]) -> List[Dict[str, str]]:
    # Load spaCy model within the process
    nlp = spacy.load("en_core_web_sm")
    
    processed_comments = []
    for comment in comments:
        if is_meaningful_comment(comment, nlp):
            lang = detect_language(comment)
            if lang != 'en':
                translated = translate_text(comment)
            else:
                translated = comment
            processed_comments.append({
                'original': comment,
                'translated': translated.strip().lower(),
                'language': lang
            })
    return processed_comments

def preprocess_comments(comments: List[str], batch_size: int = 100, max_workers: int = None) -> List[Dict[str, str]]:
    all_processed_comments = []
    
    # Split comments into batches
    batches = [comments[i:i + batch_size] for i in range(0, len(comments), batch_size)]
    
    # Process batches in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {executor.submit(process_comment_batch, batch): batch for batch in batches}
        for future in as_completed(future_to_batch):
            all_processed_comments.extend(future.result())
    
    return all_processed_comments


