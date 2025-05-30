import streamlit as st
import json
from datetime import datetime

# Method 1: Using Streamlit's menu
def create_bug_report_menu():
    with st.sidebar:
        with st.expander("Report a Bug 🐛"):
            bug_description = st.text_area("Describe the bug you encountered:")
            if st.button("Submit Bug Report"):
                if bug_description:
                    save_bug_report(bug_description)
                    st.success("Bug report submitted successfully!")
                else:
                    st.error("Please enter a bug description")

# Method 2: Using a button and popup approach
def create_bug_report_button():
    if st.button("Report a Bug 🐛"):
        bug_description = st.text_area("Describe the bug you encountered:")
        if st.button("Submit"):
            if bug_description:
                save_bug_report(bug_description)
                st.success("Bug report submitted successfully!")
            else:
                st.error("Please enter a bug description")

def save_bug_report(description):
    # Initialize or load existing bug reports
    try:
        with open('bug_reports.json', 'r') as f:
            bug_reports = json.load(f)
    except FileNotFoundError:
        bug_reports = []
    
    # Create new bug report
    new_report = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'description': description
    }
    
    # Add new report and save
    bug_reports.append(new_report)
    with open('bug_reports.json', 'w') as f:
        json.dump(bug_reports, f, indent=4)

