import subprocess

from langgraph.graph import StateGraph, END

from graph.state import QAState

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
        "test_output": result.stdout,
        "test_errors": result.stderr,
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

# ---------------------------
# Compile graph
# ---------------------------

qa_graph = graph.compile()
