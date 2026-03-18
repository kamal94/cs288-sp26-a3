import pandas as pd
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import llm
import sys
import json
from pathlib import Path


def load():
    script_dir = Path(__file__).parent
    
    index_path = script_dir / "eecs_ind.faiss"
    json_path = script_dir / "data_storage.json"
    df = pd.read_json(str(json_path), orient="records")
    
    model = SentenceTransformer('BAAI/bge-base-en-v1.5')
    ind = faiss.read_index(str(index_path))
    
    tokenized_corpus = [[word.lower() for word in doc.split() if len(word) > 2] for doc in df['txt'].tolist()]
    bm25 = BM25Okapi(tokenized_corpus)
    
    return model, ind, df, bm25

def get_context(q, model, index, df, bm25, k_dense=8, k_sparse=4):
    q_embed = model.encode([q]).astype('float32')
    faiss.normalize_L2(q_embed)
    _, f_ind = index.search(q_embed, k_dense)
    first = [i for i in f_ind[0] if i != -1]

    t_query = [word.lower() for word in q.split() if len(word) > 2]
    if not t_query:
        t_query = q.lower().split() 
        
    second = np.argsort(bm25.get_scores(t_query))[::-1][:k_sparse].tolist()
    return "\n\n".join([df.iloc[i]['txt'] for i in list(set(first + second))])


def main():
    q_path = sys.argv[1]
    pred_path = sys.argv[2]
    model, ind, df, bm25 = load()

    with open(q_path, 'r', encoding='utf-8') as f:
        questions = [line.strip().strip('"\'') for line in f if line.strip()]

    ans = []
    sys_prompt = """You are a highly precise QA bot for the UC Berkeley EECS department. 
    Base your answer STRICTLY on the provided context. Follow these rules exactly:
    1. Extract the exact short answer directly from the text (must be under 10 words).
    2. Do NOT write full sentences or conversational filler. Output ONLY the core entity, name, date, or number.
    3. If there are multiple valid answers in the context, provide ONLY ONE of them.
    4. If the question is a Yes/No question, output exactly "Yes" or "No".
    5. If the question requires counting or arithmetic, output ONLY the final calculated number.
    6. If the exact answer is absolutely not in the context, output "Not available"."""
    
    for q in questions:
        try:
            context = get_context(q, model, ind, df, bm25)
            query = f"Context:\n{context}\n\nQuestion: {q}\nAnswer:"
            res = llm.call_llm(query, sys_prompt, "meta-llama/llama-3.1-8b-instruct", 20, 0.0, 25)
            clean_res = res.replace("\n", " ").replace("\r", " ").strip()
            ans.append(clean_res)
        except Exception: # OpenRouter time-out check
            print(f"error with question: '{q}'")
            ans.append("not available")


    with open(pred_path, 'w', encoding='utf-8') as f:
        for a in ans:
            f.write(f"{a}\n")

if __name__ == "__main__":
    main()