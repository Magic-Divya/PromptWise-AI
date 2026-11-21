def apply_risen(prompt, role="AI assistant", instructions="",
                steps="Explain the task in logical steps",
                end_goal="Deliver a complete answer"):

    return f"""
ROLE:
Act as {role}.

INSTRUCTIONS:
{instructions or "Understand the task and follow the requirements carefully."}

STEPS:
{steps}

END GOAL:
{end_goal}

TASK:
{prompt}

REQUIREMENTS:
- Be clear and accurate.
- Organize the response logically.
- Identify uncertainty instead of inventing information.
""".strip()