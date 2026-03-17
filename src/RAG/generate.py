import pandas as pd
import numpy as np
import faiss
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
    
    model = SentenceTransformer('thenlper/gte-large', device='mps')
    ind = faiss.read_index(str(index_path))
    ind.nprobe = 10
    
    return model, ind, df

def get_context(q, model, index, df, k=10):
    q_embed = model.encode([q]).astype('float32')
    faiss.normalize_L2(q_embed)
    _, ind = index.search(q_embed, k)

    txts = []
    for i in ind[0]:
        if i != -1:
            txts.append(df.iloc[i]['txt'])
    
    return " ".join(txts)


def main():
    q_path = sys.argv[1]
    pred_path = sys.argv[2]
    model, ind, df = load()

    with open(q_path, 'r', encoding='utf-8') as f:
        questions = [line.strip() for line in f if line.strip()]

    ans = []
    sys_prompt = f"""You will act as a strict QA bot answering questions 
        about the University of California, Berkeley EECS department. Your answer should be as concise as possible; MUST BE UNDER 10 WORDS.
        You must extract the answer directly from the text if possible. If the context 
        provided does not contain the answer, reply with an educated guess (using both
        the information given to you and your existing knowledge base). Do not reply full sentence structure,
        i.e., do not include punctuation. If there are multiple correct answers, reply with ONLY ONE."""

    for q in questions:
        try:
            context = get_context(q, model, ind, df)
            query = f"Context:\n{context}\n\nQuestion: {q}\nAnswer:"
            res = llm.call_llm(query, sys_prompt, "meta-llama/llama-3.1-8b-instruct", 10, 0.0, 15)
            clean_res = res.replace("\n", " ").replace("\r", " ").strip()
            ans.append(clean_res)
        except Exception: # OpenRouter time-out check
            print(f"error with question: '{q}'")
            ans.append("Timeout error.")


    with open(pred_path, 'w', encoding='utf-8') as f:
        for a in ans:
            f.write(f"{a}\n")

if __name__ == "__main__":
    main()