from flask import Flask, render_template, jsonify, request
import time
import azure.cognitiveservices.speech as speechsdk
import threading
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Azure Speech and OpenAI configuration
speech_key = "Azure Speech Service API Key"
service_region = "syour region"
GPT4V_KEY = "Azure OpenAI Service API Key"
GPT4V_ENDPOINT = "your endpoint URL"
headers = {
    "Content-Type": "application/json",
    "api-key": GPT4V_KEY,
}

# Set the end-of-speech timeout (in milliseconds)
ENDPOINT_SILENCE_TIMEOUT_MS = 5000  # 5 seconds

app = Flask(__name__)
transcription_result = {"text": "", "response": ""}
recognizer = None
recognition_thread = None
done = False

def setup_speech_recognition():
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, str(ENDPOINT_SILENCE_TIMEOUT_MS))
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    return recognizer

def continuous_transcription():
    global transcription_result, done, recognizer
    recognizer = setup_speech_recognition()
    accumulated_text = []

    def handle_continuous_result(evt):
        result = evt.result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized: {}".format(result.text))
            accumulated_text.append(result.text)
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized.")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details.reason
            print("Speech Recognition canceled: {}".format(cancellation))
            if result.cancellation_details.error_details:
                print("Error details: {}".format(result.cancellation_details.error_details))

    def handle_session_stopped(evt):
        global done
        complete_transcription = " ".join(accumulated_text)
        transcription_result["text"] = complete_transcription
        print("Complete Transcription:", complete_transcription)

        # Send the transcription to Azure OpenAI and print the response
        response = analyze_text_with_openai(complete_transcription)
        transcription_result["response"] = response
        print("Azure OpenAI Response:", response)

        # Send email with the transcription and response
        send_email(response, recipients=["Email ID"])

        done = True

    def handle_no_speech(evt):
        print("No speech detected for a while. Stopping recognition...")
        recognizer.stop_continuous_recognition_async()

    # Connect callbacks
    recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
    recognizer.recognized.connect(handle_continuous_result)
    recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    recognizer.session_stopped.connect(handle_session_stopped)
    recognizer.canceled.connect(lambda evt: print('CANCELED: {}'.format(evt)))
    recognizer.speech_end_detected.connect(handle_no_speech)

    # Start continuous recognition
    recognizer.start_continuous_recognition_async().get()

    # Wait for the recognition session to complete
    while not done:
        time.sleep(1)

    print("Recognition completed.")

def analyze_text_with_openai(text):
    prompt = (
        "You are a highly intelligent assistant. Here is the transcription of a meeting:\n\n"
        f"{text}\n\n"
        "Please generate a summary and action items for this meeting transcription."
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a highly intelligent assistant, especially related generating a summary and action items for a meeting transcription."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800
    }

    try:
        response = requests.post(GPT4V_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
        
        response_data = response.json()
        if 'choices' not in response_data or not response_data['choices']:
            raise ValueError("Unexpected response structure from OpenAI API.")

        response_text = response_data['choices'][0]['message']['content'].strip()
        return response_text
    
    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return f"HTTP error: {http_err}"
    except requests.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return f"Request error: {req_err}"
    except ValueError as val_err:
        print(f"Value error occurred: {val_err}")
        return f"Value error: {val_err}"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"Unexpected error: {e}"

def send_email(content, recipients):
    subject = "Meeting Summary and Action Items"
    body = f"{content}"

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = 'Email ID'
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    # Send the email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('Email ID', 'password ')
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/')
def index():
    return render_template('index2.html')

@app.route('/start_transcription', methods=['POST'])
def start_transcription():
    global recognition_thread, done
    done = False
    recognition_thread = threading.Thread(target=continuous_transcription)
    recognition_thread.start()
    return jsonify({"status": "started"})

@app.route('/stop_transcription', methods=['POST'])
def stop_transcription():
    global recognizer
    if recognizer:
        recognizer.stop_continuous_recognition_async()
    return jsonify({"status": "stopped"})

@app.route('/get_transcription', methods=['GET'])
def get_transcription():
    return jsonify(transcription_result)

@app.route('/search_transcription', methods=['POST'])
def search_transcription():
    data = request.get_json()
    keyword = data.get("keyword", "")
    search_results = search_text_for_keyword(transcription_result["text"], keyword)
    return jsonify({"search_results": search_results})

def search_text_for_keyword(text, keyword):
    results = []
    if keyword:
        lines = text.split("\n")
        for line in lines:
            if keyword.lower() in line.lower():
                results.append(line)
    return results

if __name__ == "__main__":
    app.run(debug=True, port=5001)
