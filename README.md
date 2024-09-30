# Automated-Minutes-of-the-meeting

This project is a Flask-based web application that performs speech-to-text transcription using Azure's Cognitive Services and provides meeting summaries and action items using Azure OpenAI GPT-4. The application is designed to capture and process real-time speech, generate meeting minutes, and send the results via email.

# Features
1. Real-time Speech-to-Text Transcription: Captures speech from the microphone and converts it to text using Azure's Speech Service.
2. Intelligent Meeting Analysis: Uses OpenAI's GPT-4 model to generate meeting summaries and identify action items from the transcription.
3. Search Functionality: Allows you to search for keywords within the transcription.
4. Email Integration: Sends the meeting minutes and action items via email to the specified recipients.
   
# Setup and Installation
**Prerequisites**
1. Python 3.7+
2. Azure Speech SDK (azure-cognitiveservices-speech)
3. Flask
4. Requests
5. An Azure account with access to the Speech Service and OpenAI GPT-4

# Installation
1. Clone the repository
2. Install the dependencies
3. Run the application
