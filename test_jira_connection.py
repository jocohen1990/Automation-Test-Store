from integrations.jira_client import get_issue


print("Starting Jira connection test...")
issue = get_issue("ATS-4")

print("Jira connection test completed successfully.")
print("Issue Key:", issue.key)
print("Summary:", issue.fields.summary)
print("Description:", issue.fields.description)