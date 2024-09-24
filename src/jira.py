import requests
import json
import urllib3
import streamlit as st
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Jira API URL and authentication details
JIRA_URL = "https://tarundeeptrial.atlassian.net"
API_ENDPOINT = "/rest/api/2/issue"
USERNAME = "tarundeep.sharma2009@gmail.com"
API_TOKEN = "ATATT3xFfGF0f4KxMXInWccouRk-avst9DrdFla32YoowRV-NDZnYDDCLa4gGYEqbudncl25RThmQS53k2pmHiSgdqZD1sbTehWyXHuYzRZcEfxjXhjRnCOLklc7Ict8J9f34FrD9mA6y4EP8aNpl3FBsvwIqh7GCPKQ9yvqPnV4ANVab9AirHo=A69C4BD8"

# Function to create a story in Jira
def create_jira_story(project_key, summary, description, issue_type="Story"):
    url = JIRA_URL + API_ENDPOINT
    auth = (USERNAME, API_TOKEN)
    print(url)
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
    
    print(payload)
    response = requests.post(url, auth=auth, headers=headers, data=json.dumps(payload),verify=False)

    if response.status_code == 201:
        print("Story created successfully.")
        print("Issue key:", response.json()["key"])
        key = response.json()["key"]
        st.chat_message("assistant").warning(f"Jira Story with ID {key} have been created successfully!!! :+1: :tada:")
    else:
        print("Failed to create story.")
        print("Status code:", response.status_code)
        print("Response:", response.json())
        st.chat_message("assistant").warning(f"Failed to create Jira Story!!! :cry:")
        
        
def make_story(raw_text):

    # Initialize variables
    description = "No title provided"  # Default value if title is absent
    details = []

    # Check if the raw text contains both "Jira story" and "Acceptance Criteria"
    if "Story" in raw_text and "Acceptance Criteria" in raw_text:
        # Split the raw text into lines
        lines = raw_text.strip().split('\n')

        # Process each line
        for line in lines:
            if "Title" in line:
                description = line.replace("Story Title: ", "").strip()
            elif line.startswith("Story:"):
                # Collect the story details, including the label
                details.append(line.strip())
            elif line.startswith("Acceptance Criteria:"):
                # Add the acceptance criteria header
                details.append(line.strip())
            elif details or "Acceptance Criteria" in line:
                # Continue collecting details for the acceptance criteria
                details.append(line.strip())

        # Create the JSON object
        story_json = {
            "description": description,
            "details": "\n".join(details)  # Merge details into a single string
        }

        # Convert to JSON string (if needed)
        story_json_string = json.dumps(story_json, indent=4)

        # Print the JSON string
        print(story_json_string)
        return story_json_string
    else:
        print("The raw text does not contain both 'Jira story' and 'Acceptance Criteria'.")
