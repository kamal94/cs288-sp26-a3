#!/bin/bash
cat src/RAG/eecs_ind.faiss.part.* > src/RAG/eecs_ind.faiss
cat src/RAG/data_storage.json.part.* > src/RAG/data_storage.json

python3 src/RAG/rag.py "$1" "$2"