import openai
import streamlit as st
from streamlit_option_menu import option_menu
import pyaudio
import wave
import datetime

with st.sidebar:
    selected = option_menu(
        menu_title = "Main Menu",
        options = ["Record", "Upload", "Transcribe", "Summary"],
    )



if selected == "Upload":
    st.title('Upload')

    API_Key = st.secrets["openai_key"] #API Key from OpenAI (Whisper)
    openai.api_key = API_Key # Accesing API Key (ChatGPT)
    model_id = 'whisper-1' 
    
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
                messages = [
                    {"role": "system", "content": "你是個得力的文書處理助手。"},
                    {"role": "assistant", "content": "我是一個基於人工智慧的語言模型，設計來幫助處理各種文書處理任務。如果您有任何需要，不論是文字處理、文件編輯、資訊檢索或其他任何事情，請隨時告訴我，我會盡力提供幫助。請問您有什麼特定的問題或工作，我可以協助您處理嗎？"},
                    {"role": "user", "content": "幫我把會議紀錄根據內容整理成段落，再根據段落整理成表格，表格內容須顯示段落主題、約50字摘要，並在表個最後一列顯示最終結論。"},
                    {"role": "assistant", "content": "當然可以幫您進行這項任務。請提供會議紀錄的內容，我將根據您的要求整理成表格，包括段落主題、約50字的摘要，以及最終結論。請提供會議紀錄的文本或內容，我將嘗試協助您處理。"},
                    {"role": "user", "content": transcribe_response}
                ]
            )
            st.text("")
            st.text("Summary")
            st.write(summary_response['choices'][0]['message']['content'])
