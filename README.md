# Assignment 3
[link](https://cs288.eecs.northwestern.edu/assignments/a3/)

## QA Dataset

The evaluation dataset lives in `src/RAG/`:

| File | Description |
|---|---|
| `qa_questions.txt` | 114 factual questions, one per line |
| `qa_answers.txt` | Ground-truth answers aligned line-by-line with the questions |

### Content

Questions are short, factual queries derived from UC Berkeley EECS web pages (faculty bios, news articles, technical reports, course pages, etc.). Answers are concise, typically 1–5 words, and may be a name, date, number, or short phrase. Numeric answers are always expressed as digits, not words.

### Generation

Questions and answers were generated with `src/RAG/generate_qa.py` using the OpenAI `gpt-3.5-turbo` model.

**How it works:**

1. All documents under `src/crawler/parsed_documents/` are loaded and shuffled.
2. Each document is sent to the model in an independent prompt asking for one factual QA pair answerable solely from that document's content.
3. The model returns `SKIP` for documents that are too noisy or lack clear facts; those are discarded.
4. Generation stops once `QUESTIONS_TO_GENERATE` (adjustable parameter) valid pairs are collected.

## Running the RAG Pipeline

### Prerequisites

Install dependencies and set the required API key:

```bash
pip install -r src/RAG/requirements.txt
export OPENROUTER_API_KEY=<your_key>
```

The pipeline calls [OpenRouter](https://openrouter.ai/) for LLM inference. An account and API key are required.

### Usage

```bash
python src/RAG/generate.py <questions_file> <predictions_output_file>
```

| Argument | Description |
|---|---|
| `questions_file` | Path to a plain-text file with one question per line |
| `predictions_output_file` | Path where predicted answers will be written (one per line, aligned with input) |

**Example — run against the included QA dataset:**

```bash
python src/RAG/generate.py src/RAG/qa_questions.txt src/RAG/qa_answers_pred.txt
```

### How it works

1. **Load index** — reads `eecs_ind.faiss` (dense vector index) and `data_storage.json` (document store) from `src/RAG/`.
2. **Hybrid retrieval** — for each question, retrieves the top-8 chunks via dense search (`BAAI/bge-small-en-v1.5` embeddings + FAISS) and top-4 chunks via sparse search (BM25); the union forms the context.
3. **LLM answer** — the context and question are sent to `meta-llama/llama-3.1-8b-instruct` via OpenRouter. The model is instructed to return a short, direct answer (under 10 words).
4. **Write predictions** — one answer per line is written to the output file.

If a request times out, the line is recorded as `"not available"` and processing continues.

### Allowed models

The LLM call is restricted to the models listed in `src/RAG/llm.py`:

- `meta-llama/llama-3.1-8b-instruct` *(default)*
- `meta-llama/llama-3-8b-instruct`
- `qwen/qwen3-8b`
- `qwen/qwen-2.5-7b-instruct`
- `allenai/olmo-3-7b-instruct`
- `mistralai/mistral-7b-instruct`
