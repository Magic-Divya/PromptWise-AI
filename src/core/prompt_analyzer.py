import re

def analyze_prompt(prompt):
    prompt = prompt or ""
    words = re.findall(r"\b[\w'-]+\b", prompt)
    word_count = len(words)

    requirements = {
        "Role specified": bool(
            re.search(r"\b(act as|role:|you are|character:)\b", prompt, re.I)
        ),
        "Context provided": bool(
            re.search(r"\b(context|background|scenario|situation)\b", prompt, re.I)
        ),
        "Task specified": word_count >= 5,
        "Output format specified": bool(
            re.search(r"\b(format|table|bullet|json|paragraph|output|structure)\b",
                      prompt, re.I)
        ),
        "Constraints specified": bool(
            re.search(r"\b(must|should|avoid|limit|only|include|constraint|requirement)\b",
                      prompt, re.I)
        ),
        "Audience identified": bool(
            re.search(r"\b(audience|reader|user|student|developer|customer)\b",
                      prompt, re.I)
        ),
        "Success criteria included": bool(
            re.search(r"\b(success criteria|quality criteria|verify|validate|check)\b",
                      prompt, re.I)
        )
    }

    score = round(sum(requirements.values()) / len(requirements) * 100)

    suggestions = []

    for name, present in requirements.items():
        if not present:
            suggestions.append(f"Consider adding: {name.lower()}.")

    if word_count < 8:
        suggestions.append("Add more detail to make the task and expected outcome clearer.")

    if word_count > 500:
        suggestions.append("Consider dividing this long prompt into smaller sections.")

    return {
        "word_count": word_count,
        "character_count": len(prompt),
        "requirements": requirements,
        "quality_indicator": score,
        "suggestions": suggestions,
        "assessment_note": (
            "This is a rule-based completeness indicator, not a measure of factual accuracy."
        )
    }
