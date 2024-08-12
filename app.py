from flask import Flask, redirect, request, jsonify, session, url_for
from flask import send_file
import base64
import hashlib
import os
import urllib.parse
import requests
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import binascii
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = binascii.hexlify(os.urandom(24)).decode()

# Load environment variables from the .env file
load_dotenv()

# Configurations
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = 'https://instacanva.onrender.com/callback'
SCOPE = 'app:read design:content:read design:meta:read design:content:write design:permission:read design:permission:write folder:read folder:write folder:permission:read folder:permission:write asset:read asset:write comment:read comment:write brandtemplate:meta:read brandtemplate:content:read profile:read'
CODE_CHALLENGE_METHOD = 'S256'

# Configure the Google Gemini API
genai.configure(api_key=os.environ.get('GENAI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# SendGrid configuration
sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
sendgrid_from_email = os.environ.get('SENDGRID_MAIL')

# Twilio configuration
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NO')
client = Client(twilio_account_sid, twilio_auth_token)

# RECIPIENT info
RECIPIENT_MAIL = os.environ.get('RECIPIENT_MAIL')
RECIPIENT_NO = os.environ.get('RECIPIENT_NO')

Token_Response = dict()

def generate_code_verifier():
    """Generate a random code verifier."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')

def generate_code_challenge(code_verifier):
    """Generate a code challenge from the code verifier."""
    code_verifier_bytes = code_verifier.encode('utf-8')
    code_challenge_bytes = hashlib.sha256(code_verifier_bytes).digest()
    return base64.urlsafe_b64encode(code_challenge_bytes).decode('utf-8').rstrip('=')

@app.route('/')
def index():
    """Generate authorization URL and redirect user."""
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    auth_url = (
        "https://www.canva.com/api/oauth/authorize?"
        f"response_type=code&client_id={CLIENT_ID}&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"scope={urllib.parse.quote(SCOPE)}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method={CODE_CHALLENGE_METHOD}"
    )

    session['code_verifier'] = code_verifier
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handle OAuth2 callback and exchange code for access token."""
    auth_code = request.args.get('code')
    code_verifier = session.get('code_verifier')

    if not auth_code or not code_verifier:
        return jsonify({'error': 'Missing authorization code or code verifier'}), 400

    token_response = get_access_token(auth_code, code_verifier)
    print('T----------A', token_response.get('access_token'))

    if 'access_token' in token_response:
        session['access_token'] = token_response['access_token']
        Token_Response['access_token'] = token_response['access_token']

        whatsapp_url = "https://api.whatsapp.com/send?phone=14155238886&text=I%20am%20now%20authenticated%20with%20Canva!"
        button_html = f'''
        <html>
            <body style="display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f0f0;">
                <div style="text-align: center;">
                    <h1 style="color: #333;">Authentication successful!</h1>
                    <a href="{whatsapp_url}" target="_blank">
                        <button style="
                            background-color: #00c4cc;
                            color: #ffffff;
                            border: none;
                            border-radius: 8px;
                            padding: 15px 30px;
                            font-size: 55px;
                            font-weight: bold;
                            text-transform: uppercase;
                            cursor: pointer;
                            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                            transition: background-color 0.3s ease;
                        ">
                            Go to WhatsApp
                        </button>
                    </a>
                </div>
            </body>
        </html>
        '''

        return button_html
    else:
        return jsonify({'error': 'Failed to authenticate with Canva.'}), 400

def send_email(subject, html_content, to_email):
    try:
        message = Mail(
            from_email=sendgrid_from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content)
        sg = SendGridAPIClient(api_key=sendgrid_api_key)
        response = sg.send(message)
        logging.info(f"Email sent to {to_email}: {response.status_code}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def handle_natural_language_input(user_input):
    prompt = f"""
    You are instaCanva⚡, a productive & creative WhatsApp Bot 🤩 tool to help users create and manage Canva designs.
    Users might ask for help with creating a new design, finding templates, customizing designs, managing files,
    or account assistance. Given the user's input: {user_input}', generate an appropriate response.

    Your tagline is Instant ideas! Instant Designs! and you have some built in functionality to help users right here in
    WhatsApp : You can allow users to create designs, list designs , edit, view, upload assets and get ideas for their Canva
    projects right within WhatsApp! Also" if the user says Thanks or any related message, it means, he has gotten some other service you have offer.

    """

    response = model.generate_content(prompt)

    # Ensure the response has candidates
    if response and response.candidates:
        # Extract the summarised sentence from the first candidate's content parts
        candidate = response.candidates[0]
        if candidate.content and candidate.content.parts:
            summarised_sentence = candidate.content.parts[0].text.strip()
            return summarised_sentence

    return "Sorry, I couldn't understand your request. Please try again or ask for help."

@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    """Handle incoming WhatsApp messages."""
    incoming_msg = request.values.get('Body', '').lower()
    media_url = request.values.get('MediaUrl0', '')

    resp = MessagingResponse()
    msg = resp.message()

    # This will store the title temporarily
    user_data = {}
    list_data = {}

    # Check if the user wants to upload
    if 'upload' in incoming_msg:
        if 'access_token' not in Token_Response:
            msg.body("Please authenticate first by visiting: https://instacanva.onrender.com")
        else:
            msg.body("Go on to upload your asset now!")
    elif media_url and 'access_token' in Token_Response:
        try:
            # Fetch the media content
            file_data = requests.get(media_url).content
            upload_success = upload_asset_to_canva(file_data, Token_Response['access_token'])

            if upload_success:
                msg.body("Your asset has been successfully uploaded to your Canva account💥.")

                # Send the alert to Design Team Lead or Admin via email
                recipient_email = RECIPIENT_MAIL
                subject = 'New Upload to Canva via instaCanva 🎉'
                html_content = '''
                An asset has been successfully uploaded by one of your team members and may require some attention or review 🤩✨!<br>
                Thanks & Regards!<br>
                <strong>instaCanva⚡</strong>
                '''
                send_email(subject, html_content, recipient_email)
            else:
                msg.body("There was an error uploading your asset. Please try again.")
        except Exception as e:
            print(f"Error processing media: {e}")
            msg.body("There was an error processing your media. Please try again.")
    elif 'connect' in incoming_msg:
        if 'access_token' not in Token_Response:
            msg.body("Please authenticate first by visiting: https://instacanva.onrender.com")
        else:
            msg.body("Great Connecting! Let the magic begin🚀")
            msg.body("What do you want to do?")
    elif 'create' in incoming_msg and 'access_token' in Token_Response:
        if incoming_msg:    # Ask for the title of the creation
            # msg.body("Sure, give us a title for your creation")
            user_data['expected_action'] = 'get_title'
            user_data['design_type'] = 'doc'  # Store the design type for later use
        if user_data.get('expected_action') == 'get_title':
            # Capture the title from the user response
            title = incoming_msg
            data = {
                "design_type": {
                    "type": "preset",  # Can be "preset" or "custom"
                    "name": user_data.get('design_type')  # Use the stored design type
                },
                "title": title  # Use the title provided by the user
            }
            created = create_design(data, Token_Response['access_token'])
            if created:
                msg.body("Your creation has been successfully created 💥.")
            else:
                msg.body("There was an error creating your document. Please try again.")
            # Reset the user data after creation
            user_data.clear()
    elif 'list' in incoming_msg or 'show me' in incoming_msg or 'get me' in incoming_msg or 'download' in incoming_msg or 'export' in incoming_msg and 'access_token' in Token_Response:
        # response_message = "Here are the top 5 designs matching your search:"
        # msg.body(response_message)
        # msg.body("Please provide a search term to filter your designs.")
        incoming_msg = incoming_msg.replace('list', '').replace('show me', '').replace('get me', '').replace('download', '').replace('export', '').strip()
        list_data['expected_action'] = 'search_designs'

        listed_designs = list_designs(Token_Response['access_token'], incoming_msg)
        # search = incoming_msg
        if listed_designs.status_code == 200:
            designs_data = listed_designs.json()
            designs = designs_data.get("items", [])

            filtered_designs = [design for design in designs]

            # Select the top 5 results - LET'S FIRST GET ONE FOR NOW
            top_5_designs = filtered_designs[:1]
            if top_5_designs:
                for design in top_5_designs:
                    title = design.get('title', 'No Title')
                    design_id = design.get('id', 'No ID')
                    thumbnail_url = design.get('thumbnail', {}).get('url', '')

                    # Send the thumbnail as an image with a caption
                    if thumbnail_url:
                        # msg.media(thumbnail_url)
                        # caption = f"""Title: {title} with ID: {design_id} """
                        # msg.body(caption)
                        # print('DESIGNS:', title, design_id, thumbnail_url)
                        create_export = create_export_job(design_id, "pdf", Token_Response['access_token'])
                        if create_export.status_code == 200:
                            export_job = create_export.json().get("job", {})
                            export_job_id = export_job.get('id')
                            print(f"Export Job ID: {export_job_id}")

                            url = poll_export_status(export_job_id, Token_Response['access_token'])
                            if url:  # If the export job is successful and a URL is returned
                                file_name = "instaCanvaExport.pdf"  # Define the name of the file to save
                                print(url[0])

                                message = client.messages.create(
                                    body="Here's what you requested!",
                                    media_url=url,
                                    to=f'whatsapp:{RECIPIENT_NO}',
                                    from_=f'whatsapp:{twilio_phone_number}',
                                )
                                print("MB", message.body)
                            else:
                                msg.body("There was an error exporting your design. Please try again.")
                        else:
                            print(f"Failed to create export job: {create_export.status_code}")
                    else:
                        # If no thumbnail is available, send the details without the image
                        fallback_message = f'''Title: {title} with ID: {design_id} Thumbnail: No Thumbnail Available'''
                        msg.body(fallback_message)
            else:
                msg.body("No designs matched your search term. Please try again with a different term.")
        else:
            msg.body("There was an error retrieving your designs. Please try again.")

        # Reset the user data after the search
        list_data.clear()

    else:
        chat_bot = handle_natural_language_input(incoming_msg)
        msg.body(chat_bot)

    return str(resp)

def get_access_token(auth_code, code_verifier):
    """Exchange the authorization code for an access token."""
    token_url = "https://api.canva.com/rest/v1/oauth/token"

    credentials = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()

    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier
    }

    response = requests.post(token_url, headers=headers, data=data)
    return response.json()

def upload_asset_to_canva(file_data, access_token):
    """Upload an asset to Canva."""
    upload_url = "https://api.canva.com/rest/v1/asset-uploads"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",
        "Asset-Upload-Metadata": json.dumps({ "name_base64": "TXkgQXdlc29tZSBVcGxvYWQg8J+agA==" })
    }

    response = requests.post(upload_url, headers=headers, data=file_data)
    print(response.status_code)

    return response.status_code == 200

def create_design(data, access_token):
    """Create a design in Canva."""
    create_design_url = "https://api.canva.com/rest/v1/designs"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(create_design_url, headers=headers, json=data)
    if response.status_code == 200:
        design_data = response.json()
        return response.status_code == 200
    else:
        print(f"Failed to create design: {response.json()}")
        return None

def list_designs(access_token,search):
    """List all designs."""
    list_designs_url = "https://api.canva.com/rest/v1/designs"
    query_params = {
        "query": search,  # Optional: Add search term here if needed
        "ownership": "any",  # Can be "owned", "shared", or "any"
        "sort_by": "modified_descending"  # Can be "relevance", "modified_descending", "title_ascending", etc.
    }
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(list_designs_url, headers=headers, params=query_params)
    if response.status_code == 200:
        return response
    else:
        print(f"Failed to list designs: {response.json()}")
        return response.status_code

def get_design_metadata(design_id, access_token):
    """Get metadata for a specific design."""
    get_design_url = f"https://api.canva.com/rest/v1/designs/{design_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(get_design_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get design metadata: {response.json()}")
        return None

