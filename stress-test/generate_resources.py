"""Generates the terms typed by the simulated users, sampled from the term file loaded by the pipeline.

The sample is deterministic: every test run types the same terms in the same order,
so the results of different versions of the api can be compared.

Usage: python3 generate_resources.py
"""
import json
import random
from pathlib import Path

STRESS_TEST_DIR = Path(__file__).parent
TERM_FILE = STRESS_TEST_DIR.parent / "config" / "localstack" / "init" / "default.jsonl"
SEARCH_TERMS_FILE = STRESS_TEST_DIR / "user-files" / "resources" / "search-terms.tsv"

AMOUNT_OF_TERMS = 5000
SEED = 42


def load_terms() -> list[str]:
    with open(TERM_FILE, encoding="utf-8") as term_file:
        return [json.loads(line)["term"] for line in term_file if line.strip()]


def main():
    terms = load_terms()
    search_terms = random.Random(SEED).sample(terms, AMOUNT_OF_TERMS)

    with open(SEARCH_TERMS_FILE, "w", encoding="utf-8") as search_terms_file:
        search_terms_file.write("term\n")
        search_terms_file.writelines(f"{term}\n" for term in search_terms)

    print(f"{len(search_terms)} of {len(terms)} terms written to {SEARCH_TERMS_FILE}")


if __name__ == "__main__":
    main()
