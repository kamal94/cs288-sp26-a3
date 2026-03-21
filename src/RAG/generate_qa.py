#!/usr/bin/env python3
"""
Generate question-answer pairs from parsed documents using OpenAI.
Saves results to questions.txt, answers.txt, and reference.txt.
"""

import asyncio
import logging
import random
from pathlib import Path

from openai import AsyncOpenAI

QUESTIONS_TO_GENERATE = 100
MAX_DOC_LENGTH = 5000
MIN_DOC_LENGTH = 50
CONCURRENCY = 5

PARSED_DOCS_DIR = Path(__file__).parent.parent / "crawler" / "parsed_documents"
OUTPUT_DIR = Path(__file__).parent.parent / "crawler"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def get_all_documents(docs_dir: Path) -> list[tuple[str, Path]]:
    """Return (filename, filepath) pairs for all files in docs_dir."""
    return [(p.name, p) for p in docs_dir.iterdir() if p.is_file()]


def read_document(filepath: Path, max_length: int = MAX_DOC_LENGTH) -> str | None:
    """Read and truncate document content; return None on error or empty content."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        return content[:max_length] if content.strip() else None
    except Exception:
        log.warning("Could not read %s", filepath)
        return None


async def generate_qa(
    client: AsyncOpenAI,
    semaphore: asyncio.Semaphore,
    doc_name: str,
    doc_content: str,
) -> dict[str, str] | None:
    """Generate a single QA pair from doc_content, respecting the concurrency semaphore."""
    prompt = (
        "Analyze this document and generate ONE clear, simple factual question-answer pair.\n"
        "The question must be answerable from ONLY this document (no external knowledge needed).\n"
        "The answer should be 1-5 words maximum.\n"
        "The question should be simple and direct.\n"
        "The answer can be numeric, a name, or a date. If the answer is numeric, it should always be a number, not a word.\n\n"
        f"Document Name: {doc_name}\n\n"
        f"Document Content:\n{doc_content}\n\n"
        'If the document is too vague, noisy, or doesn\'t contain clear factual information, respond with only: "SKIP"\n\n'
        "Otherwise respond in this exact format:\n"
        "QUESTION: [question]\n"
        "ANSWER: [answer]"
    )

    async with semaphore:
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            log.error("OpenAI error for %s: %s", doc_name, e)
            return None

    text = response.choices[0].message.content or ""
    if "SKIP" in text:
        return None

    question = answer = None
    for line in text.strip().splitlines():
        if line.startswith("QUESTION:"):
            question = line.removeprefix("QUESTION:").strip()
        elif line.startswith("ANSWER:"):
            answer = line.removeprefix("ANSWER:").strip()

    if question and answer:
        return {"question": question, "answer": answer, "reference": doc_name}
    return None


async def collect_qa_pairs(
    client: AsyncOpenAI,
    documents: list[tuple[str, Path]],
    target: int,
    concurrency: int,
) -> list[dict[str, str]]:
    """
    Process documents concurrently (up to `concurrency` at a time) until
    `target` valid QA pairs are collected or all documents are exhausted.
    """
    semaphore = asyncio.Semaphore(concurrency)
    random.shuffle(documents)

    valid_docs = [
        (name, content)
        for name, path in documents
        if (content := read_document(path)) and len(content.strip()) >= MIN_DOC_LENGTH
    ]

    tasks = [
        asyncio.create_task(generate_qa(client, semaphore, name, content))
        for name, content in valid_docs
    ]

    results: list[dict[str, str]] = []
    try:
        for future in asyncio.as_completed(tasks):
            qa = await future
            if qa:
                results.append(qa)
                log.info("Collected %d/%d pairs", len(results), target)
            if len(results) >= target:
                break
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    return results[:target]


def save_results(qa_pairs: list[dict[str, str]], output_dir: Path) -> None:
    """Write questions, answers, and references to separate text files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "questions": output_dir / "questions.txt",
        "answers": output_dir / "answers.txt",
        "reference": output_dir / "reference.txt",
    }
    files["questions"].write_text("\n".join(qa["question"] for qa in qa_pairs) + "\n")
    files["answers"].write_text("\n".join(qa["answer"] for qa in qa_pairs) + "\n")
    files["reference"].write_text("\n".join(qa["reference"] for qa in qa_pairs) + "\n")

    log.info("Saved %d pairs to %s", len(qa_pairs), output_dir)
    for label, path in files.items():
        log.info("  %s: %s", label, path)


async def main() -> None:
    client = AsyncOpenAI()

    log.info("Loading documents from %s", PARSED_DOCS_DIR)
    documents = get_all_documents(PARSED_DOCS_DIR)
    log.info("Found %d documents", len(documents))

    qa_pairs = await collect_qa_pairs(client, documents, QUESTIONS_TO_GENERATE, CONCURRENCY)

    if len(qa_pairs) < QUESTIONS_TO_GENERATE:
        log.warning("Only generated %d/%d pairs", len(qa_pairs), QUESTIONS_TO_GENERATE)

    save_results(qa_pairs, OUTPUT_DIR)
    log.info("Done — generated %d question-answer pairs", len(qa_pairs))


if __name__ == "__main__":
    asyncio.run(main())
