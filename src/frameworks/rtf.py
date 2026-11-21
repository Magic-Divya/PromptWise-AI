def apply_rtf(prompt, role="AI assistant",
              task="Complete the requested task",
              output_format="Structured paragraphs"):

    return f"""
ROLE:
Act as {role}.

TASK:
{task}

INPUT:
{prompt}

FORMAT:
{output_format}

Follow the requested task and produce the output in the specified format.
""".strip()