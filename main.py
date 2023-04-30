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

openai.api_key = OPENAI_API_KEY


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
    for i, comment in enumerate(comments):
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

    # print(q_and_a_pairs)

    collection.add(
        documents=[json.dumps(pair, indent=2) for pair in q_and_a_pairs],
        ids=[f"pair-{i}" for i, pair in enumerate(q_and_a_pairs)],
    )

    question = "how can i grow a tiktok following for a consumer app?"

    results = collection.query(
        query_texts=[question],
        n_results=2,
        include=["documents"]
        # where={"metadata_field": "is_equal_to_this"}, # optional filter
        # where_document={"$contains":"search_string"}  # optional filter
    )

    # print(
    #     json.dumps(results, indent=2),
    # )

    messages = [
        {
            "role": "system",
            "content": f"You are a mentor with the following intro blurb. You are tasked with answering questions about your expertise. Be as helpful as possible! Be as specific as possible to your own experiences from your intro\n\n intro:\n\n{intro}",
        }
    ]

    for document_str in results["documents"][0]:
        document = json.loads(document_str)
        messages.append({"role": "user", "content": document["question"]})
        messages.append({"role": "assistant", "content": document["answer"]})

    messages.append({"role": "user", "content": question})

    response = get_openai_completion(messages)["message"]["content"]
    print(response)
