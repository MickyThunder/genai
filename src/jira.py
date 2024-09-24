import requests
import json

# Jira API URL and authentication details
JIRA_URL = "https://tarundeeptrial.atlassian.net/"
API_ENDPOINT = "/rest/api/2/issue"
USERNAME = "tarundeep.sharma2009@gmail.com"
API_TOKEN = "ATATT3xFfGF06U_iPkDhOe8rg5VnSyZRTHXB4Fp4N3ig2QNSdVFQuo3s9hRc2lOKm8ch30VxdyX44gWOdm9772I7Sf3WDN8a-h1j5gkTQt8bqOvjZ8FZNYz4rZbn_XxW2wov3kdN3UXKtocWnEGHcPVSdQMdm0lA87yhIl6kO6UIAyWSncLaXyM=B32BCECC"

# Function to create a story in Jira
def create_jira_story(project_key, summary, description, issue_type="Story"):
    url = JIRA_URL + API_ENDPOINT
    auth = (USERNAME, API_TOKEN)
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "project": {
                "key": project_key
            },
            "summary": summary,
            "description": description,
            "issuetype": {
                "name": issue_type
            }
        }
    }

    response = requests.post(url, auth=auth, headers=headers, data=json.dumps(payload),verify=False)

    if response.status_code == 201:
        print("Story created successfully.")
        print("Issue key:", response.json()["key"])
    else:
        print("Failed to create story.")
        print("Status code:", response.status_code)
        print("Response:", response.json())

# Example usage
project_key = "FUN"
summary = "Example Story"
description = "This is an example story created via the Jira API."
issue_type = "Story"
create_jira_story(project_key, summary, description,issue_type="Story")