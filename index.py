import openai
from streamlit_option_menu import option_menu
import streamlit as st
from st_audiorec import st_audiorec
import datetime

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
openai.api_key = API_Key # Accessing API Key Globally(ChatGPT)

# Session State
if 'transcribe_response' not in st.session_state:
    st.session_state['transcribe_response'] = None
if 'summary_response' not in st.session_state:
    st.session_state['summary_response'] = None

# Function
def transcribe_audio():
    if media_file is not None:
        transcribe_response = openai.Audio.transcribe(
            api_key = API_Key,
            model = model_id,
            file = media_file,
            response_format = 'text'  # text, json, srt, vtt
        )
        return transcribe_response

def summarize_audio(tr_response):
    if media_file is not None:
        summary_response = openai.ChatCompletion.create(
            model = 'gpt-3.5-turbo-1106',
            messages = [
                {"role": "system", "content": "你是個熟練於整理重點跟紀錄重要事項的文書處理者。"},
                {"role": "assistant", "content": "是的，我擁有整理、記錄和處理文書的能力。如果您有任何需要整理的信息或想要記錄的重要事項，請告訴我，我將盡力協助您完成相關的文書工作。無論是整理文件、撰寫摘要、還是紀錄重要內容，我都可以提供支援。請告訴我您需要的具體協助，我將竭誠為您服務。請問您有什麼特定的問題或工作，我可以協助您處理嗎？"},
                {"role": "user", "content": "幫我把會議紀錄根據內容梳理成段落，再根據段落整理出第一個表格為會議摘要，內容須顯示段落主題、約50字摘要，並在表格最後一個行最終結論；第二個表格為待辦清單，根据會議記錄，顯示待辦事項(若沒有則填寫無)、執行者(若沒有則填寫無)"},
                {"role": "assistant", "content": "當然可以幫您進行這項任務。請提供會議紀錄的內容，我將根據您的要求整理成表格。請提供會議紀錄的文本或內容，我將嘗試協助您處理。"},
                {"role": "user", "content": "把以下會議記錄按照上面的要求彙整，結尾不需要其他詢問:"+ tr_response}
            ]
        )
        return summary_response

# Record Page
if selected == "Record":
    st.title('Record')
    
    wav_audio_data = st_audiorec()

    if wav_audio_data is not None:
        st.audio(wav_audio_data, format='audio/wav')

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
            {"role": "assistant", "content": "So from the transcription you have uploaded, what question do you have?"}
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
                
                for response in openai.ChatCompletion.create(
                    model = "gpt-3.5-turbo-1106",
                    messages = [{"role": m["role"], "content": m["content"]}
                              for m in st.session_state.messages], stream=True):
                                  
                    full_response += response.choices[0].delta.get("content", "")
                    message_placeholder.markdown(full_response + "▌")
                                  
                message_placeholder.markdown(full_response)
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})
