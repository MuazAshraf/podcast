from flask import Flask, request, jsonify
from podcastfy.client import generate_podcast
from IPython.display import Audio
import os
from dotenv import load_dotenv
import atexit
import grpc, sys

# Force unbuffered logging
os.environ['PYTHONUNBUFFERED'] = "1"
sys.stderr = sys.stdout

# Load environment variables
load_dotenv('.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
# Graceful shutdown for grpc

def shutdown_server():
    grpc._cython.cygrpc._stop()
    print("Server shutting down...")

atexit.register(shutdown_server)
# Function to embed audio
def embed_audio(audio_file):
    try:
        return f"Audio generated successfully. File path: {audio_file}"
    except Exception as e:
        return f"Error embedding audio: {str(e)}"

@app.route('/generate_podcast', methods=['POST'])
def generate_podcast_api():
    try:
        data = request.get_json()

        # Extract options from JSON request
        urls = data.get('urls', [])
        transcript_only = data.get('transcript_only', False)
        tts_model = data.get('tts_model', 'openai')  # Default to OpenAI TTS
        longform = data.get('longform', False)
        raw_text = data.get('text', None)
        topic = data.get('topic', None)
        image_paths = data.get('image_paths', [])
        transcript_file = data.get('transcript_file', None)
        llm_model_name = data.get('llm_model_name', None)
        api_key_label = OPENAI_API_KEY
        file_path = data.get('file_path', None)
        conversation_config = data.get('conversation_config', None)

        # Initialize audio file variable
        audio_file = None

        # Handle YouTube URL processing
        if urls and any("youtube.com" in url or "youtu.be" in url for url in urls):
            # Extract YouTube video IDs
            video_ids = [url.split('v=')[-1].split('&')[0] if 'youtube.com' in url else url.split('/')[-1].split('?')[0] for url in urls]
            urls = [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]

        # Generate podcast based on input options
        if urls:
            audio_file = generate_podcast(urls=urls, tts_model=tts_model, longform=longform, transcript_only=transcript_only, api_key_label=api_key_label)

        elif raw_text:
            audio_file = generate_podcast(text=raw_text, tts_model=tts_model, api_key_label=api_key_label)

        elif topic:
            audio_file = generate_podcast(topic=topic, tts_model=tts_model, api_key_label=api_key_label)

        elif image_paths:
            audio_file = generate_podcast(image_paths=image_paths, tts_model=tts_model, api_key_label=api_key_label)

        elif transcript_file:
            audio_file = generate_podcast(transcript_file=transcript_file, tts_model=tts_model, api_key_label=api_key_label)

        elif file_path and file_path.endswith('.pdf'):
            audio_file = generate_podcast(urls=[file_path], tts_model=tts_model, api_key_label=api_key_label)

        elif conversation_config:
            audio_file = generate_podcast(urls=urls, conversation_config=conversation_config, tts_model=tts_model, api_key_label=api_key_label)

        # Custom LLM Model
        elif llm_model_name and api_key_label:
            audio_file = generate_podcast(urls=urls, tts_model=tts_model, llm_model_name=llm_model_name, api_key_label=api_key_label)

        else:
            return jsonify({"error": "Invalid input parameters"}), 400

        # Return success response with audio file
        response_message = embed_audio(audio_file)
        return jsonify({"message": response_message, "file": audio_file})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, threaded=True)

