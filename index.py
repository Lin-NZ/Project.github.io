import openai
import streamlit as st
import pyaudio
import wave
import datetime

API_Key = st.secrets["openai_key"] #API Key from OpenAI (Whisper)
openai.api_key = API_Key # Accesing API Key (ChatGPT)
model_id = 'whisper-1' 

st.title('Test App')

# Hide Footer(Made with Streamlit) & Main Menu
hide_st_style = '''
    <style>
        #MainMenu {visibility : hidden;}
        footer {visibility : hidden;}
    </style>
    '''
st.markdown(hide_st_style, unsafe_allow_html = True)

media_file = st.file_uploader('Upload Audio', type = ('wav', 'mp3', 'mp4'))

def transcribe_audio():
    if media_file is not None:
        return openai.Audio.transcribe(
            api_key = API_Key,
            model = model_id,
            file = media_file,
            response_format = 'text'  # text, json, srt, vtt
        )


if media_file is not None:  # Check if a file has been uploaded
    if st.sidebar.button("Transcribe Audio"):
        transcribe_response = transcribe_audio()
        st.text("Transcription")
        st.write(transcribe_response)
        summary_response = openai.ChatCompletion.create(
            model = 'gpt-3.5-turbo',
            messages = [{'role': 'user', 'content': '幫我把以下會議紀錄根據內容整理成段落後再段落整理成摘要並做出表格，
表格內容須顯示段落主題約30字內容再額外顯示最終結論 ' + transcribe_response}]
        )
        st.text("")
        st.text("Summary")
        st.write(summary_response['choices'][0]['message']['content'])
