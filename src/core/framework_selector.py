def select_framework(prompt, task="General"):
    """
    Select a suitable prompting framework using transparent
    keyword-based rules. This is a heuristic selector.
    """

    text = f"{prompt} {task}".lower()

    if any(word in text for word in [
        "analyze", "analysis", "evaluate", "compare",
        "research", "investigate"
    ]):
        return "CO-STAR"

    if any(word in text for word in [
        "step by step", "procedure", "process",
        "workflow", "implement", "develop"
    ]):
        return "RISEN"

    if any(word in text for word in [
        "code", "program", "python", "java",
        "function", "debug"
    ]):
        return "RTF"

    if any(word in text for word in [
        "creative", "story", "campaign", "design",
        "brainstorm", "idea"
    ]):
        return "CREATE"

    return "CO-STAR"