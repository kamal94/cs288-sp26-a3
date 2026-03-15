import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import pickle

# cleaned and chunked data goes in to the dataframe

df = pd.DataFrame(data)
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

embed = embed_model.encode(df['txt'].tolist(), show_progress_bar = True)
embed = np.array(embed).astype('float32')

dim = embed.shape[1]
nlist = 100
quantizer = faiss.IndexFlatIP(dim)
index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)

faiss.normalize_L2(embed)

index.train(embed)
index.add(embed)
index.nprobe = 10

faiss.write_index(index, "eecs_ind.faiss")
df.to_pickle("data_storage.pkl")
