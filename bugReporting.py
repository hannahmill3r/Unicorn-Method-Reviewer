import streamlit as st
import json
from datetime import datetime

# Method 1: Using Streamlit's menu
def create_bug_report_menu2():
    with st.sidebar:
        with st.expander("Report a Bug 🐛"):
            user_name = st.text_input("Your Name:", key="name_sidebar")
            bug_description = st.text_area("Describe the bug you encountered:", key="bug_sidebar")
            if st.button("Submit Bug Report", key="submit_sidebar"):
                if bug_description and user_name:
                    save_bug_report(bug_description, user_name)
                    st.success("Bug report submitted successfully!")
                else:
                    st.error("Please fill in both your name and bug description")

# Method 2: Using a button and popup approach
def create_bug_report_button2():
    if st.button("Report a Bug 🐛"):
        user_name = st.text_input("Your Name:", key="name_main")
        bug_description = st.text_area("Describe the bug you encountered:", key="bug_main")
        if st.button("Submit", key="submit_main"):
            if bug_description and user_name:
                save_bug_report(bug_description, user_name)
                st.success("Bug report submitted successfully!")
            else:
                st.error("Please fill in both your name and bug description")

def save_bug_report2(description, name):
    # Initialize or load existing bug reports
    try:
        with open('bug_reports.json', 'r') as f:
            bug_reports = json.load(f)
    except FileNotFoundError:
        bug_reports = []
    
    # Create new bug report
    new_report = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'name': name,
        'description': description
    }
    
    # Add new report and save
    bug_reports.append(new_report)
    with open('bug_reports.json', 'w') as f:
        json.dump(bug_reports, f, indent=4)

import streamlit as st
import json
from datetime import datetime

# Method 1: Using Streamlit's menu
def create_bug_report_menu():
    with st.sidebar:
        with st.expander("Report a Bug 🐛"):
            if 'submitted_sidebar' not in st.session_state:
                st.session_state.submitted_sidebar = False
            
            if not st.session_state.submitted_sidebar:
                with st.form(key="bug_form_sidebar"):
                    user_name = st.text_input("Your Name:", key="name_sidebar")
                    bug_description = st.text_area("Describe the bug you encountered:", key="bug_sidebar")
                    submit_button = st.form_submit_button("Submit Bug Report")
                    
                    if submit_button and bug_description and user_name:
                        save_bug_report(bug_description, user_name)
                        st.session_state.submitted_sidebar = True
                        st.rerun()
                    elif submit_button:
                        st.error("Please fill in both your name and bug description")
            else:
                st.success("Bug report submitted successfully!")
                if st.button("Submit Another Response", key="another_sidebar"):
                    st.session_state.submitted_sidebar = False
                    st.rerun()

# Method 2: Using a button and popup approach
def create_bug_report_button():
    if 'submitted_main' not in st.session_state:
        st.session_state.submitted_main = False
        
    if st.button("Report a Bug 🐛") or st.session_state.submitted_main:
        if not st.session_state.submitted_main:
            with st.form(key="bug_form_main"):
                user_name = st.text_input("Your Name:", key="name_main")
                bug_description = st.text_area("Describe the bug you encountered:", key="bug_main")
                submit_button = st.form_submit_button("Submit")
                
                if submit_button and bug_description and user_name:
                    save_bug_report(bug_description, user_name)
                    st.session_state.submitted_main = True
                    st.rerun()
                elif submit_button:
                    st.error("Please fill in both your name and bug description")
        else:
            st.success("Bug report submitted successfully!")
            if st.button("Submit Another Response", key="another_main"):
                st.session_state.submitted_main = False
                st.rerun()

def save_bug_report(description, name):
    # Initialize or load existing bug reports
    try:
        with open('bug_reports.json', 'r') as f:
            bug_reports = json.load(f)
    except FileNotFoundError:
        bug_reports = []
    
    # Create new bug report
    new_report = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'name': name,
        'description': description
    }
    
    # Add new report and save
    bug_reports.append(new_report)
    with open('bug_reports.json', 'w') as f:
        json.dump(bug_reports, f, indent=4)