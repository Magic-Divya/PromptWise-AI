def apply_costar(prompt, context="", audience="General audience",
                 tone="Professional", output_format="Structured paragraphs"):

    return f"""
CONTEXT:
{context or "Provide relevant background for the task."}

OBJECTIVE:
{prompt}

STYLE:
Clear, logical and well-organized.

TONE:
{tone}

AUDIENCE:
{audience}

RESPONSE FORMAT:
{output_format}

ADDITIONAL INSTRUCTIONS:
- Address the objective directly.
- Include relevant examples where useful.
- Avoid unsupported claims.
- Keep the response appropriate for the target audience.
""".strip()