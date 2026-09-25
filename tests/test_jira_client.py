from integrations.jira_client import get_issue


def test_get_jira_issue():
    issue = get_issue("ATS-4")

    assert issue.key == "ATS-4"
    assert issue.fields.summary == "User Story: User can log into the application"
    assert issue.fields.description

    print("\nJira connection test completed successfully.")
    print("Issue Key:", issue.key)
    print("Summary:", issue.fields.summary)
    print("Description:", issue.fields.description)