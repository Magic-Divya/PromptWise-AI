import re

from src.core.prompt_analyzer import analyze_prompt
from src.frameworks.costar import apply_costar
from src.frameworks.create import apply_create
from src.frameworks.risen import apply_risen
from src.frameworks.rtf import apply_rtf

FRAMEWORKS = [
    "CO-STAR",
    "RISEN",
    "RTF",
    "CREATE",
    "CRISPE",
    "RACE",
    "APE",
    "TAG",
    "CARE",
    "STAR",
    "BAB",
    "Zero-Shot",
    "Few-Shot",
    "Sequential",
    "Self-Check",
    "Structured Output"
]

FRAMEWORK_DESCRIPTIONS = {
    "CO-STAR": "Context, Objective, Style, Tone, Audience and Response.",
    "RISEN": "Role, Instructions, Steps, End goal and Narrowing.",
    "RTF": "Role, Task and Format.",
    "CREATE": "Character, Request, Examples, Adjustments, Type and Extras.",
    "CRISPE": "Capacity, Role, Insight, Statement, Personality and Experiment.",
    "RACE": "Role, Action, Context and Expectation.",
    "APE": "Action, Purpose and Expectation.",
    "TAG": "Task, Action and Goal.",
    "CARE": "Context, Action, Result and Example.",
    "STAR": "Situation, Task, Action and Result.",
    "BAB": "Before, After and Bridge.",
    "Zero-Shot": "Direct instructions without examples.",
    "Few-Shot": "Instructions supported by example input-output pairs.",
    "Sequential": "Break a complex task into ordered stages.",
    "Self-Check": "Ask for a final verification against explicit criteria.",
    "Structured Output": "Specify a predictable output schema and format."
}

def select_framework(prompt, task="General"):
    text = f"{prompt} {task}".lower()

    rules = [
        (["debug", "python", "java", "program", "code", "function"], "RTF"),
        (["workflow", "procedure", "implement", "step by step", "process"], "RISEN"),
        (["story", "creative", "campaign", "brainstorm", "design"], "CREATE"),
        (["json", "schema", "structured data", "csv"], "Structured Output"),
        (["example", "examples", "sample input"], "Few-Shot"),
        (["check", "verify", "review", "validate", "quality"], "Self-Check"),
        (["research", "compare", "analyze", "evaluate", "investigate"], "CO-STAR"),
        (["situation", "case study", "scenario"], "STAR")
    ]

    for keywords, framework in rules:
        if any(word in text for word in keywords):
            return framework

    return "CO-STAR"

