import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path
import pickle
import torch

parsed_dir = Path("../crawler/parsed_documents")

# need grid search
chunk_size = 200
overlap = 40
step = chunk_size - overlap
data = []
for file in parsed_dir.iterdir():
    if file.is_file():
        try:
            text = file.read_text(encoding='utf-8')
            words = text.split()
            if not words:
                continue
                
            for i in range(0, len(words), step):
                chunk_text = " ".join(words[i:i+chunk_size])
                data.append({'txt': chunk_text})
            
        except Exception:
            continue

df = pd.DataFrame(data, columns=['txt'])

# cleaned and chunked data goes in to the dataframe
# df = pd.DataFrame(data)

device = "mps" if torch.backends.mps.is_available() else "cpu"

embed_model = SentenceTransformer('BAAI/bge-small-en-v1.5', device=device)

embed = embed_model.encode(df['txt'].tolist(), show_progress_bar=True, batch_size=16)
embed = np.array(embed).astype('float32')

dim = embed.shape[1]
index = faiss.IndexFlatIP(dim) 
faiss.normalize_L2(embed)
index.add(embed)

faiss.write_index(index, "eecs_ind.faiss")
df.to_json("data_storage.json", orient="records")