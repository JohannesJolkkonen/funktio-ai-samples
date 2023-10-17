from PyPDF2 import PdfReader
import streamlit as st
from dotenv import load_dotenv
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text
    
def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(raw_text)
    return chunks

def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
        )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']
    for i, message in reversed(list(enumerate(st.session_state.chat_history))):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)

def main():
    load_dotenv()
    st.set_page_config(page_title="HPE QuickSpec LLM-Demo", page_icon="https://yt3.googleusercontent.com/g7JWbHh0bzCiDFtfvq86-9Ro8yFNM6TESGJVhSB58a_aTrhLAkN9YTeSx_X156n5cRAMcrO_Q4c=s176-c-k-c0x00ffffff-no-rj-mo")

    st.write(css, unsafe_allow_html=True)
    
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = None

    st.header("Chat with ")
    user_question = st.text_input("Ask a question about your product sheets:")
    if user_question and st.session_state.vectorstore:
        try:
            handle_userinput(user_question)
        except Exception as e:
            print(f"Exception {e}")
    elif user_question:
        exception = "Please upload some product sheets using the sidebar!"
        st.write(bot_template.replace("{{MSG}}", exception), unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your product sheets and click 'Process'", accept_multiple_files=True
        )
        if st.button("Process files"):
            with st.spinner("Processing files"):
                # get pdf text
                raw_text = get_pdf_text(pdf_docs)
                
                # Get the text chunks 
                text_chunks = get_text_chunks(raw_text)

                # Create vector store
                st.session_state.vectorstore = get_vectorstore(text_chunks)
                
                # Create conversation chain
                st.session_state.conversation = get_conversation_chain(st.session_state.vectorstore)


if __name__ == '__main__':
    main()