def _build_prompt(prompt, framework, task, audience, role,
                  output_format, context, constraints):

    common = f"""
ROLE:
Act as {role or "a knowledgeable AI assistant"}.

TASK:
{task or "Complete the user's requested task."}

USER REQUEST:
{prompt}

CONTEXT:
{context or "Use only the information supplied in the request and relevant general knowledge."}

AUDIENCE:
{audience or "General audience"}

OUTPUT FORMAT:
{output_format or "Clear, structured paragraphs"}

CONSTRAINTS:
{constraints or "Be accurate, relevant, clear and appropriately detailed."}
"""

    templates = {
        "CRISPE": f"""
CAPACITY AND ROLE:
{role}

INSIGHT:
Understand the context and intended outcome before responding.

STATEMENT:
{prompt}

PERSONALITY:
Use a clear and suitable communication style.

EXPERIMENT:
Consider a useful approach and produce the requested output.

{common}
""",
        "RACE": f"""
ROLE: {role}
ACTION: Complete the requested task.
CONTEXT: {context or "Use the supplied task details."}
EXPECTATION: {output_format}

REQUEST:
{prompt}

AUDIENCE: {audience}
CONSTRAINTS: {constraints or "Avoid unsupported claims."}
""",
        "APE": f"""
ACTION:
{task}

PURPOSE:
Explain or achieve the intended result of this request.

EXPECTATION:
{output_format}

INPUT:
{prompt}

CONTEXT:
{context or "No additional context supplied."}

REQUIREMENTS:
{constraints or "Provide a clear and useful response."}
""",
        "TAG": f"""
TASK:
{task}

ACTION:
Act as {role} and complete the requested work.

GOAL:
Deliver {output_format} for {audience}.

INPUT:
{prompt}

CONTEXT:
{context}

CONSTRAINTS:
{constraints or "Keep the result relevant and accurate."}
""",
        "CARE": f"""
CONTEXT:
{context or "Use the task details supplied below."}

ACTION:
{task}

RESULT:
Produce {output_format}.

EXAMPLE:
Include an example when it improves understanding.

REQUEST:
{prompt}

ROLE: {role}
AUDIENCE: {audience}
CONSTRAINTS: {constraints}
""",
        "STAR": f"""
SITUATION:
{context or "Consider the situation described in the request."}

TASK:
{task}

ACTION:
Describe the appropriate approach and actions.

RESULT:
Provide {output_format}.

REQUEST:
{prompt}

ROLE: {role}
AUDIENCE: {audience}
CONSTRAINTS: {constraints}
""",
        "BAB": f"""
BEFORE:
Identify the current problem or starting point from this request:
{prompt}

AFTER:
Describe the desired outcome as {output_format}.

BRIDGE:
Explain the practical steps connecting the current situation to the desired result.

CONTEXT: {context}
ROLE: {role}
AUDIENCE: {audience}
CONSTRAINTS: {constraints}
""",
        "Zero-Shot": f"""
Perform this task directly without relying on examples.

TASK:
{prompt}

ROLE: {role}
CONTEXT: {context}
AUDIENCE: {audience}
OUTPUT: {output_format}
CONSTRAINTS: {constraints}
""",
        "Few-Shot": f"""
TASK:
{prompt}

First, identify the pattern or format demonstrated by the examples supplied by the user.
Then apply that pattern to the requested task.

EXAMPLES:
Use only examples supplied in the context. If none are supplied, ask for examples only when they are essential.

CONTEXT: {context}
ROLE: {role}
OUTPUT FORMAT: {output_format}
CONSTRAINTS: {constraints}
""",
        "Sequential": f"""
Complete the task in the following stages:

1. Understand the request and identify its objective.
2. Identify the relevant context and requirements.
3. Break the work into logical steps.
4. Complete each step.
5. Present the final result.
6. Check the result against the requirements.

REQUEST:
{prompt}

ROLE: {role}
CONTEXT: {context}
OUTPUT FORMAT: {output_format}
CONSTRAINTS: {constraints}
""",
        "Self-Check": f"""
Complete the requested task:
{prompt}

Before presenting the final response, check it against these criteria:
- Does it address the user's actual request?
- Is it complete and logically organized?
- Does it follow the requested format?
- Are unsupported assumptions avoided?
- Are all supplied constraints respected?

Provide the final answer and a concise verification summary.
Do not expose private internal reasoning.

ROLE: {role}
CONTEXT: {context}
OUTPUT FORMAT: {output_format}
CONSTRAINTS: {constraints}
""",
        "Structured Output": f"""
Return the result using this structure:

OBJECTIVE:
State the task objective.

RESULT:
Provide the requested output.

KEY DETAILS:
List important supporting details.

ASSUMPTIONS:
Identify assumptions or missing information.

FINAL CHECK:
Briefly verify that the output follows the requirements.

REQUEST:
{prompt}

ROLE: {role}
CONTEXT: {context}
OUTPUT FORMAT: {output_format}
CONSTRAINTS: {constraints}
"""
    }

    if framework in templates:
        return templates[framework].strip()

    if framework == "CO-STAR":
        return apply_costar(
            prompt,
            context=context,
            audience=audience,
            output_format=output_format
        )

    if framework == "RISEN":
        return apply_risen(
            prompt,
            role=role,
            instructions=f"Complete this {task} task carefully. {constraints}",
            end_goal=f"Produce a {output_format} response."
        )

    if framework == "RTF":
        return apply_rtf(
            prompt,
            role=role,
            task=task,
            output_format=output_format
        )

    if framework == "CREATE":
        return apply_create(
            prompt,
            context=context,
            role=role,
            expectation=output_format,
            audience=audience
        )

    return common.strip()

def optimize_prompt(
    prompt,
    framework="Auto",
    task="General",
    audience="General audience",
    role="AI assistant",
    output_format="Structured paragraphs",
    context="",
    constraints=""
):
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Please enter a prompt before optimizing.")

    selected = framework or "Auto"

    if selected == "Auto":
        selected = select_framework(prompt, task)

    if selected not in FRAMEWORKS:
        raise ValueError(f"Unknown framework: {selected}")

    improved = _build_prompt(
        prompt.strip(),
        selected,
        task,
        audience,
        role,
        output_format,
        context,
        constraints
    )

    analysis = analyze_prompt(improved)

    return {
        "original_prompt": prompt.strip(),
        "improved_prompt": improved,
        "framework": selected,
        "analysis": analysis,
        "original_analysis": analyze_prompt(prompt.strip()),
        "improvement_notes": [
            "Added a defined role and task.",
            "Organized the request using the selected framework.",
            "Included context, audience and output expectations.",
            "Added explicit constraints and quality checks."
        ]
    }
