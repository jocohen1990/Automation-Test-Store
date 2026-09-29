import subprocess
import sys
from pathlib import Path

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver


from graph.state import QAState

from agents.agent_runner import run_agent, extract_json
from integrations.jira_client import get_jira_client, create_defect

# How many times the reviewer can reject test cases before the run stops
MAX_REVIEW_ROUNDS = 2

# Only app tests run here. test_jira_client.py and test_openai.py check API
# connections, not the app, so their failures must not become app defects.
APP_TESTS = ["tests/test_login.py"]

TEST_CASES_DIR = Path("test_cases")


# ---------------------------
# Helpers
# ---------------------------

def build_story_text(issue) -> str:
    """Turn a Jira issue into plain text for the Requirements Agent."""
    fields = issue.fields
    names = issue.raw.get("names", {})  # custom field id -> display name

    lines = [
        f"Issue key: {issue.key}",
        f"Summary: {fields.summary}",
        f"Issue type: {fields.issuetype.name}",
        f"Status: {fields.status.name}",
        f"Priority: {getattr(fields.priority, 'name', 'None')}",
        f"Labels: {', '.join(fields.labels) or 'None'}",
        "",
        "Description:",
        fields.description or "(empty)",
    ]

    # Text custom fields, e.g. an "Acceptance Criteria" field
    for field_id, value in issue.raw["fields"].items():
        if field_id.startswith("customfield_") and isinstance(value, str) and value.strip():
            lines += ["", f"{names.get(field_id, field_id)}:", value]

    attachments = getattr(fields, "attachment", None) or []
    if attachments:
        lines += ["", "Attachments: " + ", ".join(a.filename for a in attachments)]

    comments = getattr(getattr(fields, "comment", None), "comments", None) or []
    if comments:
        lines += ["", "Comments:"]
        lines += [f"- {c.author.displayName}: {c.body}" for c in comments]

    return "\n".join(lines)


# ---------------------------
# Node functions
# ---------------------------

def requirements_agent(state: QAState):
    issue_key = state["issue_key"]

    try:
        issue = get_jira_client().issue(issue_key, expand="names")
    except Exception as exc:
        # The Requirements Agent must not guess the story, so stop here
        return {"error": f"Could not fetch Jira issue {issue_key}: {exc}"}

    requirements = run_agent("requirements_agent", build_story_text(issue))
    return {"requirements": requirements}


def test_generator(state: QAState):
    prompt = "Structured requirements:\n" + state.get("requirements", "")

    # Revision Mode: send the previous tests and the reviewer's feedback
    if state.get("review_feedback"):
        prompt += (
            "\n\nPrevious test cases:\n" + state.get("generated_tests", "")
            + "\n\nReviewer feedback:\n" + state.get("review_feedback", "")
        )

    return {"generated_tests": run_agent("test_generator_agent", prompt)}


def test_reviewer(state: QAState):
    prompt = (
        "Structured requirements:\n" + state.get("requirements", "")
        + "\n\nGenerated test cases:\n" + state.get("generated_tests", "")
    )
    review = run_agent("test_reviewer_agent", prompt)

    review_json = extract_json(review) or {}
    decision = str(review_json.get("decision", "")).upper()
    if decision not in ("APPROVED", "REJECTED"):
        # Fall back to the Markdown summary; anything unclear counts as REJECTED
        decision = "APPROVED" if "Decision: APPROVED" in review else "REJECTED"

    feedback = "\n".join(review_json.get("feedback_for_generator", [])) or review

    update = {
        "reviewed_tests": review,
        "review_decision": decision,
        "review_feedback": feedback,
        "review_attempts": state.get("review_attempts", 0) + 1,
    }

    # Save approved test cases for the human to automate
    if decision == "APPROVED":
        TEST_CASES_DIR.mkdir(exist_ok=True)
        path = TEST_CASES_DIR / f"{state['issue_key']}_test_cases.md"
        path.write_text(state.get("generated_tests", ""), encoding="utf-8")
        update["test_cases_file"] = str(path)

    return update


