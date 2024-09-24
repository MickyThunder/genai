import streamlit as st

def sidebar():
    with st.sidebar:
        st.markdown(
            "## How to use\n"
            "1. Enter your [OpenAI API key](https://platform.openai.com/account/api-keys) below🔑\n"  # noqa: E501
            "2. Upload a pdf, docx, or txt file📄\n"
            "3. Ask a question about the document💬\n"
        )
def mainSection(df):
    st.title("AI TechBA - Data Engineer Assistant")

    input_text = st.text_area("Enter your input text here:")

    if st.button("Submit"):
        st.write("You entered:", input_text)
        st.write("AI response will be displayed here")

