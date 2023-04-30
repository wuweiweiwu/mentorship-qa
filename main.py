import os
from typing import Dict, List
import time
import json

from dotenv import load_dotenv
import openai
import requests
from bs4 import BeautifulSoup
import streamlit as st
import chromadb

# setup Chroma in-memory, for easy prototyping. Can add persistence easily!
client = chromadb.Client()

# Create collection. get_collection, get_or_create_collection, delete_collection also available!
collection = client.create_collection("all-my-documents")

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def get_openai_completion(
    messages: List[Dict],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0,
):
    while True:
        try:
            # Use chat completion API
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )

            return response.choices[0]
        except openai.error.RateLimitError:
            print(
                "The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again."
            )
            time.sleep(10)  # Wait 10 seconds and try again


if __name__ == "__main__":
    URL = "https://elpha.com/posts/tfveek4e/office-hours-i-am-growth-solopreneur-helping-companies-build-product-led-growth-plg-models-i-m-elena-verna-ama"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    author = soup.find(class_="byline-text").find("a").text.strip()
    # print(author)

    post_body = soup.find(class_="full-post-body")
    intro = ""
    paragraphs = post_body.find_all("p")
    for paragraph in paragraphs:
        # print(paragraph.text.strip())
        intro += paragraph.text.strip() + "\n"

    # print(intro)

    q_and_a_pairs = []

    comments = soup.find_all(class_="comment-nest-container")
    for i, comment in comments:
        question_body = comment.find(
            class_="initial-comment-container", recursive=False
        ).find(class_="full-post-body")
        question = ""
        paragraphs = question_body.find_all("span")
        for paragraph in paragraphs:
            question += paragraph.text.strip() + "\n"

        author_link = comment.find(
            "a", class_="member-img-thumbnail", href=lambda text: author in text
        )

        answer = ""
        if author_link:
            parent = author_link.parent.parent
            answer_body = parent.find(class_="full-post-body")

            paragraphs = question_body.find_all("span")
            for paragraph in paragraphs:
                answer += paragraph.text.strip() + "\n"

        # print("----------QUESTION-------")
        # print(question)

        # print("----------ANSWER-------")
        # print(answer)

        if question and answer:
            q_and_a_pairs.append({"question": question, "answer": answer, "id": i})

        # Add docs to the collection. Can also update and delete. Row-based API coming soon!
        # collection.add(
        #     documents=["This is document1", "This is document2"], # we handle tokenization, embedding, and indexing automatically. You can skip that and add your own embeddings as well
        #     metadatas=[{"source": "notion"}, {"source": "google-docs"}], # filter on these!
        #     ids=["doc1", "doc2"], # unique for each doc
        # )

        # # Query/search 2 most similar results. You can also .get by id
        # results = collection.query(
        #     query_texts=["This is a query document"],
        #     n_results=2,
        #     # where={"metadata_field": "is_equal_to_this"}, # optional filter
        #     # where_document={"$contains":"search_string"}  # optional filter
        # )

        collection.add(
            documents=[json.dump(pair) for pair in q_and_a_pairs],
            ids=[pair.id for pair in q_and_a_pairs],
        )

        results = collection.query(
            query_texts=["What is PLG?"],
            n_results=2,
            # where={"metadata_field": "is_equal_to_this"}, # optional filter
            # where_document={"$contains":"search_string"}  # optional filter
        )

        print(results)
