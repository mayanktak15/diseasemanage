import requests
from typing import Iterable, Optional

from .config import (
    GEMINI_API_KEY,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    MAX_CONTEXT_CHARS
)
from .types import Document
from .prompts import SYSTEM_INSTRUCTION, RAG_PROMPT_TEMPLATE
from .fallback import rule_based_response, best_faq_block


def build_response(query: str, symptoms: Optional[str], docs: Iterable[Document]) -> str:
    # 1. Check rule-based overrides immediately (fast, zero dependency)
    rule_res = rule_based_response(query)
    if rule_res:
        return rule_res

    doc_list = list(docs)
    context = _join_docs(doc_list)
    symptoms_sec = f"\nUser Symptoms: {symptoms}" if symptoms else ""

    # Determine provider stack based on environment
    if GEMINI_API_KEY:
        try:
            return _call_gemini(query, context, symptoms_sec)
        except Exception:
            pass  # Fall through on failure

    # Try Ollama if configured and accessible
    try:
        return _call_ollama(query, context, symptoms_sec)
    except Exception:
        pass  # Fall through on failure

    # Fallback to local high-fidelity retrieval format (Zero Local LLM mode)
    if doc_list:
        best_doc = doc_list[0].content
        answer_text = best_doc
        
        # Format the output matching target style
        additional = "If symptoms are severe or persistent, please submit a consultation form."
        if symptoms:
            additional = f"Noted symptoms: {symptoms}. Please submit a consultation form for certified doctor review."

        return (
            f"**Answer**: {answer_text}\n"
            f"**Additional Info**: {additional}"
        )

    # Hard fallback if no document is matched
    faq_fb = best_faq_block(query)
    if faq_fb:
        return (
            f"**Answer**: {faq_fb}\n"
            f"**Additional Info**: General Guidance only."
        )

    return (
        "**Answer**: I'm here to help with questions about Docify Online and general health guidance.\n"
        "**Additional Info**: Please ask about consultations, certificates, or common health concerns. "
        "If you are feeling unwell, register and submit a consultation form."
    )


def _join_docs(docs: list[Document]) -> str:
    chunks: list[str] = []
    remaining = MAX_CONTEXT_CHARS
    for doc in docs:
        if remaining <= 0:
            break
        content = doc.content.strip()
        if not content:
            continue
        if len(content) > remaining:
            content = content[:remaining].rstrip() + "..."
        chunks.append(content)
        remaining -= len(content)
    return "\n\n".join(chunks)


def _call_gemini(query: str, context: str, symptoms_section: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    
    prompt = RAG_PROMPT_TEMPLATE.format(
        context=context,
        question=query,
        symptoms_section=symptoms_section
    )
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_INSTRUCTION
    )
    
    response = model.generate_content(prompt)
    if response and response.text:
        return response.text.strip()
    raise RuntimeError("Empty response from Gemini API")


def _call_ollama(query: str, context: str, symptoms_section: str) -> str:
    prompt = RAG_PROMPT_TEMPLATE.format(
        context=context,
        question=query,
        symptoms_section=symptoms_section
    )
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": SYSTEM_INSTRUCTION,
        "stream": False
    }
    
    url = f"{OLLAMA_BASE_URL}/api/generate"
    resp = requests.post(url, json=payload, timeout=5)
    resp.raise_for_status()
    
    result = resp.json()
    response_text = result.get("response")
    if response_text:
        return response_text.strip()
    raise RuntimeError("Empty response from Ollama")
