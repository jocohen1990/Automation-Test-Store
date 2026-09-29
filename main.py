from langchain_core.runnables.config import RunnableConfig
from langgraph.types import Command

from graph.qa_graph import qa_graph


def main():
    issue_key = input("Jira issue key (e.g., ATS-4): ").strip()

    # The thread_id lets the graph pause and resume the same run
    config: RunnableConfig | None = {"configurable": {"thread_id": f"{issue_key}-run-1"}}

    result = qa_graph.invoke({"issue_key": issue_key}, config)

    # The graph pauses at human_review when a test fails
    if "__interrupt__" in result:
        print("\n--- Failure Analysis ---")
        print(result["__interrupt__"][0].value["failure_analysis"])

        choice = ""
        while choice not in ("create", "skip", "investigate"):
            choice = input("\nCreate Jira defect? (create / skip / investigate): ").strip().lower()

        result = qa_graph.invoke(Command(resume=choice), config)

    # The run can end early: Jira fetch failed, or test cases were never approved
    if result.get("error"):
        print("\nStopped:", result["error"])
        return

    print("\nReview decision:", result.get("review_decision"),
          f"(after {result.get('review_attempts', 0)} review round(s))")

    if result.get("review_decision") != "APPROVED":
        print("\nTest cases were not approved. Last review:\n")
        print(result.get("reviewed_tests", ""))
        return

    print("Approved test cases saved to:", result.get("test_cases_file"))
    print("\nTest status:", result.get("test_status"))
    print("Defect decision:", result.get("defect_decision", "n/a"))
    print("Jira defect:", result.get("jira_defect", "none created"))


if __name__ == "__main__":
    main()
