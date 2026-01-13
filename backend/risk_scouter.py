from llama_index.core import PromptTemplate
from backend.rag_engine import get_index, llm_pro

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
    "Provide a structured analysis with 'Risk Flags' and 'Relevant Past Projects'.\n"
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
    
    return {
        "analysis": response.text,
        "relevant_past_projects": [n.node.metadata.get('file_name', 'Unknown') for n in nodes],
        "risk_flags": [] # In a real app we'd parse the LLM output to extract these structured. For now, rely on text.
    }
