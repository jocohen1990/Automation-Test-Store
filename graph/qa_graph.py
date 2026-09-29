import subprocess

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver


from graph.state import QAState

from integrations.jira_client import get_jira_client, get_issue, create_defect

# ---------------------------
# Node functions
# ---------------------------

def requirements_agent(state):
    # Requirements Agent logic
    return state

def test_generator(state):
    # Test Generator logic
    return state

def test_reviewer(state):
    # Test Reviewer logic
    return state

def run_playwright_tests(state):
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/"],
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
    "jira_defect_node",
    jira_defect_node
)


# ---------------------------
# Connect nodes
# ---------------------------

graph.set_entry_point("requirements_agent")

graph.add_edge(
    "requirements_agent", 
    "test_generator"
)

graph.add_edge(
    "test_generator",
    "test_reviewer"
)

graph.add_edge(
    "test_reviewer",
    "run_playwright_tests"
)

graph.add_edge(
    "run_playwright_tests",
    END
)

graph.add_edge(
    "jira_defect",
    END
)

# ---------------------------
# Compile graph
# ---------------------------

qa_graph = graph.compile()
