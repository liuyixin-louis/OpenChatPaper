import datetime
import os
import streamlit as st
from streamlit_chat import message
import requests
from config import PDF_SAVE_DIR, quickbuttons

st.set_page_config(
    page_title="ChatPaper - Demo",
    page_icon=":robot:"
)

pdf_uploaded = False

if pdf_uploaded is False:
    st.sidebar.markdown("## Upload a PDF")
    pdf_uploader = st.sidebar.file_uploader("Upload a PDF", type="pdf", )

st.sidebar.markdown("## API Key")
api_key = st.sidebar.text_input(
    "OpenAI API Key", value="", label_visibility="hidden", help="Please enter your API key.")


def get_text():
    input_text = st.text_input(
        "User: ", "", help="Please ask any questions about the paper.")
    return input_text


st.header("ChatPaper - Demo")

API_URL = "http://localhost:5000/query/"
header = {"api_key": ""}

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

if "user_stamp" not in st.session_state:
    import datetime
    user_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state['user_stamp'] = user_stamp


if pdf_uploader is not None:
    if api_key:
        header['api_key'] = api_key
        pdf_name = pdf_uploader.name.replace(' ', '_')

        file_name = f"{st.session_state.user_stamp}_{pdf_name}"

        # check PDF_SAVE_DIR
        if not os.path.exists(PDF_SAVE_DIR):
            os.makedirs(PDF_SAVE_DIR)

        filepath = os.path.join(PDF_SAVE_DIR, file_name)
        with open(filepath, "wb") as f:
            f.write(pdf_uploader.getbuffer())
        user_query = get_text()
        
        # summarize_button = st.sidebar.button("Summarize")
        # if summarize_button:
        #     user_query = "Please summarize this paper."
        
        # contribution_button = st.sidebar.button("Contribution")
        # if contribution_button:
        #     user_query = "What is the contribution of this paper?"
        
        # novelty_button = st.sidebar.button("Novelty")
        # if novelty_button:
        #     user_query = "What is the novelty of this paper?"
        
        # strength_button = st.sidebar.button("Strength")
        # if strength_button:
        #     user_query = "What are the strengths of this paper?"
        
        # drawback_button = st.sidebar.button("Drawback")
        # if drawback_button:
        #     user_query = "What are the drawbacks of this paper?"
        
        # improvement_button = st.sidebar.button("Improvement")
        # if improvement_button:
        #     user_query = "What might be the improvements of this paper?"
        
        st.sidebar.markdown("## Quick Buttons")
        for key, value in quickbuttons.items():
            button = st.sidebar.button(key, key=key)
            if button:
                user_query = value
        
        if user_query:
            st.session_state.past.append(user_query)
            query_data = {"pdf_link": filepath,
                          "user_stamp": st.session_state.user_stamp, "user_query": user_query}
            print(query_data)
            response = requests.post(
                API_URL, headers=header, json=query_data, timeout=300)
            output = response.json()
            code = output['code']
            response = output['response']
            if code == 200:
                st.session_state.generated.append(response)

        if st.session_state['generated']:
            for i in range(len(st.session_state['generated'])-1, -1, -1):
                message(st.session_state["generated"][i],
                        key=str(i), avatar_style="fun-emoji")
                message(st.session_state['past'][i], is_user=True, key=str(
                    i) + '_user', avatar_style="personas")
    else:
        st.markdown(
            "<span style='color:red'>Please enter your API key.</span>", unsafe_allow_html=True)
else:
    st.markdown("<span style='color:red'>Please upload a PDF file.</span>",
                unsafe_allow_html=True)
