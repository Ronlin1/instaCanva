# instaCanva 💥 - Instant Ideas! Instant Designs!

instaCanva is a powerful WhatsApp bot designed to integrate seamlessly with Canva, allowing users to manage and create Canva designs instantly from WhatsApp. The bot supports functionalities such as design creation, asset uploading, design listing, idea creation, Canva custom support, Canva for Teams Management, and more.

📌 Code is available to the judging team or members upon request! 
You don't need to download any app! to try instaCanva: Simply send `join moon-reach` to +14155238886 or visit this [link](https://wa.me/14155238886?text=Hello)

🎥 Demo: https://youtu.be/Dfd7Y4bf_5s

## 3 main keywords to use when testing the MVP
 - `upload` --  This will import or send your assets/files to Canva
 - `connect` -- Connect your Canva account to instaCanva
 - `download` or `get me` or `export` -- This downloads and retrieves the query parametered file

## Features 
![](/instaCanva.png)
- **Authenticate with Canva**: Users can authenticate their Canva account via OAuth2.
- **Upload Assets**: Upload images and other assets to Canva.
- **Create Designs**: Create new Canva designs with user-provided titles.
- **List Designs**: Search and list Canva designs based on user input.
- **Export Designs**: Export Canva designs in PDF format and receive them via WhatsApp.
- **Natural Language Processing**: Handle various user inputs and provide relevant responses using IBM Watsonx  AI.
- 
## Current Limitations
- Limited Command Handling: The bot currently supports a basic set of commands. More complex commands and functionalities will be added in future updates.
- Design Export Formats: Currently, only PDF export is supported. Support for additional formats will be considered.
- Scalability: The bot is optimized for basic use cases and may require further optimization to handle a large number of simultaneous users efficiently.
- Error Handling: Some edge cases and error scenarios are not fully covered. We are working on improving error handling and user feedback.
- User Interface: The user experience is limited to text-based interactions. Future updates will include more interactive elements.

## Future Integrations
- Enhanced Design Functionalities: Integration of more Canva features such as template customization, text editing, and image manipulation directly via WhatsApp.
- Multi-format Export: Support for additional export formats beyond PDF, such as PNG and JPEG.
- Advanced Natural Language Processing : Integration of more advanced NLP features for better understanding and response to user queries.
- Integration with Other Platforms: Future plans include integrating with other popular platforms and services to enhance functionality and user experience.
- Analytics and Reporting: Adding features for tracking and analyzing bot interactions and user activities to improve performance and user satisfaction.

## Active Development
InstaCanva is an actively developing project. We are continuously working on enhancing its features, improving performance, and addressing user feedback. Stay tuned for regular updates and new features!

## Prerequisites

- **Python 3.8+**
- **Flask**: Web framework for building the bot.
- **Requests**: For making HTTP requests.
- **Twilio**: For handling WhatsApp messages.
- **SendGrid**: For sending emails.
- **IBM Watsonx  AI**: For natural language processing.

## Setup

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies**

   Create a virtual environment and install the required Python packages:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**

   Create a `.env` file in the root directory of the project and add the following environment variables:

   ```
   IBM_API_KEY=<your-genai-api-key>
   SENDGRID_API_KEY=<your-sendgrid-api-key>
   SENDGRID_MAIL=<your-sendgrid-email>
   TWILIO_ACCOUNT_SID=<your-twilio-account-sid>
   TWILIO_AUTH_TOKEN=<your-twilio-auth-token>
   TWILIO_PHONE_NO=<your-twilio-phone-number>
   RECIPIENT_MAIL=<recipient-email-for-notifications>
   RECIPIENT_NO=<recipient-whatsapp-number-for-notifications>
   ```

4. **Run the Application**

   Start the Flask application:

   ```bash
   python app.py
   ```

   The bot will be accessible at `http://localhost:8000`.

## Endpoints

### Index Route

- **URL**: `/`
- **Method**: `GET`
- **Description**: Redirects the user to the Canva OAuth2 authorization page.

### Callback Route

- **URL**: `/callback`
- **Method**: `GET`
- **Description**: Handles the OAuth2 callback, exchanges the authorization code for an access token, and provides a link to WhatsApp for further interaction.

### WhatsApp Route

- **URL**: `/whatsapp`
- **Method**: `POST`
- **Description**: Handles incoming WhatsApp messages, processes commands, and responds accordingly.

## Functionality

### OAuth2 Authentication

The bot uses OAuth2 to authenticate users with Canva. It generates an authorization URL and exchanges the authorization code for an access token.

### Upload Asset

Users can upload assets (images, etc.) to Canva, and the bot will notify a designated recipient via email upon successful upload.

### Create Design

Users can create new Canva designs by providing a title. The bot interacts with Canva’s API to create the design and confirms the creation to the user.

### List Designs

The bot allows users to search and list their Canva designs based on input keywords. It can also export designs to PDF and send them via WhatsApp.

### Natural Language Processing

IBM Watsonx  AI is used to handle natural language input from users, providing appropriate responses and assistance based on the user's request.

## Logging

Logging is configured to provide information and error messages. Logs are output to the console and can be adjusted in the `logging.basicConfig` configuration.

## Contributing

Feel free to open issues and submit pull requests to contribute to the project. Please follow the code of conduct and contributing guidelines provided in the repository.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any questions or support, please contact [AFRO BOY](mailto:ronlinx6@.com).

---

This README should provide a comprehensive overview of instaCanva, its setup, and its functionality.
