import openai
import streamlit as st
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime
import json

# Define the Gmail API scopes for read-only access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

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
            {
                "role": "system",
                "content": (
                    "Eres un experto redactor en español especializado en la creación de artículos de blog "
                    "atractivos, informativos y optimizados para SEO. Utiliza el siguiente contenido de correo "
                    "electrónico para generar un artículo en español con las siguientes características:\n\n"
                    "1. **Título**: Crea un título atractivo y optimizado para SEO que refleje con precisión el tema.\n"
                    "2. **Introducción**: Comienza con una introducción cautivadora y fácil de relacionar, que resalte la "
                    "importancia del tema y presente una declaración de tesis clara.\n"
                    "3. **Estructura**: Desglosa los puntos principales en secciones con subtítulos claros. Cada sección debe "
                    "ser informativa, proporcionando ejemplos prácticos y detalles específicos.\n"
                    "4. **Ejemplos**: Incluye ejemplos relevantes o estudios de caso para ilustrar los puntos clave. "
                    "Por ejemplo: 'Imagina una tienda de ropa que utiliza la inteligencia artificial para analizar el "
                    "comportamiento de sus clientes y enviar ofertas personalizadas justo antes de cada cambio de temporada.'\n"
                    "5. **Palabras Clave**: Integra de manera natural palabras clave como 'inteligencia artificial en marketing', "
                    "'transformación digital', y 'tecnología en marketing' sin sobrecargar el texto.\n"
                    "6. **Conclusión**: Termina con una conclusión que invite a la acción o a la reflexión, como animar al lector a "
                    "explorar más el tema o compartir sus opiniones.\n\n"
                    "Escribe el artículo en un tono cálido, conversacional y accesible. Asegúrate de que sea fácil de leer, con párrafos "
                    "cortos y un lenguaje claro. Utiliza un tono directo que hable a las necesidades e intereses del lector."
                )
            },
            {"role": "user", "content": content}
        ]
    )
    return response['choices'][0]['message']['content'].strip()

# Gmail API setup to retrieve relevant emails
def fetch_emails():
    # Ensure the Gmail credentials file has been uploaded
    if gmail_credentials is not None:
        creds = Credentials.from_authorized_user_info(json.load(gmail_credentials), SCOPES)
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
    else:
        st.error("Please upload your Gmail credentials JSON file.")
        return []

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
    if not openai_api_key or not wp_username or not wp_password or gmail_credentials is None:
        st.error("Please provide all required credentials and ensure the Gmail credentials file is uploaded.")
    else:
        emails = fetch_emails()
        for email in emails:
            title = email["subject"]
            content = generate_article(email["body"])
            publish_response = publish_to_wordpress(title, content)
            st.success(f"Published: {publish_response['title']['rendered']}")
