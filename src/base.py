from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import ChatMessage
from langchain_openai import ChatOpenAI
import streamlit as st
import configparser
import azai 
config = configparser.ConfigParser()
config.read('config.ini')



llm = azai.client

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)


with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", type="password")

if "messages" not in st.session_state:
    st.session_state["messages"] = [ChatMessage(role="assistant", content="How can I help you?")]

for msg in st.session_state.messages:
    st.chat_message(msg.role).write(msg.content)

if prompt := st.chat_input():
    st.session_state.messages.append(ChatMessage(role="user", content=prompt))
    st.chat_message("user").write(prompt)


   
    stream_handler = StreamHandler(st.empty())
    messages = [{"role": msg.role, "content": msg.content} for msg in st.session_state.messages]
    response = llm.chat.completions.create(
    model="gpt-4",
        messages=messages,
        stream=False,
        #tools=tools,
        #tool_choice="auto"
    )
    
    #response = llm.invoke(st.session_state.messages)
    
    
    assistant_message = response.choices[0].message.content
    st.session_state.messages.append(ChatMessage(role="assistant", content=assistant_message))
    st.chat_message("assistant").write(assistant_message)
