from llama_index.core import PromptTemplate
from backend.rag_engine import get_index, llm_pro

import json
import re

RISK_PROMPT_TMPL = (
    "You are an expert construction project manager and risk analyst suitable for 'The Foreman' system.\n"
    "We are evaluating a new project described below:\n"
    "---------------------\n"
    "{project_description}\n"
    "---------------------\n"
    "Based on the following historical project documents and lessons learned:\n"
    "{context_str}\n"
    "---------------------\n"
    "Identify potential budget or design risks for this new project. "
    "Highlight specific 'pain points' from past projects that might reoccur. "
    "Provide the output as a valid JSON object with the following structure:\n"
    "{{\n"
    "  \"analysis\": \"<Detailed markdown analysis here>\",\n"
    "  \"risk_flags\": [\"<Short risk title 1>\", \"<Short risk title 2>\"]\n"
    "}}\n"
)

def analyze_risk(project_description: str, top_k: int = 5):
    index = get_index()
    # Use Pro embedding/retrieval is same, but we use Pro LLM for reasoning
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(project_description)
    
    context_str = "\n\n".join([n.node.get_content() for n in nodes])
    
    fmt_prompt = RISK_PROMPT_TMPL.format(
        project_description=project_description,
        context_str=context_str
    )
    
    # Use Gemini 3 Pro for the complex analysis
    response = llm_pro.complete(fmt_prompt)
    
    # Parse JSON
    cleaned_text = response.text.strip()
    # Remove markdown code blocks if present
    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[7:]
    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text[3:]
    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]
        
    try:
        data = json.loads(cleaned_text)
        analysis_text = data.get("analysis", response.text)
        risk_flags = data.get("risk_flags", [])
    except json.JSONDecodeError:
        # Fallback
        analysis_text = response.text
        risk_flags = ["Error parsing structured risk data"]

    return {
        "analysis": analysis_text,
        "relevant_past_projects": [n.node.metadata.get('file_name', 'Unknown') for n in nodes],
        "risk_flags": risk_flags
    }
