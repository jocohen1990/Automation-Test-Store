from typing import TypedDict


class QAState(TypedDict):
    issue_key: str
    requirements: str
    test_cases: list
    test_results: str
    failure_analysis: str
    jira_defect: str
    review: str