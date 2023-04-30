import os


from dotenv import load_dotenv
import openai
import requests
from bs4 import BeautifulSoup

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


URL = "https://realpython.github.io/fake-jobs/"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")
