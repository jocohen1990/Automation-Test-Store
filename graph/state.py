from typing import Required, TypedDict


class QAState(TypedDict, total=False):
    issue_key: Required[str]   # always provided when the run starts
    requirements: str
    generated_tests: str
    reviewed_tests: str
    review_decision: str   # "APPROVED" | "REJECTED"
    review_feedback: str   # reviewer's fix list, sent back to the generator
    review_attempts: int   # number of review rounds so far
    test_cases_file: str   # where approved test cases were saved

    error: str             # set when a step can't continue (e.g., Jira fetch failed)
    
    test_status: str
    test_exit_code: int
    test_output: str
    test_errors: str
    
    failure_analysis: str
    defect_decision: str # "create" | "skip" | "investigate"
    jira_defect: str
   