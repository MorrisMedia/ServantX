import re
from typing import Dict, List, Optional

import asyncio
from core_services.openai_service import chat_with_openai_async, chat_with_openai_async_tracked
from services.cost_service import log_ai_cost
from services.web_research_service import search_legal_web_context


def _keyword_tokens(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-zA-Z]{3,}", text.lower()) if token not in {"the", "and", "for", "with"}]


def _select_relevant_contract_snippets(contract_text: str, question: str, limit: int = 8) -> List[str]:
    lines = [re.sub(r"\s+", " ", line).strip(" \t-:") for line in contract_text.splitlines()]
    lines = [line for line in lines if len(line) >= 20]
    if not lines:
        return []

    tokens = set(_keyword_tokens(question))
    scored = []
    for line in lines:
        line_lower = line.lower()
        score = 0
        for token in tokens:
            if token in line_lower:
                score += 2
        if any(keyword in line_lower for keyword in ["payment", "rate", "reimbursement", "term", "net", "invoice", "underpayment"]):
            score += 1
        scored.append((score, line))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [line for score, line in scored if score > 0][:limit]
    if selected:
        return selected
    return lines[:limit]


def _format_history(history: Optional[List[Dict[str, str]]]) -> str:
    if not history:
        return "No previous conversation context."
    messages = []
    for item in history[-10:]:
        role = item.get("role", "user").upper()
        content = (item.get("content") or "").strip()
        if not content:
            continue
        messages.append(f"{role}: {content}")
    return "\n".join(messages) if messages else "No previous conversation context."


def _fallback_answer(question: str, contract_snippets: List[str], web_results: List[Dict[str, str]], used_web: bool) -> Dict:
    if contract_snippets:
        answer = (
            "OpenAI is currently unavailable, so this is a fallback summary based on contract text. "
            f"Relevant contract excerpt: \"{contract_snippets[0]}\""
        )
    else:
        answer = (
            "OpenAI is currently unavailable and no clear contract excerpt was found for your question. "
            "Try asking with a more specific clause, term, date, or payment keyword."
        )

    sources = [
        {
            "sourceType": "contract",
            "title": f"Contract Excerpt {idx + 1}",
            "url": None,
            "snippet": snippet,
        }
        for idx, snippet in enumerate(contract_snippets[:4])
    ]
    if used_web:
        sources.extend(
            {
                "sourceType": "web",
                "title": item.get("title") or "Web result",
                "url": item.get("url"),
                "snippet": item.get("snippet") or "",
            }
            for item in web_results[:4]
        )

    return {
        "answer": answer,
        "usedWeb": used_web and len(web_results) > 0,
        "sources": sources,
        "disclaimer": "For informational purposes only and not legal advice.",
    }


async def generate_contract_chat_response(
    *,
    contract_name: str,
    contract_text: str,
    question: str,
    include_web: bool = False,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict:
    question = (question or "").strip()
    if not question:
        return {
            "answer": "Please provide a question.",
            "usedWeb": False,
            "sources": [],
            "disclaimer": "For informational purposes only and not legal advice.",
        }

    contract_snippets = _select_relevant_contract_snippets(contract_text, question, limit=8)
    web_results = search_legal_web_context(question, max_results=5) if include_web else []
    conversation = _format_history(history)

    system_prompt = """You are a contract analysis assistant for healthcare billing teams.
Your job is to answer questions using the provided contract excerpts first, and optionally supplemental web snippets.
Rules:
- Prioritize contract terms over web snippets.
- If contract text does not support a claim, say that explicitly.
- Be concise, actionable, and cite evidence snippets.
- If web snippets are included, treat them as general context and identify them as external context.
- Never present legal conclusions as definitive legal advice.
- End with this sentence exactly: "This is not legal advice."
Output plain text only."""

    contract_evidence = "\n".join(f"- {snippet}" for snippet in contract_snippets) if contract_snippets else "- No relevant contract snippets found."
    web_evidence = (
        "\n".join(
            f"- [{item.get('title')}] {item.get('snippet')} ({item.get('url')})"
            for item in web_results
        )
        if web_results
        else "- No web research was requested."
    )

    user_prompt = f"""Contract Name: {contract_name}

Conversation History:
{conversation}

User Question:
{question}

Relevant Contract Excerpts:
{contract_evidence}

Optional Web Context:
{web_evidence}

Answer with:
1) Direct answer.
2) "Contract evidence:" bullet list.
3) If web context used, "External context:" bullet list.
4) Any uncertainty or missing clause notes.
5) End with the required legal disclaimer sentence."""

    output_text, usage = await chat_with_openai_async_tracked(
        text=user_prompt,
        prompt=system_prompt,
        model="gpt-4o-mini",
    )
    asyncio.ensure_future(log_ai_cost(
        service="contract_chat",
        provider="openai",
        model="gpt-4o-mini",
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        latency_ms=usage.get("latency_ms"),
        success=bool(output_text),
    ))

    if not output_text:
        return _fallback_answer(question, contract_snippets, web_results, include_web)

    sources = [
        {
            "sourceType": "contract",
            "title": f"Contract Excerpt {idx + 1}",
            "url": None,
            "snippet": snippet,
        }
        for idx, snippet in enumerate(contract_snippets[:5])
    ]
    if include_web:
        sources.extend(
            {
                "sourceType": "web",
                "title": item.get("title") or "Web result",
                "url": item.get("url"),
                "snippet": item.get("snippet") or "",
            }
            for item in web_results[:5]
        )

    if not output_text.strip().endswith("This is not legal advice."):
        output_text = f"{output_text.strip()}\n\nThis is not legal advice."

    return {
        "answer": output_text,
        "usedWeb": include_web and len(web_results) > 0,
        "sources": sources,
        "disclaimer": "For informational purposes only and not legal advice.",
    }
