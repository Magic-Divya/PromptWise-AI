
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import StringIO

from src.database import (
    init_db,
    create_user,
    verify_user,
    save_prompt,
    list_prompts,
    delete_prompt,
    get_stats,
)
from src.engine import optimize_prompt, analyze_prompt, FRAMEWORKS
from src.evaluation import evaluate_response
from src.ai import generate_response


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PromptWise AI",
    page_icon="PW",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

init_db()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "user": None,
    "optimized_result": None,
    "generated_response": "",
    "evaluation_result": None,
    "last_prompt": "",
    "workflow": None,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# DARK THEME
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 10% 0%, #17213b 0%, transparent 28%),
            radial-gradient(circle at 90% 10%, #25163a 0%, transparent 25%),
            #090d18;
        color: #edf1ff;
    }

    [data-testid="stSidebar"] {
        background: #0d1424;
        border-right: 1px solid #26334c;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    h1, h2, h3 {
        color: #f3f5ff !important;
        font-weight: 750 !important;
    }

    p, label, li {
        color: #b8c2d9;
    }

    .hero {
        padding: 30px;
        border-radius: 22px;
        background: linear-gradient(120deg, #172747, #252044, #18213a);
        border: 1px solid #38466b;
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 36px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 8px;
    }

    .hero-subtitle {
        color: #c0cbea;
        font-size: 15px;
    }

    .eyebrow {
        color: #a78bfa;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .metric-card {
        background: linear-gradient(145deg, #151f34, #111827);
        border: 1px solid #2b3a56;
        border-radius: 17px;
        padding: 20px;
        min-height: 120px;
    }

    .metric-label {
        color: #9eacc8;
        font-size: 13px;
        margin-bottom: 10px;
    }

    .metric-value {
        color: #ffffff;
        font-size: 30px;
        font-weight: 800;
    }

    .metric-caption {
        color: #8b9ab8;
        font-size: 12px;
        margin-top: 5px;
    }

    .section-card {
        background: #111a2b;
        border: 1px solid #2a3852;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 16px;
    }

    .small-muted {
        color: #91a0bd;
        font-size: 13px;
    }

    .success-panel {
        background: #102b27;
        border: 1px solid #236c5b;
        padding: 15px;
        border-radius: 12px;
    }

    .info-panel {
        background: #17233c;
        border: 1px solid #344c78;
        padding: 15px;
        border-radius: 12px;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"],
    .stNumberInput input {
        background: #101a2b !important;
        color: #f4f6ff !important;
        border-color: #34435f !important;
        border-radius: 10px !important;
    }

    .stButton button {
        border-radius: 10px;
        font-weight: 650;
        border: 1px solid #475c88;
        transition: 0.2s ease;
    }

    .stButton button[kind="primary"] {
        background: linear-gradient(90deg, #6757dc, #8b5cf6);
        color: white;
        border: none;
    }

    .stButton button:hover {
        border-color: #a78bfa;
        transform: translateY(-1px);
    }

    div[data-testid="stMetric"] {
        background: #131d30;
        padding: 15px;
        border: 1px solid #2b3a56;
        border-radius: 14px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        background: #121c2e;
        border-radius: 9px;
        padding: 10px 18px;
    }

    hr {
        border-color: #293750;
    }

    code {
        color: #c4b5fd !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_text(value, default=""):
    if value is None:
        return default
    return str(value)


def get_user_id():
    user = st.session_state.get("user")
    if not user:
        return None
    return user.get("id")


def get_history():
    user_id = get_user_id()
    if user_id is None:
        return []

    try:
        records = list_prompts(user_id)
        return [dict(item) for item in records]
    except Exception:
        return []


def get_prompt_count():
    user_id = get_user_id()
    if user_id is None:
        return 0

    try:
        stats = get_stats(user_id)
        if isinstance(stats, dict):
            return int(stats.get("prompts", 0))
        return 0
    except Exception:
        return 0


def metric_card(label, value, caption):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_hero(title, subtitle, eyebrow="PROMPTWISE AI"):
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">{eyebrow}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_frameworks():
    return [str(item) for item in FRAMEWORKS]


def save_current_prompt(original, optimized, framework):
    user_id = get_user_id()
    if user_id is None:
        return

    try:
        save_prompt(user_id, original, optimized, framework)
    except Exception as exc:
        st.warning(f"Prompt was optimized, but history could not be saved: {exc}")


# ============================================================
# AUTHENTICATION SCREEN
# ============================================================

def authentication_screen():

    st.markdown("<br><br>", unsafe_allow_html=True)

    left, right = st.columns([1.15, 1])

    with left:
        st.markdown(
            """
            <div style="padding:35px 15px;">
                <div class="eyebrow">YOUR INTELLIGENT PROMPT WORKSPACE</div>
                <div style="font-size:48px;font-weight:850;color:white;">
                    PromptWise <span style="color:#a78bfa;">AI</span>
                </div>
                <div style="font-size:18px;color:#bac7e2;margin-top:15px;">
                    Turn ordinary instructions into structured,
                    effective and measurable prompts.
                </div>
                <br>
                <div class="section-card">
                    <h3>01 / Adaptive Prompt Engineering</h3>
                    <p>Explore 16 prompt frameworks and select a suitable structure.</p>
                </div>
                <div class="section-card">
                    <h3>02 / Prompt Evaluation</h3>
                    <p>Review response quality indicators and instruction coverage.</p>
                </div>
                <div class="section-card">
                    <h3>03 / Personal Workspace</h3>
                    <p>Save, revisit, compare and export your prompt experiments.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div style="background:#111a2b;border:1px solid #34435f;
                        border-radius:20px;padding:25px;">
            """,
            unsafe_allow_html=True,
        )

        login_tab, register_tab = st.tabs(["Sign In", "Create Account"])

        with login_tab:
            st.subheader("Welcome back")
            st.caption("Sign in to continue to your workspace.")

            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")

                submitted = st.form_submit_button(
                    "Sign In",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:
                    if not username.strip() or not password:
                        st.error("Please enter both username and password.")
                    else:
                        try:
                            user = verify_user(username.strip(), password)

                            if user:
                                st.session_state.user = dict(user)
                                st.session_state.optimized_result = None
                                st.success("Login successful. Welcome!")
                                st.rerun()
                            else:
                                st.error("Incorrect username or password.")
                        except Exception as exc:
                            st.error(f"Unable to sign in: {exc}")

        with register_tab:
            st.subheader("Create your account")
            st.caption("Register to access your personal PromptWise workspace.")

            with st.form("register_form"):
                display_name = st.text_input("Full name")
                new_username = st.text_input("Choose a username")
                email = st.text_input("Email address (optional)")
                new_password = st.text_input(
                    "Create password",
                    type="password",
                )
                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                )

                submitted = st.form_submit_button(
                    "Create Account",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:
                    if not all([
                        display_name.strip(),
                        new_username.strip(),
                        new_password,
                        confirm_password,
                    ]):
                        st.error("Please complete all required fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            ok, message = create_user(
                                display_name.strip(),
                                new_username.strip(),
                                email.strip(),
                                new_password,
                            )

                            if ok:
                                st.success(message)
                                st.info("Your account is ready. Sign in using your new credentials.")
                            else:
                                st.error(message)
                        except Exception as exc:
                            st.error(f"Registration failed: {exc}")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<p style='text-align:center;color:#71809e;'>"
        "PromptWise AI | Adaptive Prompt Engineering and Response Evaluation"
        "</p>",
        unsafe_allow_html=True,
    )


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():

    user = st.session_state.user

    with st.sidebar:
        st.markdown(
            """
            <div style="padding:12px 4px 20px;">
                <div style="font-size:26px;font-weight:850;color:white;">
                    PromptWise <span style="color:#a78bfa;">AI</span>
                </div>
                <div class="small-muted">Intelligent Prompt Workspace</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        st.markdown("**WORKSPACE**")

        pages = [
            "Overview",
            "Prompt Studio",
            "Framework Library",
            "AI Model Lab",
            "Evaluation Lab",
            "Workflow Builder",
            "Knowledge Assistant",
            "Prompt History",
            "Learning Center",
            "Settings",
        ]

        selected = st.radio(
            "Navigation",
            pages,
            label_visibility="collapsed",
        )

        st.markdown("---")

        st.markdown("**SIGNED IN AS**")
        st.write(safe_text(user.get("display_name"), user.get("username", "User")))
        st.caption("@" + safe_text(user.get("username")))

        st.markdown("---")

        if st.button("Log Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown(
            """
            <div style="padding-top:20px;color:#71809e;font-size:11px;">
                PROMPTWISE AI<br>
                Adaptive Prompt Engineering<br>
                Project Workspace
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected


# ============================================================
# OVERVIEW DASHBOARD
# ============================================================

def overview_page():

    user = st.session_state.user
    history = get_history()
    count = get_prompt_count()

    show_hero(
        f"Welcome, {safe_text(user.get('display_name'), 'User')}",
        "Your personal workspace for creating, improving and evaluating prompts.",
        "YOUR WORKSPACE",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("PROMPTS CREATED", count, "Saved in your history")

    with col2:
        metric_card("FRAMEWORKS", len(FRAMEWORKS), "Available techniques")

    with col3:
        metric_card("WORKSPACE", "Active", "Account status")

    with col4:
        metric_card("AI MODES", "2", "Demo and local Ollama")

    st.markdown("## Quick Actions")

    a, b, c = st.columns(3)

    with a:
        st.markdown(
            """
            <div class="section-card">
                <h3>Prompt Studio</h3>
                <p>Create and optimize prompts with structured frameworks.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Prompt Studio", use_container_width=True):
            st.session_state.quick_navigation = "Prompt Studio"
            st.rerun()

    with b:
        st.markdown(
            """
            <div class="section-card">
                <h3>Evaluation Lab</h3>
                <p>Evaluate generated responses using quality indicators.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Evaluation Lab", use_container_width=True):
            st.session_state.quick_navigation = "Evaluation Lab"
            st.rerun()

    with c:
        st.markdown(
            """
            <div class="section-card">
                <h3>Framework Library</h3>
                <p>Explore prompt engineering frameworks and techniques.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Explore Frameworks", use_container_width=True):
            st.session_state.quick_navigation = "Framework Library"
            st.rerun()

    st.markdown("## Recent Activity")

    if history:
        recent = history[:5]

        rows = []
        for item in recent:
            rows.append({
                "Framework": item.get("framework", "Unknown"),
                "Created": item.get("created_at", ""),
                "Original prompt": safe_text(item.get("original"))[:90],
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No saved prompts yet. Start by creating your first prompt in Prompt Studio.")


# ============================================================
# PROMPT STUDIO
# ============================================================

def prompt_studio_page():

    show_hero(
        "Prompt Studio",
        "Transform a basic instruction into a structured, optimized prompt.",
        "CREATE / OPTIMIZE / IMPROVE",
    )

    frameworks = ["Auto"] + normalize_frameworks()

    with st.container(border=True):
        st.subheader("1. Describe your task")

        prompt = st.text_area(
            "Your original prompt",
            placeholder="Example: Explain machine learning to a beginner.",
            height=150,
            key="studio_prompt",
        )

        c1, c2 = st.columns(2)

        with c1:
            framework = st.selectbox(
                "Prompt framework",
                frameworks,
                index=0,
            )

            task = st.selectbox(
                "Task category",
                [
                    "General",
                    "Academic",
                    "Research",
                    "Programming",
                    "Creative Writing",
                    "Business",
                    "Data Analysis",
                    "Education",
                    "Problem Solving",
                ],
            )

            role = st.text_input(
                "AI role",
                value="Expert AI assistant",
            )

        with c2:
            audience = st.selectbox(
                "Target audience",
                [
                    "General audience",
                    "Beginner",
                    "Student",
                    "Researcher",
                    "Developer",
                    "Professional",
                    "Technical audience",
                ],
            )

            output_format = st.selectbox(
                "Expected output",
                [
                    "Structured paragraphs",
                    "Bullet points",
                    "Step-by-step guide",
                    "Table",
                    "JSON",
                    "Code",
                    "Report",
                    "Presentation outline",
                ],
            )

            context = st.text_area(
                "Additional context",
                placeholder="Add background information...",
                height=90,
            )

        constraints = st.text_area(
            "Constraints and requirements",
            placeholder="Example: Use simple language, include examples, avoid unnecessary jargon...",
            height=90,
        )

        optimize_clicked = st.button(
            "Optimize My Prompt",
            type="primary",
            use_container_width=True,
        )

    if optimize_clicked:
        if not prompt.strip():
            st.error("Enter a prompt before optimizing.")
        else:
            with st.spinner("Analyzing your prompt and building an improved version..."):
                try:
                    result = optimize_prompt(
                        prompt.strip(),
                        framework,
                        task,
                        audience,
                        role,
                        output_format,
                        context,
                        constraints,
                    )

                    st.session_state.optimized_result = result
                    st.session_state.last_prompt = prompt.strip()

                    save_current_prompt(
                        prompt.strip(),
                        result.get("improved_prompt", ""),
                        result.get("framework", framework),
                    )

                    st.success("Your prompt has been optimized and saved to history.")

                except Exception as exc:
                    st.error(f"Optimization failed: {exc}")

    result = st.session_state.get("optimized_result")

    if result:
        st.markdown("---")
        st.markdown("## 2. Optimization Results")

        st.info(
            "Selected framework: "
            + safe_text(result.get("framework", "Not specified"))
        )

        original_col, improved_col = st.columns(2)

        with original_col:
            st.markdown("### Original Prompt")
            st.text_area(
                "Original",
                value=safe_text(result.get("original_prompt")),
                height=260,
                disabled=True,
                key="original_result_display",
            )

        with improved_col:
            st.markdown("### Improved Prompt")
            st.text_area(
                "Improved",
                value=safe_text(result.get("improved_prompt")),
                height=260,
                key="improved_result_display",
            )

            st.download_button(
                "Download Improved Prompt",
                data=safe_text(result.get("improved_prompt")),
                file_name="promptwise_optimized_prompt.txt",
                mime="text/plain",
                use_container_width=True,
            )

        analysis = result.get("analysis", {})
        if not isinstance(analysis, dict):
            analysis = {}

        st.markdown("### Prompt Analysis")

        quality = analysis.get("quality_indicator", 0)

        if isinstance(quality, (int, float)):
            st.metric("Prompt completeness indicator", f"{quality:.0f}%")
            st.progress(max(0.0, min(float(quality) / 100, 1.0)))

        requirements = analysis.get("requirements", {})

        if isinstance(requirements, dict) and requirements:
            st.markdown("**Detected requirements**")
            req_cols = st.columns(3)

            for index, (name, value) in enumerate(requirements.items()):
                with req_cols[index % 3]:
                    st.write(f"**{name.replace('_', ' ').title()}**")
                    st.write("Detected" if value else "Not detected")

        suggestions = analysis.get("suggestions", [])

        if suggestions:
            st.markdown("**Suggestions for further improvement**")
            for suggestion in suggestions:
                st.write("- " + str(suggestion))

        notes = result.get("improvement_notes", [])
        if notes:
            st.markdown("**Optimization notes**")
            for note in notes:
                st.write("- " + str(note))


# ============================================================
# FRAMEWORK LIBRARY
# ============================================================

FRAMEWORK_DETAILS = {
    "CO-STAR": ("Context, Objective, Style, Tone, Audience, Response", "Useful for detailed, well-contextualized instructions."),
    "RISEN": ("Role, Instructions, Steps, End Goal, Narrowing", "Useful for structured tasks and processes."),
    "RTF": ("Role, Task, Format", "A simple framework for direct and clear instructions."),
    "CREATE": ("Character, Request, Examples, Adjustments, Type, Extras", "Useful for creative and customized outputs."),
    "CRISPE": ("Capacity, Role, Insight, Statement, Personality, Experiment", "Useful for defining AI behavior and response style."),
    "RACE": ("Role, Action, Context, Expectation", "Useful for concise task specifications."),
    "APE": ("Action, Purpose, Expectation", "Useful for outcome-focused instructions."),
    "TAG": ("Task, Action, Goal", "Useful for short, goal-oriented prompts."),
    "CARE": ("Context, Action, Result, Example", "Useful for contextual problem solving."),
    "STAR": ("Situation, Task, Action, Result", "Useful for scenario-based prompts."),
    "BAB": ("Before, After, Bridge", "Useful for explaining transformations and improvements."),
    "Zero-Shot": ("Instruction without examples", "Useful when the task is clear and examples are unnecessary."),
    "Few-Shot": ("Instruction with examples", "Useful when examples help establish a pattern."),
    "Sequential": ("A task broken into ordered stages", "Useful for multi-step tasks."),
    "Self-Check": ("Instruction plus verification criteria", "Useful for encouraging a response to check its own requirements."),
    "Structured Output": ("Explicit schema and output requirements", "Useful for JSON, tables and consistent formats."),
}


def framework_library_page():

    show_hero(
        "Framework Library",
        "Explore the prompt engineering techniques available in PromptWise AI.",
        "16 STRUCTURED TECHNIQUES",
    )

    search = st.text_input(
        "Search frameworks",
        placeholder="Search by name or technique...",
    )

    selected_frameworks = normalize_frameworks()

    if search.strip():
        selected_frameworks = [
            name for name in selected_frameworks
            if search.lower() in name.lower()
            or search.lower() in FRAMEWORK_DETAILS.get(name, ("", ""))[0].lower()
            or search.lower() in FRAMEWORK_DETAILS.get(name, ("", ""))[1].lower()
        ]

    st.caption(f"{len(selected_frameworks)} framework(s) found")

    cols = st.columns(2)

    for index, name in enumerate(selected_frameworks):
        meaning, purpose = FRAMEWORK_DETAILS.get(
            name,
            ("Structured prompt technique", "Use for relevant tasks."),
        )

        with cols[index % 2]:
            with st.container(border=True):
                st.subheader(name)
                st.write(f"**Structure:** {meaning}")
                st.write(purpose)

                if st.button(
                    f"Use {name}",
                    key=f"use_framework_{name}",
                    use_container_width=True,
                ):
                    st.session_state.selected_framework = name
                    st.session_state.quick_navigation = "Prompt Studio"
                    st.rerun()


# ============================================================
# AI MODEL LAB
# ============================================================

def ai_model_lab_page():

    show_hero(
        "AI Model Lab",
        "Generate responses from your prompts using the available response modes.",
        "MODEL EXPERIMENTATION",
    )

    st.info(
        "Demo mode uses a template-based demonstration. "
        "For actual local language-model generation, use Ollama with a model installed and running."
    )

    mode = st.radio(
        "Generation mode",
        ["Demo", "Ollama"],
        horizontal=True,
    )

    model = "llama3.2"

    if mode == "Ollama":
        model = st.text_input(
            "Ollama model name",
            value="llama3.2",
        )

    prompt_source = st.radio(
        "Prompt source",
        ["Use optimized prompt", "Enter a new prompt"],
        horizontal=True,
    )

    if prompt_source == "Use optimized prompt":
        result = st.session_state.get("optimized_result")
        if result:
            prompt = safe_text(result.get("improved_prompt"))
            st.text_area(
                "Prompt to generate from",
                value=prompt,
                height=170,
                disabled=True,
            )
        else:
            prompt = ""
            st.warning("Optimize a prompt in Prompt Studio first.")
    else:
        prompt = st.text_area(
            "Enter your prompt",
            height=170,
            placeholder="Write the instruction for the model...",
        )

    if st.button("Generate Response", type="primary", use_container_width=True):
        if not prompt.strip():
            st.error("Please provide a prompt.")
        else:
            with st.spinner("Generating response..."):
                try:
                    answer, source, error = generate_response(
                        prompt,
                        mode,
                        model,
                    )

                    if error:
                        st.error(str(error))
                    else:
                        st.session_state.generated_response = safe_text(answer)
                        st.session_state.generated_source = safe_text(source)
                        st.success("Response generated.")

                except Exception as exc:
                    st.error(f"Generation failed: {exc}")

    if st.session_state.get("generated_response"):
        st.markdown("## Generated Response")

        st.caption(
            "Generation source: "
            + safe_text(st.session_state.get("generated_source", "Unknown"))
        )

        st.text_area(
            "Response",
            value=st.session_state.generated_response,
            height=300,
        )

        st.download_button(
            "Download Response",
            data=st.session_state.generated_response,
            file_name="promptwise_response.txt",
            mime="text/plain",
        )


# ============================================================
# EVALUATION LAB
# ============================================================

def evaluation_lab_page():

    show_hero(
        "Evaluation Lab",
        "Measure response quality using PromptWise AI's heuristic evaluation indicators.",
        "ANALYZE / COMPARE / IMPROVE",
    )

    st.info(
        "These scores are heuristic indicators based on text and instruction matching. "
        "They are not proof of factual accuracy or a substitute for human evaluation."
    )

    result = st.session_state.get("optimized_result")

    default_prompt = (
        safe_text(result.get("improved_prompt"))
        if result else ""
    )

    default_response = st.session_state.get("generated_response", "")

    prompt = st.text_area(
        "Evaluation prompt",
        value=default_prompt,
        height=150,
        key="evaluation_prompt",
    )

    response = st.text_area(
        "AI response",
        value=default_response,
        height=220,
        key="evaluation_response",
    )

    if st.button(
        "Evaluate Response",
        type="primary",
        use_container_width=True,
    ):
        if not prompt.strip() or not response.strip():
            st.error("Both prompt and response are required.")
        else:
            try:
                scores = evaluate_response(response, prompt)
                st.session_state.evaluation_result = scores
                st.success("Evaluation completed.")
            except Exception as exc:
                st.error(f"Evaluation failed: {exc}")

    scores = st.session_state.get("evaluation_result")

    if scores:
        st.markdown("---")
        st.markdown("## Evaluation Results")

        score_items = [
            (name, value)
            for name, value in scores.items()
            if isinstance(value, (int, float))
        ]

        if score_items:
            cols = st.columns(len(score_items))

            for index, (name, value) in enumerate(score_items):
                with cols[index]:
                    st.metric(name, f"{value:.0f}/100")
                    st.progress(max(0.0, min(float(value) / 100, 1.0)))

            chart_df = pd.DataFrame(
                score_items,
                columns=["Evaluation metric", "Score"],
            )

            fig = px.bar(
                chart_df,
                x="Evaluation metric",
                y="Score",
                range_y=[0, 100],
                title="Response Quality Indicators",
            )

            fig.update_layout(
                paper_bgcolor="#111a2b",
                plot_bgcolor="#111a2b",
                font_color="#edf1ff",
                yaxis_gridcolor="#293750",
            )

            st.plotly_chart(fig, use_container_width=True)

            st.download_button(
                "Download Evaluation Report",
                data=pd.DataFrame(
                    score_items,
                    columns=["Metric", "Score"],
                ).to_csv(index=False),
                file_name="promptwise_evaluation.csv",
                mime="text/csv",
            )


# ============================================================
# WORKFLOW BUILDER
# ============================================================

def workflow_builder_page():

    show_hero(
        "Workflow Builder",
        "Break a complex task into clear prompt engineering stages.",
        "PLAN / STRUCTURE / EXECUTE",
    )

    task = st.text_area(
        "Describe your workflow goal",
        placeholder="Example: Build a research workflow for analyzing renewable energy trends.",
        height=130,
    )

    workflow_type = st.selectbox(
        "Workflow type",
        [
            "Research workflow",
            "Content creation workflow",
            "Programming workflow",
            "Data analysis workflow",
            "Academic workflow",
            "Business workflow",
        ],
    )

    if st.button("Build Workflow", type="primary", use_container_width=True):
        if not task.strip():
            st.error("Describe the task first.")
        else:
            steps = [
                ("Understand the objective", "Identify the expected outcome and scope."),
                ("Gather context", "Collect the relevant background information and requirements."),
                ("Plan the approach", "Break the goal into manageable stages."),
                ("Execute each stage", "Create a focused prompt for each individual task."),
                ("Review the results", "Check relevance, completeness, clarity and instruction coverage."),
                ("Refine the workflow", "Improve prompts based on the evaluation results."),
            ]

            st.session_state.workflow = {
                "goal": task,
                "type": workflow_type,
                "steps": steps,
            }

            st.success("Workflow structure created.")

    workflow = st.session_state.get("workflow")

    if workflow:
        st.markdown("---")
        st.subheader(workflow["type"])
        st.write("**Goal:** " + workflow["goal"])

        for index, (title, description) in enumerate(workflow["steps"], start=1):
            with st.container(border=True):
                st.markdown(f"### Step {index}: {title}")
                st.write(description)

        workflow_text = "\n".join(
            f"{i}. {title}\n{description}"
            for i, (title, description) in enumerate(workflow["steps"], start=1)
        )

        st.download_button(
            "Download Workflow",
            data=workflow_text,
            file_name="promptwise_workflow.txt",
            mime="text/plain",
        )


# ============================================================
# KNOWLEDGE ASSISTANT
# ============================================================

def knowledge_assistant_page():

    show_hero(
        "Knowledge Assistant",
        "Upload a text-based reference document and search its contents.",
        "DOCUMENT-BASED KNOWLEDGE SEARCH",
    )

    st.info(
        "This module performs simple text matching over uploaded content. "
        "It is not a vector database or a full retrieval-augmented generation system."
    )

    uploaded_file = st.file_uploader(
        "Upload a TXT, MD or CSV file",
        type=["txt", "md", "csv"],
    )

    if uploaded_file:
        try:
            document_text = uploaded_file.getvalue().decode(
                "utf-8",
                errors="replace",
            )

            st.session_state.knowledge_document = document_text
            st.session_state.knowledge_filename = uploaded_file.name

            st.success(f"Loaded: {uploaded_file.name}")

        except Exception as exc:
            st.error(f"Could not read the document: {exc}")

    document = st.session_state.get("knowledge_document", "")

    if document:
        st.caption(
            "Current document: "
            + safe_text(st.session_state.get("knowledge_filename"))
        )

        question = st.text_input(
            "Search your document",
            placeholder="Enter keywords or a question...",
        )

        if st.button("Search Document", type="primary"):
            if not question.strip():
                st.error("Enter a search query.")
            else:
                terms = [
                    term.lower()
                    for term in question.split()
                    if len(term) > 2
                ]

                paragraphs = [
                    part.strip()
                    for part in document.replace("\r", "").split("\n")
                    if part.strip()
                ]

                matches = []

                for paragraph in paragraphs:
                    score = sum(
                        1 for term in terms
                        if term in paragraph.lower()
                    )

                    if score:
                        matches.append((score, paragraph))

                matches.sort(key=lambda item: item[0], reverse=True)

                if matches:
                    st.markdown("### Matching content")

                    for score, paragraph in matches[:8]:
                        with st.container(border=True):
                            st.caption(f"Keyword matches: {score}")
                            st.write(paragraph)
                else:
                    st.warning("No matching text was found.")

        with st.expander("Preview uploaded document"):
            st.text(document[:5000])


# ============================================================
# PROMPT HISTORY
# ============================================================

def prompt_history_page():

    show_hero(
        "Prompt History",
        "Review your saved prompt experiments and export your work.",
        "YOUR PERSONAL PROMPT ARCHIVE",
    )

    history = get_history()

    if not history:
        st.info("Your history is empty. Optimize a prompt to create your first record.")
        return

    st.write(f"**Total saved prompts:** {len(history)}")

    table_rows = []

    for item in history:
        table_rows.append({
            "ID": item.get("id", ""),
            "Framework": item.get("framework", ""),
            "Created": item.get("created_at", ""),
            "Original": safe_text(item.get("original"))[:100],
            "Optimized": safe_text(item.get("optimized"))[:100],
        })

    df = pd.DataFrame(table_rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Export History as CSV",
        data=df.to_csv(index=False),
        file_name="promptwise_history.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("View or delete a saved prompt")

    for index, item in enumerate(history):
        prompt_id = item.get("id")

        title = (
            safe_text(item.get("framework"), "Prompt")
            + " | "
            + safe_text(item.get("created_at"), "Date unavailable")
        )

        with st.expander(title):
            st.markdown("**Original prompt**")
            st.write(safe_text(item.get("original")))

            st.markdown("**Optimized prompt**")
            st.text_area(
                "Saved optimized prompt",
                value=safe_text(item.get("optimized")),
                height=150,
                disabled=True,
                key=f"history_prompt_{index}",
            )

            st.download_button(
                "Download this prompt",
                data=safe_text(item.get("optimized")),
                file_name=f"promptwise_prompt_{prompt_id}.txt",
                mime="text/plain",
                key=f"history_download_{index}",
            )

            if st.button(
                "Delete this record",
                key=f"history_delete_{index}",
            ):
                try:
                    delete_prompt(get_user_id(), prompt_id)
                    st.success("History record deleted.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not delete this record: {exc}")


# ============================================================
# LEARNING CENTER
# ============================================================

def learning_center_page():

    show_hero(
        "Learning Center",
        "Learn the foundations of prompt engineering and effective AI instructions.",
        "LEARN / EXPERIMENT / IMPROVE",
    )

    lessons = [
        (
            "What is Prompt Engineering?",
            "Prompt engineering is the practice of designing and refining instructions "
            "to guide an AI system toward a useful response.",
        ),
        (
            "Why use frameworks?",
            "Frameworks provide a repeatable structure for specifying roles, context, "
            "tasks, constraints and expected outputs.",
        ),
        (
            "Zero-Shot Prompting",
            "Give the model a clear instruction without supplying examples.",
        ),
        (
            "Few-Shot Prompting",
            "Provide examples to demonstrate the expected response pattern.",
        ),
        (
            "Role-Based Prompting",
            "Specify a role or perspective to establish the intended response context.",
        ),
        (
            "Structured Output",
            "Describe the required format, such as a table, JSON object or numbered list.",
        ),
        (
            "Prompt Evaluation",
            "Review whether a response is relevant, complete, clear and aligned with the prompt.",
        ),
        (
            "Iterative Refinement",
            "Improve a prompt through repeated testing, evaluation and adjustment.",
        ),
    ]

    for title, description in lessons:
        with st.expander(title):
            st.write(description)

    st.markdown("---")
    st.subheader("Prompt Engineering Checklist")

    checklist = [
        "The task is clearly defined.",
        "The AI role is appropriate.",
        "Relevant context is provided.",
        "The target audience is specified.",
        "The output format is clear.",
        "Constraints and requirements are included.",
        "The expected result can be evaluated.",
    ]

    for item in checklist:
        st.checkbox(item, key=f"learning_{item}")


# ============================================================
# SETTINGS
# ============================================================

def settings_page():

    show_hero(
        "Settings",
        "Manage your workspace preferences and account information.",
        "WORKSPACE CONFIGURATION",
    )

    user = st.session_state.user

    st.subheader("Account Information")

    st.text_input(
        "Display name",
        value=safe_text(user.get("display_name")),
        disabled=True,
    )

    st.text_input(
        "Username",
        value=safe_text(user.get("username")),
        disabled=True,
    )

    st.text_input(
        "Email",
        value=safe_text(user.get("email")),
        disabled=True,
    )

    st.markdown("---")
    st.subheader("Application Information")

    st.write("**Application:** PromptWise AI")
    st.write("**Project:** A Framework for Adaptive Prompt Engineering and AI Response Evaluation")
    st.write("**Frameworks:** 16")
    st.write("**Database:** SQLite")
    st.write("**Interface:** Streamlit")
    st.write("**Theme:** Dark")

    st.markdown("---")
    st.subheader("Data and Privacy")

    st.write(
        "Your account and saved prompts are stored in the application's local "
        "SQLite database. Keep your project folder secure, especially when it "
        "contains account records."
    )

    if st.button("Log Out", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ============================================================
# MAIN APPLICATION ROUTER
# ============================================================

def main():

    if not st.session_state.user:
        authentication_screen()
        return

    page = render_sidebar()

    # Support navigation from dashboard and framework cards.
    quick_navigation = st.session_state.pop("quick_navigation", None)

    if quick_navigation:
        page = quick_navigation

    if page == "Overview":
        overview_page()

    elif page == "Prompt Studio":
        prompt_studio_page()

    elif page == "Framework Library":
        framework_library_page()

    elif page == "AI Model Lab":
        ai_model_lab_page()

    elif page == "Evaluation Lab":
        evaluation_lab_page()

    elif page == "Workflow Builder":
        workflow_builder_page()

    elif page == "Knowledge Assistant":
        knowledge_assistant_page()

    elif page == "Prompt History":
        prompt_history_page()

    elif page == "Learning Center":
        learning_center_page()

    elif page == "Settings":
        settings_page()

    st.markdown("---")

    st.markdown(
        """
        <div style="text-align:center;color:#71809e;font-size:12px;padding:10px;">
            PromptWise AI | Adaptive Prompt Engineering and AI Response Evaluation
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