def run_playwright_tests(state: QAState):
    print(f"\nRunning app tests for {state.get('issue_key')}: {', '.join(APP_TESTS)}")

    result = subprocess.run(
        # sys.executable = the Python in your active venv
        # --tb=short -rf = short tracebacks plus a summary of failed tests
        [sys.executable, "-m", "pytest", *APP_TESTS, "--tb=short", "-rf"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        test_status = "PASSED"
    else:
        test_status = "FAILED"

    return {
        "test_status": test_status,
        "test_exit_code": result.returncode,
        "test_output": result.stdout,
        "test_errors": result.stderr,
    }


def failure_analysis_agent(state: QAState):
    prompt = (
        "Failed test results (pytest output):\n" + state.get("test_output", "")
        + "\n\nErrors (stderr):\n" + (state.get("test_errors") or "(none)")
    )
    return {"failure_analysis": run_agent("failure_analysis_agent", prompt)}


def human_review(state: QAState):
    # Pauses the graph so a human can review the failure analysis.
    # Keep this node to just the interrupt: it reruns from the top on resume.
    decision = interrupt({
        "failure_analysis": state.get("failure_analysis", ""),
        "question": "Create Jira defect? (create / skip / investigate)",
    })
    return {"defect_decision": decision}


# ---------------------------
# Routing functions
# ---------------------------

def route_after_requirements(state: QAState):
    # Stop if the Jira story couldn't be fetched
    return END if state.get("error") else "test_generator"


def route_after_test_review(state: QAState):
    if state.get("review_decision") == "APPROVED":
        return "run_playwright_tests"
    if state.get("review_attempts", 0) < MAX_REVIEW_ROUNDS:
        return "test_generator"   # send back with the reviewer's feedback
    return END                    # still rejected after max rounds


def route_after_tests(state: QAState):
    # Only failed runs go to failure analysis; passing runs end here.
    return "failure_analysis_agent" if state.get("test_status") == "FAILED" else END


def route_after_review(state: QAState):
    # A Jira defect is only created when the human chose "create".
    return "jira_defect_node" if state.get("defect_decision") == "create" else END


def jira_defect_node(state: QAState):
    # Create a defect in Jira using the provided state information
    failure_analysis = state.get("failure_analysis", "")
    
    defect = create_defect(
        project="ATS",
        summary=f"Automated test failure for {state.get('issue_key', 'unknown issue')}",
        description=failure_analysis
    )
    
    return {
        "jira_defect": defect.key
    }
    
    
# ---------------------------
# Build the graph
# ---------------------------

# Create the LangGraph instance rather than importing asyncio.graph.
graph = StateGraph(QAState)

# Add nodes
graph.add_node(
    "requirements_agent", 
    requirements_agent
)

graph.add_node(
    "test_generator",
    test_generator
)

graph.add_node(
    "test_reviewer",
    test_reviewer
)

graph.add_node(
    "run_playwright_tests",
    run_playwright_tests
)

graph.add_node(
    "failure_analysis_agent",
    failure_analysis_agent
)

graph.add_node(
    "human_review",
    human_review
)

graph.add_node(
    "jira_defect_node",
    jira_defect_node
)


# ---------------------------
# Connect nodes
# ---------------------------

graph.set_entry_point("requirements_agent")

graph.add_conditional_edges(
    "requirements_agent",
    route_after_requirements
)

graph.add_edge(
    "test_generator",
    "test_reviewer"
)

graph.add_conditional_edges(
    "test_reviewer",
    route_after_test_review
)

graph.add_conditional_edges(
    "run_playwright_tests",
    route_after_tests
)

graph.add_edge(
    "failure_analysis_agent",
    "human_review"
)

graph.add_conditional_edges(
    "human_review",
    route_after_review
)

graph.add_edge(
    "jira_defect_node",
    END
)

# ---------------------------
# Compile graph
# ---------------------------

# interrupt() requires a checkpointer to save state while paused
qa_graph = graph.compile(checkpointer=InMemorySaver())
