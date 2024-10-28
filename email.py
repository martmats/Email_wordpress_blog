import openai
import streamlit as st
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime

# Streamlit Sidebar for Secret Keys and Filters
st.sidebar.title("API Settings")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
wp_username = st.sidebar.text_input("WordPress Username")
wp_password = st.sidebar.text_input("WordPress Application Password", type="password")
gmail_credentials = st.sidebar.file_uploader("Upload Gmail credentials.json", type="json")

st.sidebar.title("Email Filter Settings")
start_date = st.sidebar.date_input("Start Date", datetime.now())
end_date = st.sidebar.date_input("End Date", datetime.now())

# Set OpenAI API Key
openai.api_key = openai_api_key

# Function to generate article content from email text using GPT-3.5 Turbo
def generate_article(content):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Create a blog article from the following email content."},
            {"role": "user", "content": content}
        ]
    )
    return response['choices'][0]['message']['content'].strip()

# Gmail API setup to retrieve relevant emails
def fetch_emails():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = Credentials.from_authorized_user_file("gmail_credentials.json", SCOPES)
    service = build('gmail', 'v1', credentials=creds)

    # Query for specific keywords and date range
    query = "AI OR artificial intelligence OR IA OR inteligencia artificial"
    if start_date and end_date:
        query += f" after:{start_date.strftime('%Y/%m/%d')} before:{end_date.strftime('%Y/%m/%d')}"

    results = service.users().messages().list(userId='me', q=query).execute()
    emails = results.get('messages', [])

    email_data = []
    for email in emails:
        msg = service.users().messages().get(userId='me', id=email['id']).execute()
        subject = [header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject'][0]
        body = msg['snippet']  # Get snippet for preview
        email_data.append({"subject": subject, "body": body})
    
    return email_data

# Function to publish the generated article to WordPress
def publish_to_wordpress(title, content):
    url = "https://yourwordpresssite.com/wp-json/wp/v2/posts"
    headers = {
        "Authorization": f"Basic {wp_username}:{wp_password}"
    }
    post_data = {
        "title": title,
        "content": content,
        "status": "publish"
    }
    response = requests.post(url, headers=headers, json=post_data)
    return response.json()

# Main logic to fetch, process, and publish emails
if st.button("Run Automation"):
    if not openai_api_key or not wp_username or not wp_password or not gmail_credentials:
        st.error("Please provide all required credentials.")
    else:
        emails = fetch_emails()
        for email in emails:
            title = email["subject"]
            content = generate_article(email["body"])
            publish_response = publish_to_wordpress(title, content)
            st.success(f"Published: {publish_response['title']['rendered']}")
