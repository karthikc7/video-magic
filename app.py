import subprocess
import os
import moviepy.editor as mp
import speech_recognition as sr
from gtts import gTTS
import streamlit as st
import imageio_ffmpeg as iio  # Import the imageio_ffmpeg module
import openai

# Replace with your Azure OpenAI API key and endpoint URL
openai.api_key = "22ec84421ec24230a3638d1b51e3a7dc"
openai.api_base = "https://internshala.openai.azure.com/openai/deployments/gpt-40/chat/completions?api-version=2024-08-01-preview"

# Ensure FFmpeg is available
ffmpeg_path = iio.get_ffmpeg_exe()  # Get the path to FFmpeg
if not os.path.exists(ffmpeg_path):
    st.error("FFmpeg is not installed or not found.")

def transcribe_audio(video_path):
    """Extracts audio from video, performs speech recognition, and cleans up temporary files"""
    recognizer = sr.Recognizer()
    audio_file_path = "temp_audio.wav"

    # Extract audio from video
    with mp.VideoFileClip(video_path) as video_clip:
        video_clip.audio.write_audiofile(audio_file_path)

    with sr.AudioFile(audio_file_path) as source:
        audio = recognizer.record(source)
        transcription = recognizer.recognize_google(audio, language="en-US", show_partial=True)  # Capture partial transcriptions

    os.remove(audio_file_path)
    return transcription

def correct_text(text):
    """Corrects the transcribed text using Azure OpenAI's GPT-4 model"""
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Correct the following text:\n{text}",
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text.strip()

def synthesize_audio(text, max_chars=100, voice_name='en-US-Wavenet-J'):
    """Converts text to speech with a specific voice, truncating if necessary"""
    if len(text) > max_chars:
        # Split text into chunks with a smaller character limit
        chunks = [text[i:i+100] for i in range(0, len(text), 100)]
        audio_files = []
        for i, chunk in enumerate(chunks):
            tts = gTTS(text=chunk, lang='en', slow=False)
            audio_file_path = f"generated_audio_{i}.mp3"
            tts.save(audio_file_path)
            audio_files.append(audio_file_path)
        # Concatenate audio files if needed
        final_audio_path = "generated_audio.mp3"
        mp.concatenate_audioclips([mp.AudioFileClip(file) for file in audio_files]).write_audiofile(final_audio_path)
        return final_audio_path
    else:
        tts = gTTS(text=text, lang='en', slow=False)
        audio_file_path = "generated_audio.mp3"
        tts.save(audio_file_path)
        return audio_file_path

def replace_audio_in_video(video_path, new_audio_path, output_path="output_video.mp4"):
    """Replaces video audio with the generated audio"""
    video_clip = mp.VideoFileClip(video_path)
    new_audio_clip = mp.AudioFileClip(new_audio_path)
    video_with_new_audio = video_clip.set_audio(new_audio_clip)
    video_with_new_audio.write_videofile(output_path, codec="libx264", audio_codec="aac")

# Streamlit UI
st.title("Audio Replacement in Video")

uploaded_video = st.file_uploader("Upload a Video", type=["mp4", "avi", "mov"])
if uploaded_video:
    # Saving the uploaded video to a file
    video_path = "input_video.mp4"
    with open(video_path, "wb") as f:
        f.write(uploaded_video.read())

    st.video(uploaded_video)

    if st.button("Process Video"):
        progress_bar = st.progress(0)
        try:
            transcription = transcribe_audio(video_path)
            progress_bar.progress(30)  # Update progress bar

            corrected_text = correct_text(transcription)
            progress_bar.progress(60)  # Update progress bar

            new_audio_file = synthesize_audio(corrected_text)
            progress_bar.progress(90)  # Update progress bar

            replace_audio_in_video(video_path, new_audio_file)
            progress_bar.progress(100)  # Update progress bar

            st.success("Audio replaced successfully!")
            with open("output_video.mp4", "rb") as f:
                st.download_button("Download Processed Video", f, "output_video.mp4")
        except Exception as e:
            st.error(f"Error processing video: {e}")
        finally:
            # Clean up any temporary files
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")
            if os.path.exists("generated_audio.mp3"):
                os.remove("generated_audio.mp3")