import streamlit as st
from langchain_controller import LangchainController

st.title("Guardian Search")

controller = LangchainController()

user_input = st.text_input("Enter question:")

if st.button("Run"):
    if user_input:
        result = controller.answer_question(user_input)

        st.write(result.get("answer", ""))
        st.subheader("Articles Used: " + str(result.get("articles_used", 0)))
    else:
        st.warning("Enter something before running.")