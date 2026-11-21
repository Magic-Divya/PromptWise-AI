from src.core.framework_selector import select_framework

from src.frameworks.costar import apply_costar
from src.frameworks.risen import apply_risen
from src.frameworks.rtf import apply_rtf
from src.frameworks.create import apply_create


def optimize_prompt(
    prompt,
    framework="Auto",
    task="General",
    audience="General audience",
    output_format="Structured paragraphs",
    context="",
    role="AI assistant"
):
    """Optimize a prompt using the selected framework."""

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    selected = framework

    if framework == "Auto":
        selected = select_framework(prompt, task)

    if selected == "CO-STAR":
        result = apply_costar(
            prompt,
            context=context,
            audience=audience,
            output_format=output_format
        )

    elif selected == "RISEN":
        result = apply_risen(
            prompt,
            role=role,
            instructions=f"Complete this {task} task carefully.",
            end_goal=f"Produce a {output_format} response."
        )

    elif selected == "RTF":
        result = apply_rtf(
            prompt,
            role=role,
            task=task,
            output_format=output_format
        )

    elif selected == "CREATE":
        result = apply_create(
            prompt,
            context=context,
            role=role,
            expectation=output_format,
            audience=audience
        )

    else:
        raise ValueError(f"Unknown framework: {selected}")

    return {
        "original_prompt": prompt,
        "improved_prompt": result,
        "framework": selected
    }