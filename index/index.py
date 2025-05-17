from openai import OpenAI
from streamlit_option_menu import option_menu
import streamlit as st
import datetime
import json
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np
import soundfile as sf
import io


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
    st.title('Record')
    
    def audio_frame_callback(frame):
        sound = frame.to_ndarray()
        return av.AudioFrame.from_ndarray(sound, layout="stereo")
    
    webrtc_ctx = webrtc_streamer(
        key="speech-to-text",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=1024,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"video": False, "audio": True},
    )
    
    if webrtc_ctx.state.playing:
        audio_frames = []
        while True:
            if webrtc_ctx.audio_receiver:
                try:
                    audio_frames.append(webrtc_ctx.audio_receiver.get_frame())
                except Exception as e:
                    break
        
        if audio_frames:
            # 將音頻幀轉換為 numpy 數組
            audio_data = np.concatenate([frame.to_ndarray() for frame in audio_frames])
            
            # 將音頻數據保存為 WAV 文件
            audio_bytes = io.BytesIO()
            sf.write(audio_bytes, audio_data, 44100, format='WAV')
            audio_bytes.seek(0)
            
            # 顯示音頻播放器
            st.audio(audio_bytes, format='audio/wav')
            
            # 將音頻數據保存到 session state
            st.session_state['recorded_audio'] = audio_bytes.getvalue()

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
