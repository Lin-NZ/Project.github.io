from openai import OpenAI
from streamlit_option_menu import option_menu
import streamlit as st
import datetime
import json
import pyaudio
import wave
import tempfile
import os
import time


with open('index/prompt.json', 'r', encoding='utf-8') as f:
    prompt = json.load(f)

# Hide Footer(Made with Streamlit) & Main Menu
hide_st_style = '''
    <style>
        #MainMenu {visibility : hidden;}
        footer {visibility : hidden;}
    </style>
    '''
st.markdown(hide_st_style, unsafe_allow_html = True)

# Nav Bar Setting
with st.sidebar:
    selected = option_menu(
        menu_title = "Menu",
        menu_icon = "menu-button-fill",
        options = ["Record", "Upload", "Transcribe", "Summary", "Q&A"],
        icons = ["mic", "upload", "book", "blockquote-left", "chat-right-dots"],
        #orientation = "horizontal",
        default_index = 1,
    )

# Variables
API_Key = st.secrets["openai_key"] #API Key from OpenAI (Whisper)
client = OpenAI(api_key=API_Key) # 初始化 OpenAI 客戶端

# Session State
if 'transcribe_response' not in st.session_state:
    st.session_state['transcribe_response'] = None
if 'summary_response' not in st.session_state:
    st.session_state['summary_response'] = None

# Function
def transcribe_audio():
    if media_file is not None:
        transcribe_response = client.audio.transcriptions.create(
            model=model_id,
            file=media_file,
            response_format='srt'  # text, json, srt, vtt
        )
        return transcribe_response

def summarize_audio(tr_response):
    if media_file is not None:
        summary_response = client.chat.completions.create(
            model="gpt-4",
            messages=prompt,
            temperature=0.5
        )
        return summary_response

# Record Page
if selected == "Record":
    st.title('錄音功能')
    
    # 音頻參數設定
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    # 初始化 session state
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = []
    if 'recording_time' not in st.session_state:
        st.session_state.recording_time = 0
    if 'recorded_audio' not in st.session_state:
        st.session_state.recorded_audio = None
    
    def record_audio():
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)
            
            st.session_state.recording = True
            st.session_state.audio_data = []
            start_time = time.time()
            
            while st.session_state.recording:
                data = stream.read(CHUNK, exception_on_overflow=False)
                st.session_state.audio_data.append(data)
                st.session_state.recording_time = int(time.time() - start_time)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            st.error(f"錄音時發生錯誤: {str(e)}")
            st.session_state.recording = False
    
    # 錄音控制按鈕
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button('開始錄音', disabled=st.session_state.recording):
            st.session_state.recording = True
            record_audio()
    
    with col2:
        if st.button('停止錄音', disabled=not st.session_state.recording):
            st.session_state.recording = False
    
    with col3:
        if st.button('清除錄音', disabled=not st.session_state.audio_data):
            st.session_state.audio_data = []
            st.session_state.recorded_audio = None
            st.session_state.recording_time = 0
            st.experimental_rerun()
    
    # 顯示錄音時間
    if st.session_state.recording:
        st.write(f"錄音時間: {st.session_state.recording_time} 秒")
    
    # 處理錄音數據
    if st.session_state.audio_data:
        try:
            # 創建臨時文件來保存音頻
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                wf = wave.open(temp_file.name, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(st.session_state.audio_data))
                wf.close()
                
                # 顯示音頻播放器
                st.audio(temp_file.name, format='audio/wav')
                
                # 將音頻數據保存到 session state
                with open(temp_file.name, 'rb') as f:
                    st.session_state['recorded_audio'] = f.read()
                
                # 刪除臨時文件
                os.unlink(temp_file.name)
                
                # 顯示下載按鈕
                st.download_button(
                    label="下載錄音檔案",
                    data=st.session_state['recorded_audio'],
                    file_name=f"recording_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
                    mime="audio/wav"
                )
                
        except Exception as e:
            st.error(f"處理音頻時發生錯誤: {str(e)}")

# Upload Page
if selected == "Upload":
    st.title('Upload')
    
    model_id = 'whisper-1' 
    
    media_file = st.file_uploader('Upload Audio', type = ('wav', 'mp3', 'mp4'))
    
    if media_file is not None:  # Check if a file has been uploaded
        if st.button("Transcribe Audio"):
            transcribe_response = transcribe_audio()
            st.write("Transcription Completed!")
            st.session_state['transcribe_response'] = transcribe_response
            summary_response = summarize_audio(transcribe_response)
            st.write("Summarizing Completed!")
            st.session_state['summary_response'] = summary_response['choices'][0]['message']['content']

# Transcribe Page
if selected == "Transcribe":
    st.title('Transcribe')
    if st.session_state['transcribe_response'] == None:
        st.write("Please Upload & Transcribe Audio First!")
    else:
        st.write(st.session_state['transcribe_response'])

# Summary Page
if selected == "Summary":
    st.title('Summary')
    if st.session_state['summary_response'] == None:
        st.write("Please Upload & Transcribe Audio First!")
    else:
        st.write(st.session_state['summary_response'])

# Q&A Page
if selected == "Q&A":
    if st.session_state['transcribe_response'] == None:
        st.write("Please Upload & Transcribe Audio First!")
    else:
        preset_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "assistant", "content": "Please upload your transcription"},
            {"role": "user", "content": st.session_state['transcribe_response']},
            {"role": "assistant", "content": "那麼根據您的紀錄，您有什麼想提問的嗎？?"}
        ]
        
        if "messages" not in st.session_state:
            st.session_state.messages = preset_messages
    
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("What do you want to know?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                for response in client.chat.completions.create(
                    model = "gpt-3.5-turbo-1106",
                    messages = [{"role": m["role"], "content": m["content"]}
                              for m in st.session_state.messages], stream=True):
                                  
                    full_response += response.choices[0].delta.get("content", "")
                    message_placeholder.markdown(full_response + "▌")
                                  
                message_placeholder.markdown(full_response)
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})
