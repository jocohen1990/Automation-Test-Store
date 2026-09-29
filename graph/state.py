from typing import TypedDict


class QAState(TypedDict, total=False):
    issue_key: str
    requirements: str
    generated_tests: str
    reviewed_tests: str
    
    test_status: str
    test_exit_code: int
    test_output: str
    test_errors: str
    
    failure_analysis: str
    defect_decision: str # "create" | "skip" | "investigate"
    jira_defect: str
   