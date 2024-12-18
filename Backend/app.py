from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS  # Import CORS
from deepface import DeepFace
import os
import moviepy.editor as mp
import torchaudio
import torchaudio.transforms as T
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC, pipeline
import torch
import cv2
import uuid
import soundfile as sf
import matplotlib.pyplot as plt

app = Flask(__name__)
CORS(app)  # Enable CORS for the app

UPLOAD_FOLDER = 'uploads'
GRAPH_FOLDER = 'graphs'
AUDIO_FOLDER = 'audios'
FRAME_FOLDER = 'frames'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GRAPH_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(FRAME_FOLDER, exist_ok=True)

# Load ASR and Emotion Recognition models for audio
asr_processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
asr_model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
emotion_recognition = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")

def extract_audio(video_path):
    video = mp.VideoFileClip(video_path)
    audio_path = os.path.join(AUDIO_FOLDER, f"{uuid.uuid4()}.wav")
    video.audio.write_audiofile(audio_path)
    return audio_path

def process_audio(audio_path):
    signal, sample_rate = sf.read(audio_path)
    signal = torch.tensor(signal).float()  # Convert signal to float

    if sample_rate != 16000:
        resampler = T.Resample(orig_freq=sample_rate, new_freq=16000)
        signal = resampler(signal.unsqueeze(0)).squeeze().numpy()

    chunk_duration = 1.0  # seconds
    chunk_samples = int(16000 * chunk_duration)
    num_chunks = len(signal) // chunk_samples
    audio_emotions = []

    for i in range(num_chunks):
        chunk = signal[i * chunk_samples : (i + 1) * chunk_samples]
        input_values = asr_processor(chunk, sampling_rate=16000, return_tensors="pt").input_values
        with torch.no_grad():
            logits = asr_model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = asr_processor.decode(predicted_ids[0])

        emotions = emotion_recognition(transcription)
        dominant_emotion = max(emotions, key=lambda x: x['score'])
        audio_emotions.append({"time": i, "emotion": dominant_emotion['label']})

    return audio_emotions


def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    video_emotions = []
    frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Process every nth frame for efficiency
        if frame_count % int(fps) == 0:  # Every 1 second
            try:
                result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                dominant_emotion = result[0]['dominant_emotion'] if isinstance(result, list) else result['dominant_emotion']
                video_emotions.append({"time": frame_count / fps, "emotion": dominant_emotion})

                # Save the frame as an image for frontend preview
                frame_filename = f"{FRAME_FOLDER}/{uuid.uuid4()}.jpg"
                cv2.imwrite(frame_filename, frame)
                frames.append(frame_filename)
                
            except Exception as e:
                print(f"Error processing frame {frame_count}: {e}")

        frame_count += 1

    cap.release()
    return video_emotions, frames

def generate_emotion_graph(video_emotions, audio_emotions):
    video_times = [item['time'] for item in video_emotions]
    video_values = [item['emotion'] for item in video_emotions]
    audio_times = [item['time'] for item in audio_emotions]
    audio_values = [item['emotion'] for item in audio_emotions]

    # Create a mapping for emotion to a numerical value for plotting
    emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
    emotion_to_num = {emotion: idx for idx, emotion in enumerate(emotion_labels)}

    video_values_num = [emotion_to_num.get(emotion, None) for emotion in video_values]
    audio_values_num = [emotion_to_num.get(emotion, None) for emotion in audio_values]

    plt.figure(figsize=(12, 6))
    plt.plot(video_times, video_values_num, 'o-', label='Video Emotions')
    plt.plot(audio_times, audio_values_num, 'x--', label='Audio Emotions')
    plt.yticks(ticks=range(len(emotion_labels)), labels=emotion_labels)
    plt.xlabel('Time (seconds)')
    plt.ylabel('Emotion')
    plt.title('Time vs Emotion Graph')
    plt.legend()
    plt.grid(True)

    graph_path = os.path.join(GRAPH_FOLDER, f"{uuid.uuid4()}.png")
    plt.savefig(graph_path)
    plt.close()
    return graph_path

@app.route('/upload', methods=['POST'])
def upload_video():
    file = request.files['file']
    video_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(video_path)

    # Process both video and audio
    video_emotions, frames = process_video(video_path)
    audio_path = extract_audio(video_path)
    audio_emotions = process_audio(audio_path)

    # Generate combined emotion graph
    graph_path = generate_emotion_graph(video_emotions, audio_emotions)

    return jsonify({
        "frames": frames,
        "video_emotions": [{"time": v["time"], "emotion": v["emotion"]} for v in video_emotions],
        "audio_emotions": [{"time": a["time"], "emotion": a["emotion"]} for a in audio_emotions],
        "graph": graph_path
    })

@app.route('/graphs/<path:filename>')
def serve_graph(filename):
    return send_from_directory(GRAPH_FOLDER, filename)

@app.route('/frame/<path:filename>')
def serve_frame(filename):
    return send_from_directory(FRAME_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
