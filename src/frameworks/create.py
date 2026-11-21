def apply_create(prompt, context="", role="AI assistant",
                 expectation="A clear and useful answer",
                 audience="General audience",
                 tone="Professional"):

    return f"""
CHARACTER:
Act as {role}.

REQUEST:
{prompt}

EXAMPLES:
Use relevant examples when they improve understanding.
Do not invent examples that could mislead the reader.

ADJUSTMENTS:
Consider the following context:
{context or "No additional context supplied."}

TYPE OF OUTPUT:
{expectation}

EXTRAS:
Audience: {audience}
Tone: {tone}

Produce a useful, organized and relevant response.
""".strip()