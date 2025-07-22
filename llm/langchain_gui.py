import threading
import uvicorn
import streamlit as st
from langchain_controller import LangchainController

LOGO_URL = "https://cdn.brandfetch.io/idEaoqZ5uv/w/400/h/400/theme/dark/icon.png?c=1dxbfHSJFAPEGdCLU4o5B"
LOADING_URL = "https://cdn.pixabay.com/animation/2025/04/08/09/08/09-08-31-655_512.gif"

# --- Custom styles ---
st.markdown(f"""
<style>
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

.chat-container {{
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
    margin-top: 2rem;
    max-width: 90%;
    margin-left: auto;
    margin-right: auto;
}}

.guardian-logo {{
    width: 60px;
    height: 60px;
    border-radius: 50%;
    object-fit: contain;
    margin-top: 5px;
}}

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

.label {{
    margin-top: 1rem;
    font-size: 0.9rem;
    font-weight: bold;
    color: #ccc;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

[data-testid="stToolbar"] {{
    background: linear-gradient(135deg, #052962, #1558aa) !important;
}}

[data-testid="stToolbar"] * {{
    color: white !important;
}}

@keyframes fadeMoveDown {{
  0% {{opacity: 1; transform: translateY(0);}}
  100% {{opacity: 0; transform: translateY(20px);}}
}}

@keyframes fadeMoveUp {{
  0% {{opacity: 0; transform: translateY(20px);}}
  100% {{opacity: 1; transform: translateY(0);}}
}}

.loading-fadeout {{
  animation: fadeMoveDown 0.5s forwards;
}}

.answer-fadein {{
  animation: fadeMoveUp 0.5s forwards;
}}

.stApp > div[data-testid="column"]:nth-child(1),
.stApp > div[data-testid="column"]:nth-child(2) {{
    display: flex;
    align-items: center;
}}

.stTextInput > div > div > input {{
  height: 38px;
  padding: 8px 12px;
  font-size: 16px;
  border-radius: 6px;
  border: 1.5px solid #ccc;
  transition: border 0.1s ease;
}}

.stTextInput > div > div > input:focus {{
  outline: none;
  border: none;
  background-image: linear-gradient(white, white), linear-gradient(135deg, #052962, #1558aa);
  background-origin: border-box;
  background-clip: padding-box, border-box;
  border: 3px solid transparent;
}}

.stButton > button {{
  height: 38px;
  margin-top: 0 !important;
  font-size: 16px;
  padding: 0 25px;
  background: linear-gradient(135deg, #052962, #1558aa);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.3s ease;
}}

span[data-testid="stTextInputInstructions"],
[data-testid="stDecoration"] {{
    display: none !important;
}}

.context-box {{
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin-top: 2rem;
    color: #eee;
    max-width: 1000px;
    margin-left: auto;
    margin-right: auto;
}}

.context-header {{
    font-weight: bold;
    font-size: 1.2rem;
    margin-bottom: 1rem;
}}

.context-link {{
    margin-bottom: 0.5rem;
    display: block;
    font-weight: 500;
    background: linear-gradient(135deg, #052962, #1558aa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-decoration: none;
    transition: opacity 0.2s ease;
}}
.context-link:hover {{
    opacity: 0.8;
    text-decoration: underline;
}}

</style>
""", unsafe_allow_html=True)

controller = LangchainController()

def run_api():
    uvicorn.run(controller.app, host="0.0.0.0", port=8001, log_level="info")

api_thread = threading.Thread(target=run_api, daemon=True)
api_thread.start()

st.title("RAGuardian")

col1, col2 = st.columns([7, 1])
with col1:
    user_input = st.text_input(" ", placeholder="Enter your question", key="user_input", label_visibility="collapsed")
with col2:
    run_button = st.button("Run")

if run_button:
    if user_input:
        placeholder = st.empty()

        # Show loading UI
        placeholder.markdown(f'''
            <div id="loading" style="display:flex; flex-direction: column; justify-content:center; align-items: center; margin: 20px 0;">
                <img src="{LOADING_URL}" width="300" style="border-radius: 12px;"/>
                <div class="label">RAGuardian is thinking...</div>
            </div>
        ''', unsafe_allow_html=True)

        result = controller.answer_question(user_input)

        placeholder.markdown(f'''
            <div id="loading" class="loading-fadeout" style="display:flex; flex-direction: column; justify-content:center; align-items: center; margin: 20px 0;">
                <img src="{LOADING_URL}" width="300" style="border-radius: 12px;"/>
                <div class="label">RAGuardian is thinking...</div>
            </div>
        ''', unsafe_allow_html=True)

        response = result[0]
        time_taken = result[1]
        answer = response.get("answer", "")
        articles = response.get("articles_used", 0)
        context = response.get("context", [])

        placeholder.markdown(f'''
            <div class="chat-container answer-fadein" style="opacity:0;">
                <img src="{LOGO_URL}" class="guardian-logo" alt="Guardian Logo">
                <div class="result-bubble">
                    {answer}
                </div>
            </div>
            <div class="label answer-fadein">Articles Used: {articles}</div>
            <div class="label answer-fadein">Time Taken: {time_taken:.2f} seconds</div>
        ''', unsafe_allow_html=True)

        context_html = """
        <div class="context-box">
            <div class="label">Context</div>
            <br />
        """
        for article in context:
            title = article.get("title", "Untitled")
            url = article.get("url", "#")
            context_html += f'<a class="context-link" href="{url}" target="_blank">{title}</a>'

        context_html += "</div>"
        st.markdown(context_html, unsafe_allow_html=True)
    else:
        st.warning("Enter something before running.")
