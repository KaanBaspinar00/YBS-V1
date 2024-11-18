# 3_Asistanım.py

import streamlit as st
from config import Config
import pandas as pd
import sqlite3
import os
from langchain.text_splitter import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from ollama_llm import Ollama  # Custom LLM

# Load Excel data
depo_veri_df = pd.read_excel('depo_veri12.xlsx')
qr_codes_output_df = pd.read_excel('qr_codes_output.xlsx')
qr_images12_df = pd.read_excel('qr_images12.xlsx')
recent_qr_codes12_df = pd.read_excel('recent_qr_codes12.xlsx')

# Load data from SQLite database
conn = sqlite3.connect('depo_veri12.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM varliklar")
assets_data = cursor.fetchall()
assets_columns = [description[0] for description in cursor.description]
assets_df = pd.DataFrame(assets_data, columns=assets_columns)
conn.close()

# Convert dataframes to combined text format for embeddings
def dataframes_to_text(dataframes):
    combined_text = ""
    for name, df in dataframes.items():
        combined_text += f"\n### {name} ###\n"
        combined_text += df.to_string(index=False)
    return combined_text

# Dictionary of dataframes for easy processing
dataframes = {
    "Depo Verileri": depo_veri_df,
    "QR Kodları": qr_codes_output_df,
    "QR Resimleri": qr_images12_df,
    "Son QR Kodları": recent_qr_codes12_df,
    "Varlıklar": assets_df,
}

# Process combined data text into chunks
combined_data_text = dataframes_to_text(dataframes)
text_splitter = CharacterTextSplitter(separator='\n', chunk_size=250000, chunk_overlap=15000)
data_chunks = text_splitter.split_text(combined_data_text)

# Create or load FAISS vector store
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
if os.path.exists("faiss_index"):
    vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
else:
    vector_store = FAISS.from_texts(data_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

# Conversation memory setup
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history",
        input_key="question",
        output_key="answer",
        return_messages=True
    )

# 3_Asistanım.py

import streamlit as st
from config import Config
import pandas as pd
import sqlite3
import os
from langchain.text_splitter import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from ollama_llm import Ollama
from typing import Any, Dict
import json
import requests

# Set up Streamlit page configuration
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    initial_sidebar_state="expanded"
)

st.title(Config.PAGE_TITLE)

# Sidebar settings
with st.sidebar:
    st.markdown("# Sohbet Seçenekleri")
    model = st.selectbox('Hangi modeli kullanmak istersin ?', [Config.OLLAMA_MODEL])


# [Previous data loading code remains the same until the chat handling part]

class StreamingConversationalRetrievalChain:
    def __init__(self, llm: Ollama, retriever: Any, memory: ConversationBufferMemory):
        self.llm = llm
        self.retriever = retriever
        self.memory = memory

    def _get_context(self, question: str) -> str:
        # Get relevant documents from the retriever
        docs = self.retriever.get_relevant_documents(question)
        # Combine the document contents
        return "\n".join(doc.page_content for doc in docs)

    def stream_response(self, question: str):
        # Get chat history
        chat_history = self.memory.chat_memory.messages

        # Get relevant context
        context = self._get_context(question)

        # Prepare the full prompt
        full_prompt = f"""Context: {context}

Chat History: {chat_history}

Current Question: {question}

Please provide a response based on the above context and chat history."""

        # Stream the response using the custom Ollama implementation
        url = f"{self.llm.base_url}/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": self.llm.model,
            "prompt": f"{Config.SYSTEM_PROMPT}\n\n{full_prompt}"
        }

        response = requests.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()

        full_response = ""
        for line in response.iter_lines():
            if line:
                content = line.decode('utf-8')
                if content.startswith('data: '):
                    content = content[6:]
                if content.strip() == '[DONE]':
                    break
                try:
                    response_json = json.loads(content)
                    chunk = response_json.get('response', '')
                    full_response += chunk
                    yield chunk
                except json.JSONDecodeError:
                    continue

        # Update memory with the full conversation
        self.memory.save_context({"question": question}, {"answer": full_response})


# Initialize the streaming chain
llm = Ollama(model=model)
retriever = vector_store.as_retriever()
streaming_chain = StreamingConversationalRetrievalChain(
    llm=llm,
    retriever=retriever,
    memory=st.session_state.memory
)

# Track chat messages in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input and generate assistant responses
if user_prompt := st.chat_input("Nasıl Yardımcı Olabilirim ?"):
    # Show user prompt in chat
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    try:
        # Create a placeholder for the assistant's response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""

            # Stream the response
            for chunk in streaming_chain.stream_response(user_prompt):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")

            # Remove cursor and display final response
            response_placeholder.markdown(full_response)

        # Save the complete message to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"Yanıt oluşturulurken bir hata oluştu: {str(e)}")