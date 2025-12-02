import os
from dotenv import load_dotenv
import requests
from striprtf.striprtf import rtf_to_text

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(model="gpt-4o", temperature=0)


def extract_rtf_text(url: str) -> str:
    """
    Download an RTF document from the given URL and extract plain text from it.
    """

    response = requests.get(url)
    response.raise_for_status()

    rtf_content = response.content.decode("utf-8", errors="ignore")

    text = rtf_to_text(rtf_content)
    return  text


def summarize_text(text: str) -> str:
    """
    Summarizes the given text using the LLM.
    """
    SUM_PROMPT = """Summarize the following text {text} in one short sentence. Summarize in ukrainian"""

    summarization_prompt = PromptTemplate.from_template(SUM_PROMPT)
    chain = summarization_prompt | model
    response = chain.invoke({"text": text})

    return response

tools = [extract_rtf_text, summarize_text]