import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import BertTokenizer, BertModel

class AttentionCombiner(nn.Module):
    def __init__(self, embedding_dim):
        super(AttentionCombiner, self).__init__()
        self.attention = nn.Linear(embedding_dim, 1)
    
    def forward(self, chunk_embeddings):
        # chunk_embeddings shape: (num_chunks, embedding_dim)
        attention_weights = F.softmax(self.attention(chunk_embeddings).squeeze(-1), dim=0)
        # attention_weights shape: (num_chunks,)
        
        combined_embedding = torch.sum(chunk_embeddings * attention_weights.unsqueeze(1), dim=0)
        # combined_embedding shape: (embedding_dim,)
        
        return combined_embedding, attention_weights

def get_chunk_embeddings(text, chunk_size=512, stride=256):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')
    
    # Tokenize the entire text
    tokens = tokenizer.encode(text, add_special_tokens=False)
    
    chunk_embeddings = []
    
    for i in range(0, len(tokens), stride):
        chunk = tokens[i:i+chunk_size]
        
        # Add special tokens for BERT
        chunk = [tokenizer.cls_token_id] + chunk + [tokenizer.sep_token_id]
        
        # Pad if necessary
        if len(chunk) < chunk_size + 2:  # +2 for [CLS] and [SEP]
            chunk += [tokenizer.pad_token_id] * (chunk_size + 2 - len(chunk))
        
        # Convert to tensor and get embedding
        input_ids = torch.tensor(chunk).unsqueeze(0)  # Add batch dimension
        with torch.no_grad():
            outputs = model(input_ids)
            embedding = outputs.last_hidden_state[0, 0, :]  # Use [CLS] token embedding
        
        chunk_embeddings.append(embedding)
    
    return torch.stack(chunk_embeddings)

def combine_chunk_embeddings(text):
    # Get embeddings for each chunk
    chunk_embeddings = get_chunk_embeddings(text)
    
    # Initialize and apply the attention combiner
    combiner = AttentionCombiner(chunk_embeddings.shape[1])
    combined_embedding, attention_weights = combiner(chunk_embeddings)
    
    return combined_embedding, attention_weights

