# pip install openai
# python3 -m pip install openai 
# python -m pip install openai

# pip install streamlit

# python -m streamlit run Whisper.py

import openai
import streamlit as st

API_Key = st.secrets["openai_key"] #API Key from OpenAI (Whisper)
openai.api_key = API_Key # Accesing API Key (ChatGPT)
model_id = 'whisper-1' 

st.title('Test App')

# Hide Footer(Made with Streamlit) & Main Menu
hide_st_style = '''
    <style>
        #MainMenu {visibility : hidden;}
        footer {visibility : hidden;}
    </style
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
            messages = [{'role': 'user', 'content': 'Summarize the main point in 50 words about ' + transcribe_response}]
        )
        st.text("")
        st.text("Summary")
        st.write(summary_response['choices'][0]['message']['content'])
