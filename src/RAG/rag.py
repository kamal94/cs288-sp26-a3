import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path
import pickle

parsed_dir = Path("../crawler/parsed_documents")

# need grid search
chunk_size = 150
overlap = 30
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

embed_model = SentenceTransformer('all-MiniLM-L6-v2')

embed = embed_model.encode(df['txt'].tolist(), show_progress_bar = True)
embed = np.array(embed).astype('float32')

dim = embed.shape[1]
index = faiss.IndexFlatIP(dim) 
faiss.normalize_L2(embed)
index.add(embed)

faiss.write_index(index, "eecs_ind.faiss")
df.to_json("data_storage.json", orient="records")