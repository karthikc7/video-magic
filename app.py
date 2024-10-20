import streamlit as st
import os
import moviepy.editor as mp
import speech_recognition as sr
from gtts import gTTS

def transcribe_audio(video_path):
    recognizer = sr.Recognizer()
    audio_file_path = "temp_audio.wav"
    
    video_clip = mp.VideoFileClip(video_path)
    video_clip.audio.write_audiofile(audio_file_path)
    
    with sr.AudioFile(audio_file_path) as source:
        audio = recognizer.record(source)
        transcription = recognizer.recognize_google(audio)
    os.remove(audio_file_path)
    return transcription

def synthesize_audio(text):
    tts = gTTS(text=text, lang='en')
    audio_file_path = "generated_audio.mp3"
    tts.save(audio_file_path)
    return audio_file_path

def replace_audio_in_video(video_path, new_audio_path, output_path="output_video.mp4"):
    video_clip = mp.VideoFileClip(video_path)
    new_audio_clip = mp.AudioFileClip(new_audio_path)
    video_with_new_audio = video_clip.set_audio(new_audio_clip)
    video_with_new_audio.write_videofile(output_path, codec="libx264", audio_codec="aac")

# Streamlit UI
st.title("Audio Replacement in Video")

uploaded_video = st.file_uploader("Upload a Video", type=["mp4", "avi", "mov"])
if uploaded_video:
    with open("input_video.mp4", "wb") as f:
        f.write(uploaded_video.read())
    
    st.video(uploaded_video)

    if st.button("Process Video"):
        transcription = transcribe_audio("input_video.mp4")
        st.write("Transcription:", transcription)

        new_audio_file = synthesize_audio(transcription)
        replace_audio_in_video("input_video.mp4", new_audio_file)

        st.success("Audio replaced successfully!")
        with open("output_video.mp4", "rb") as f:
            st.download_button("Download Processed Video", f, "output_video.mp4")
