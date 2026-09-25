import os
# from integrations.jira_client import get_issue
from jira import JIRA
# from typing import Any

from dotenv import load_dotenv


def get_jira_client():
    load_dotenv()

    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_api_token = os.getenv("JIRA_API_TOKEN")

    if jira_url is None or jira_email is None or jira_api_token is None:
        raise RuntimeError(
            "JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be set in the environment."
        )

    return JIRA(
        server=jira_url,
        basic_auth=(jira_email, jira_api_token),
    )


def get_issue(issue_key: str, fields: str | list[str] | None = None):
    client = get_jira_client()
    jira_fields = ",".join(fields) if isinstance(fields, list) else fields
    return client.issue(issue_key, fields=jira_fields)


# def create_issue(
#     project: str,
#     summary: str,
#     description: str = "",
#     issue_type: str = "Task",
#     **extra_fields: Any,
# ):
#     client = get_jira_client()
#     payload = {
#         "project": project,
#         "summary": summary,
#         "description": description,
#         "issuetype": {"name": issue_type},
#         **extra_fields,
#     }
#     return client.create_issue(**payload)


# def add_comment(issue_key: str, body: str):
#     client = get_jira_client()
#     return client.add_comment(issue_key, body)


# def transition_issue(issue_key: str, transition: str, **kwargs: Any):
#     client = get_jira_client()
#     return client.transition_issue(issue_key, transition, **kwargs)


#__all__ = [
    #"get_jira_client",
    #"get_issue",
    # "create_issue",
    # "add_comment",
    # "transition_issue",
# ]
