import threading
import uvicorn
import streamlit as st
from langchain_controller import LangchainController

LOGO_URL = "https://cdn.brandfetch.io/idEaoqZ5uv/w/400/h/400/theme/dark/icon.png?c=1dxbfHSJFAPEGdCLU4o5B"

st.markdown(f"""
<style>
/* Title gradient style */
h1 {{
    font-size: 4rem;
    font-weight: 800;
    letter-spacing: -1px;
    text-align: center;
    background: linear-gradient(135deg, #052962, #1558aa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 2rem;
}}

/* Layout container */
.chat-container {{
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;  /* <-- spacing between logo and bubble */
    margin-top: 2rem;
    max-width: 90%;
    margin-left: auto;
    margin-right: auto;
}}

/* Logo image */
.guardian-logo {{
    width: 60px;
    height: 60px;
    border-radius: 50%;
    object-fit: contain;
    margin-top: 5px;
}}

/* Speech bubble */
.result-bubble {{
    position: relative;
    background: linear-gradient(135deg, #052962, #1558aa);
    color: white;
    padding: 1.2rem 1.5rem;
    border-radius: 20px;
    font-size: 1.1rem;
    line-height: 1.6;
    max-width: 600px;
    word-wrap: break-word;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.25);
}}

/* Arrow (speech bubble tail) */
.result-bubble::before {{
    content: "";
    position: absolute;
    top: 20px;
    left: -14px;
    width: 0;
    height: 0;
    border-top: 15px solid transparent;
    border-bottom: 15px solid transparent;
    border-right: 15px solid #052962;
}}

/* Articles Used */
.label {{
    margin-top: 1rem;
    font-size: 0.9rem;
    font-weight: bold;
    color: #ccc;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
</style>
""", unsafe_allow_html=True)

controller = LangchainController()


def run_api():
    uvicorn.run(controller.app, host="0.0.0.0", port=8001, log_level="info")


api_thread = threading.Thread(target=run_api, daemon=True)
api_thread.start()

st.title("RAGuardian")

user_input = st.text_input("Enter your question:")

if st.button("Run"):
    if user_input:
        result = controller.answer_question(user_input)
        answer = result.get("answer", "")
        articles = result.get("articles_used", 0)

        st.markdown(f"""
        <div class="chat-container">
            <img src="{LOGO_URL}" class="guardian-logo" alt="Guardian Logo">
            <div class="result-bubble">
                {answer}
            </div>
        </div>
        <div class="label">Articles Used: {articles}</div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Enter something before running.")
