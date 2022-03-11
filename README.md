# Univ-SearchEngine

Is a text indexer and search engine with evaluation methods. The indexer implements a SPIMI algorithm with linguistic processing (tokenizer, stemming, etc.) and scoring/ranking methods (TF-IFD, bm25).

## File to process

<https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2020-12-01/metadata.csv>

## Contains

    A SPIMI algorithm with:

    - The capability of indexing any combination of title and abstract.
    - Linguistic processing:
        - Tokenizer
        - Minimum length filtering
        - Stop word filtering
        - Stemming
    - scoring / ranking methods:
        - TF-IDF
        - BM25 with k1 = 1.2 b = 0.75

    A search engine that uses:
        - TF-IFD or BM25

    Methods to evaluate the retrieval using the queries and relevance scores.

## Instructions of use

    1. Create a folder named "Index" inside the file called "Files".
    2. Run the "search_engine.py" file.

    Note: The simple tockenizer was design to the part 1 not for the actions 8 and 10.
