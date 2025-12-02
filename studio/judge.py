import os
from dotenv import load_dotenv

import requests
from striprtf.striprtf import rtf_to_text

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from typing import TypedDict
from typing_extensions import Literal

from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.prompts import PromptTemplate


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(model="gpt-4o", temperature=0)


class AgentState(TypedDict):
    url: str
    text: str
    case_type: Literal["Administrative", "Criminal"]
    summary: str


def extract_rtf_text(state: AgentState) -> str:
    """
    Download an RTF document from the given URL and extract plain text from it.
    """

    url = state["url"]
    response = requests.get(url)
    response.raise_for_status()

    rtf_content = response.content.decode("utf-8", errors="ignore")

    text = rtf_to_text(rtf_content)
    return  {"text": text}


def classify_text(state: AgentState) -> dict:
    """Classify input court cases to criminal or administrative"""

    text = state["text"]
    cl_prompt_text = """Classify the text of the following court case {text}. 
    A court case can be either criminal or administrative. Therefore, return only the class."""

    prompt = PromptTemplate.from_template(cl_prompt_text)

    chain = prompt | model

    response = chain.invoke({"text": text})

    # return response.content
    

    if response.content == "Administrative":
        return {"case_type": "Administrative"}
    elif response.content == "Criminal":
        return {"case_type": "Criminal"}
    


def administrative_summarize(text: str) -> str:
    """
    Summary of administrative court cases highlighting the parties to the dispute, the subject matter of the claim, and the decision.
    """
    adm_prompt = """You are helpful analyst of court cases. 
    You must analyze this administrative case {text} and prepare some summary including parties to the dispute, subject matter of the claim, decision. Generate summary into Ukrainian language"""

    summarization_prompt = PromptTemplate.from_template(adm_prompt)
    chain = summarization_prompt | model
    response = chain.invoke({"text": text})

    return {"summary": response.content}


def criminal_summarize(text: str) -> str:
    """
    Summary of criminal court cases highlighting the articles of the Criminal Code, the type of punishment, and the positions of the parties.
    """
    crm_prompt = """You are helpful analyst of court cases. 
    You must analyze this criminal case {text} and prepare some summary including parties to  the articles of the Criminal Code, the type of punishment, and the positions of the parties. Generate summary only into Ukrainian language"""
    
    summarization_prompt = PromptTemplate.from_template(crm_prompt)
    chain = summarization_prompt | model
    response = chain.invoke({"text": text})

    return {"summary": response.content}

def route_by_case_type(state: AgentState) -> str:
    return state["case_type"]

app = StateGraph(AgentState)

app.add_node("extract_rtf_text", extract_rtf_text)
app.add_node("classify_text", classify_text)
app.add_node("Administrative", administrative_summarize)
app.add_node("Criminal", criminal_summarize)

app.add_edge(START, "extract_rtf_text")
app.add_edge("extract_rtf_text", "classify_text")

app.add_conditional_edges(
    "classify_text", 
    route_by_case_type,
    {
        "Administrative": "Administrative",
        "Criminal": "Criminal"
    },
)


app.add_edge("Administrative", END)
app.add_edge("Criminal", END)

graph = app.compile()