def create_export_job(design_id, export_format, access_token):
    """Create an export job for a design."""
    export_url = "https://api.canva.com/rest/v1/exports"
    data = {
        "design_id": design_id,
        "format": {
            "type": export_format
        }
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(export_url, headers=headers, json=data)
    return response

def get_export_status(export_job_id, access_token):
    """Get the status of an export job."""
    export_status_url = f"https://api.canva.com/rest/v1/exports/{export_job_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(export_status_url, headers=headers)
    # if response.status_code == 200:
    return response

def poll_export_status(export_job_id, access_token, max_retries=10, interval=10):
    """Poll the status of an export job until it is completed or the maximum retries are reached."""
    for attempt in range(max_retries):
        response = get_export_status(export_job_id, access_token)
        if response.status_code == 200:
            export_job_details = response.json().get("job", {})
            status = export_job_details.get("status")
            if status == "success":
                return export_job_details.get("urls", [])
            elif status == "failed":
                print("Export job failed.")
                return None
        else:
            print(f"Failed to get export status: {response.status_code}")

        time.sleep(interval)
    print("Max retries reached. Export job did not complete.")
    return None

@app.route('/create-design', methods=['POST'])
def create_design_route():
    """Route to create a design."""
    if 'access_token' not in Token_Response:
        return jsonify({'error': 'Authentication required'}), 403

    design_data = request.json
    design = create_design(design_data, Token_Response['access_token'])
    if design:
        return jsonify(design)
    else:
        return jsonify({'error': 'Failed to create design'}), 500

@app.route('/list-designs', methods=['GET'])
def list_designs_route():
    """Route to list designs."""
    if 'access_token' not in Token_Response:
        return jsonify({'error': 'Authentication required'}), 403

    designs = list_designs(Token_Response['access_token'])
    if designs:
        return jsonify(designs)
    else:
        return jsonify({'error': 'Failed to list designs'}), 500

@app.route('/design/<design_id>', methods=['GET'])
def get_design_metadata_route(design_id):
    """Route to get design metadata."""
    if 'access_token' not in Token_Response:
        return jsonify({'error': 'Authentication required'}), 403

    metadata = get_design_metadata(design_id, Token_Response['access_token'])
    if metadata:
        return jsonify(metadata)
    else:
        return jsonify({'error': 'Failed to get design metadata'}), 500

@app.route('/export-job', methods=['POST'])
def create_export_job_route():
    """Route to create an export job."""
    if 'access_token' not in Token_Response:
        return jsonify({'error': 'Authentication required'}), 403

    data = request.json
    export_job = create_export_job(data['design_id'], data['format'], Token_Response['access_token'])
    if export_job:
        return jsonify(export_job)
    else:
        return jsonify({'error': 'Failed to create export job'}), 500

@app.route('/export-job/<export_job_id>', methods=['GET'])
def get_export_status_route(export_job_id):
    """Route to get export job status."""
    if 'access_token' not in Token_Response:
        return jsonify({'error': 'Authentication required'}), 403

    status = get_export_status(export_job_id, Token_Response['access_token'])
    if status:
        return jsonify(status)
    else:
        return jsonify({'error': 'Failed to get export status'}), 500

@app.route('/print-session')
def print_session():
    """Print all the values in the session."""
    for key, value in session.items():
        print(f'{key}: {value}')
    return "Session values have been printed to the console."

# if __name__ == '__main__':
#     app.run(port=8000, debug=False)
