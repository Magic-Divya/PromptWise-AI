import re

def _tokens(text):
    return set(
        re.findall(r"\b[a-zA-Z0-9]{3,}\b", (text or "").lower())
    )

def evaluate_response(response, prompt):
    response = (response or "").strip()
    prompt = (prompt or "").strip()

    if not response or not prompt:
        return {
            "Relevance": 0,
            "Completeness": 0,
            "Clarity": 0,
            "Structure": 0,
            "Instruction Coverage": 0
        }

    prompt_words = _tokens(prompt)
    response_words = _tokens(response)

    overlap = len(prompt_words & response_words)
    relevance = round(100 * overlap / max(1, len(prompt_words)))
    relevance = min(100, relevance)

    word_count = len(response.split())
    completeness = min(100, round(word_count / max(30, len(prompt.split()) * 3) * 100))

    sentences = [
        s for s in re.split(r"[.!?]+", response)
        if s.strip()
    ]

    average_sentence_length = (
        word_count / max(1, len(sentences))
    )

    clarity = 100
    if average_sentence_length > 30:
        clarity -= 20
    if average_sentence_length > 45:
        clarity -= 20
    if word_count < 8:
        clarity -= 35
    clarity = max(0, clarity)

    has_structure = bool(
        re.search(r"(^|\n)\s*(#{1,6}\s|[-*]\s|\d+[.)]\s)", response)
    )
    structure = 90 if has_structure else 65
    if len(sentences) >= 3:
        structure = min(100, structure + 10)

    instruction_terms = {
        "include", "explain", "compare", "summarize",
        "list", "describe", "analyze", "create",
        "provide", "format", "example", "steps"
    }

    requested = prompt_words & instruction_terms
    followed = response_words & requested

    coverage = (
        round(100 * len(followed) / len(requested))
        if requested else 70
    )

    return {
        "Relevance": relevance,
        "Completeness": completeness,
        "Clarity": clarity,
        "Structure": structure,
        "Instruction Coverage": coverage
    }
