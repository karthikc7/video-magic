import os
import time
import subprocess
import moviepy.editor as mp
import speech_recognition as sr
from gtts import gTTS
import streamlit as st
import imageio_ffmpeg as iio  # Import the imageio_ffmpeg module

# Ensure FFmpeg is available
ffmpeg_path = iio.get_ffmpeg_exe()
if not os.path.exists(ffmpeg_path):
    st.error("FFmpeg is not installed or not found.")

def transcribe_audio(video_path):
    """Extract audio from video, convert it to text using Google Speech Recognition."""
    recognizer = sr.Recognizer()
    audio_file_path = "temp_audio.wav"
    
    # Use 'with' to ensure the video clip is closed properly
    with mp.VideoFileClip(video_path) as video_clip:
        video_clip.audio.write_audiofile(audio_file_path)

    # Recognize the audio
    with sr.AudioFile(audio_file_path) as source:
        audio = recognizer.record(source)
        transcription = recognizer.recognize_google(audio)

    os.remove(audio_file_path)  # Clean up temporary audio file
    return transcription

def synthesize_audio(text):
    """Convert the transcribed text into an audio file using gTTS."""
    tts = gTTS(text=text, lang='en')
    audio_file_path = "generated_audio.mp3"
    tts.save(audio_file_path)
    return audio_file_path

def replace_audio_in_video(video_path, new_audio_path, output_path="output_video.mp4"):
    """Replace the original audio in the video with the new synthesized audio."""
    with mp.VideoFileClip(video_path) as video_clip, mp.AudioFileClip(new_audio_path) as new_audio_clip:
        video_with_new_audio = video_clip.set_audio(new_audio_clip)
        video_with_new_audio.write_videofile(output_path, codec="libx264", audio_codec="aac")

    # Ensure the new video clip is closed
    video_with_new_audio.close()

# Streamlit UI
st.title("Audio Replacement in Video")

uploaded_video = st.file_uploader("Upload a Video", type=["mp4", "avi", "mov"])
if uploaded_video:
    # Save the uploaded video to a file
    video_path = "input_video.mp4"
    with open(video_path, "wb") as f:
        f.write(uploaded_video.read())

    st.video(uploaded_video)

    if st.button("Process Video"):
        try:
            # Step 1: Transcribe audio from the uploaded video
            transcription = transcribe_audio(video_path)
            st.write("Transcription:", transcription)

            # Step 2: Synthesize new audio from the transcription
            new_audio_file = synthesize_audio(transcription)

            # Step 3: Replace the original audio with the new audio
            output_video_path = "output_video.mp4"
            replace_audio_in_video(video_path, new_audio_file, output_video_path)

            st.success("Audio replaced successfully!")

            # Step 4: Provide a download button for the new video
            with open(output_video_path, "rb") as f:
                st.download_button("Download Processed Video", f, "output_video.mp4")

        except Exception as e:
            st.error(f"Error processing video: {e}")

        finally:
            # Clean up temporary files
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")
            if os.path.exists("generated_audio.mp3"):
                os.remove("generated_audio.mp3")
            if os.path.exists(video_path):
                time.sleep(1)  # Ensure the file is released before deleting
                os.remove(video_path)
