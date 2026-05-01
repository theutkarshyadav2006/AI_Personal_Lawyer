import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# Ensure the API key is picked up from environment variables
# You must have GROQ_API_KEY set in your .env or system environment

def get_llm():
    # Ensure environment variables are loaded
    import os
    from dotenv import load_dotenv
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    load_dotenv(os.path.join(basedir, '.env'), override=True)
    
    api_key = os.getenv("GROQ_API_KEY")
    
    # We use llama-3.3-70b-versatile
    return ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.0,
        api_key=api_key
    )

import json

def analyze_legal_case(case_text):
    """
    Uses Groq LLM to analyze a given legal case text and returns a JSON object.
    """
    llm = get_llm()
    
    template = """
    You are an expert Indian Legal Advisor AI. 
    A user has provided the following legal situation or incident:
    
    "{case}"
    
    You MUST output your response strictly as valid JSON with the exact structure below. Do not include any other text, markdown formatting, or introductory phrases.
    
    {{
      "summary": "A brief summary of the incident.",
      "key_issues": ["Issue 1", "Issue 2"],
      "relevant_laws": [
        {{"law": "Section XYZ", "description": "What this law means."}}
      ],
      "potential_outcome": "What is likely to happen.",
      "recommended_steps": ["Step 1", "Step 2"]
    }}
    """
    
    prompt = PromptTemplate(
        input_variables=["case"],
        template=template
    )
    
    chain = prompt | llm
    
    response = chain.invoke({"case": case_text})
    
    # Clean up the response in case the LLM wrapped it in markdown code blocks
    content = response.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    try:
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        # Fallback if parsing fails
        return {
            "summary": "Error parsing LLM response.",
            "key_issues": [],
            "relevant_laws": [],
            "potential_outcome": "Error: Could not retrieve valid JSON from AI.",
            "recommended_steps": []
        }

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def analyze_document_text(document_text, filename="document"):
    """
    Specifically designed to analyze extracted text from an uploaded legal document.
    Returns a detailed JSON with summary, issues, laws, outcome, and strategy.
    """
    llm = get_llm()

    template = """
You are a senior Indian Legal Advisor AI. A user has uploaded a legal document named "{filename}".
The following text was extracted from the document:

--- DOCUMENT START ---
{document_text}
--- DOCUMENT END ---

Carefully read the entire document and provide a comprehensive legal analysis.
You MUST respond ONLY with valid JSON — no extra text, no markdown, no code blocks.

{{
  "summary": "A detailed 3-5 sentence plain-English summary of what this document is about and its key contents.",
  "document_type": "What type of document this is (e.g. FIR, Legal Notice, Contract, Court Order, Affidavit, etc.)",
  "key_issues": [
    "List each important legal issue, right, or obligation identified in the document"
  ],
  "relevant_laws": [
    {{"law": "IPC Section 420", "description": "Covers cheating and dishonestly inducing delivery of property."}}
  ],
  "potential_outcome": "What is the likely legal outcome or consequence of this document and the underlying dispute.",
  "recommended_steps": [
    "Step 1: What the affected party should do first",
    "Step 2: What legal remedies are available",
    "Step 3: What documents to gather",
    "Step 4: Whether to approach police, consumer forum, civil court, or high court"
  ],
  "urgency": "High / Medium / Low — how urgent is it to act on this document",
  "rights": "What are the legal rights of the person who uploaded this document in this situation"
}}
"""

    prompt = PromptTemplate(
        input_variables=["filename", "document_text"],
        template=template
    )

    chain = prompt | llm
    response = chain.invoke({"filename": filename, "document_text": document_text})

    content = response.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "summary": content,
            "document_type": "Unknown",
            "key_issues": [],
            "relevant_laws": [],
            "potential_outcome": "Could not parse structured response.",
            "recommended_steps": ["Please consult a lawyer directly."],
            "urgency": "Unknown",
            "rights": "Please consult a qualified lawyer for your rights."
        }



def chat_with_legal_bot(question, history=[]):
    """
    Uses Groq LLM to act as a conversational legal chatbot, remembering past messages.
    Returns a parsed JSON dictionary.
    """
    llm = get_llm()
    
    # Convert our simple dict history into Langchain message objects
    formatted_history = []
    for msg in history:
        if msg["role"] == "user":
            # User messages are just strings
            formatted_history.append(HumanMessage(content=msg["content"]))
        else:
            # AI messages are dictionaries (from our parsed JSON), so we convert them back to strings for context
            content_str = json.dumps(msg["content"]) if isinstance(msg["content"], dict) else msg["content"]
            formatted_history.append(AIMessage(content=content_str))
            
    system_instruction = """
    You are a helpful, professional AI Legal Assistant.
    Provide a clear, accurate, and easy-to-understand answer. 
    If the question is about Indian law, provide the relevant sections or context.
    
    You MUST output your response strictly as valid JSON with the exact structure below. Do not include any other text or markdown formatting.
    
    {{
      "answer": "The main explanation or answer to the user's question, written in natural language.",
      "relevant_sections": ["IPC Section 420", "IT Act Section 66"],
      "disclaimer": "Standard disclaimer that this is not formal legal advice."
    }}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "history": formatted_history,
        "question": question
    })
    
    # Clean up the response in case the LLM wrapped it in markdown code blocks
    content = response.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    try:
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        # Fallback if parsing fails
        return {
            "answer": content,
            "relevant_sections": [],
            "disclaimer": "This is for informational purposes only and is not formal legal advice."
        }
