import asyncio
import threading
import uvicorn
import streamlit as st
from llm_utils.langchain_pipeline import Database
from llm_utils.langchain_controller import LangchainController, BatchQuestionRequest, MultiBatchRequest

LOGO_URL = "https://cdn.brandfetch.io/idEaoqZ5uv/w/400/h/400/theme/dark/icon.png?c=1dxbfHSJFAPEGdCLU4o5B"
LOADING_URL = "https://cdn.pixabay.com/animation/2025/04/08/09/08/09-08-31-655_512.gif"

# Database options - customize these based on your available databases
DATABASE_OPTIONS = [
    db.value[0] for db in Database
]

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

.stTextArea > div > div > textarea {{
  padding: 8px 12px;
  font-size: 16px;
  border-radius: 6px;
  border: 1.5px solid #ccc;
  transition: border 0.1s ease;
}}

.stSelectbox > div > div > div {{
  height: 38px;
  padding: 8px 12px;
  font-size: 16px;
  border-radius: 6px;
  border: 1.5px solid #ccc;
  transition: border 0.1s ease;
}}

.stTextInput > div > div > input:focus, 
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > div:focus {{
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

button[data-baseweb="tab"] {{
    color: #ccc !important;  /* Inactive tab color */
    font-weight: 600;
    border-bottom: 2px solid transparent;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    background: linear-gradient(135deg, #052962, #1558aa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    border-bottom: 2px solid #1558aa;
}}

.database-info {{
    background: rgba(5, 41, 98, 0.1);
    border: 1px solid rgba(21, 88, 170, 0.3);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    margin-top: 0.5rem;
    font-size: 0.85rem;
    color: #666;
}}

</style>
""", unsafe_allow_html=True)

controller = LangchainController()

def run_api():
    try:
        uvicorn.run(controller.app, host="0.0.0.0", port=8001, log_level="info")
    except OSError as e:
        if "address already in use" in str(e):
            print("Port 8001 is in use, trying port 8002...")
            uvicorn.run(controller.app, host="0.0.0.0", port=8002, log_level="info")
        else:
            raise e

api_thread = threading.Thread(target=run_api, daemon=True)
api_thread.start()

st.title("RAGuardian")

tab1, tab2, tab3 = st.tabs(["Single Query", "Bulk Query", "Multi Query"])

with tab1:
    col1, col2 = st.columns([7, 1])
    with col1:
        user_input = st.text_input("Question", placeholder="Enter your question", key="user_input", label_visibility="collapsed")
        
        # Database selection with dropdown
        col_db1, col_db2 = st.columns([2, 3])
        with col_db1:
            selected_db = st.selectbox(
                "Database", 
                options=DATABASE_OPTIONS,
                index=0,  # Default to first option (guardian)
                key="db_select"
            )
        
        with col_db2:
            # Show custom input field if "custom" is selected
            if selected_db == "custom":
                custom_db = st.text_input(
                    "Custom Database Name", 
                    placeholder="Enter custom database name",
                    key="custom_db_input"
                )
                final_db = custom_db if custom_db else "guardian"
            else:
                final_db = selected_db
                # Show info about selected database)
    
    with col2:
        run_button = st.button("Run", key="run_single_query")

    if run_button:
        if user_input:
            placeholder = st.empty()

            placeholder.markdown(f'''
                <div id="loading" style="display:flex; flex-direction: column; justify-content:center; align-items: center; margin: 20px 0;">
                    <img src="{LOADING_URL}" width="300" style="border-radius: 12px;"/>
                    <div class="label">RAGuardian is thinking...</div>
                </div>
            ''', unsafe_allow_html=True)

            # Pass final_db as the database parameter
            result = controller.answer_question(user_input, database=final_db)

            response = result
            time_taken = response.get('total_duration')
            answer = response.get("answer").get("answer", "")
            context = response.get("answer").get("context", [])

            placeholder.markdown(f'''
                <div class="chat-container answer-fadein" style="opacity:0;">
                    <img src="{LOGO_URL}" class="guardian-logo" alt="Guardian Logo">
                    <div class="result-bubble">
                        {answer}
                    </div>
                </div>
                <div class="label answer-fadein">Database: {final_db}</div>
                <div class="label answer-fadein">Articles Used: {len(context)}</div>
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

with tab2:
    config_col1, config_col2, config_col3, config_col4 = st.columns(4)
    with config_col1:
        batch_size = st.number_input("Batch Size", key="batch_size", min_value=1, max_value=100, value=10)
    with config_col2:
        max_workers = st.number_input("Max Workers", key="batch_workers", min_value=1, max_value=10, value=2)
    with config_col3:
        run_id = st.text_input("Run ID", value="test-run-1")
    with config_col4:
        batch_db = st.selectbox(
            "Database", 
            options=DATABASE_OPTIONS,
            index=0,
            key="batch_db_select"
        )

    query_col, button_col = st.columns([7, 1])
    with query_col:
        query = st.text_input("Batch Query", placeholder="Enter your batch query", key="batch_query", label_visibility="collapsed")
        
        # Handle custom database for batch
        if batch_db == "custom":
            batch_custom_db = st.text_input(
                "Custom Database Name", 
                placeholder="Enter custom database name",
                key="batch_custom_db_input"
            )
            final_batch_db = batch_custom_db if batch_custom_db else "guardian"
        else:
            final_batch_db = batch_db
    
    with button_col:
        run_batch_button = st.button("Run", key="run_batch_query")

    if run_batch_button:
        if query:
            placeholder = st.empty()
            placeholder.markdown(f'''
                <div id="loading" style="display:flex; flex-direction: column; justify-content:center; align-items: center; margin: 20px 0;">
                    <img src="{LOADING_URL}" width="300" style="border-radius: 12px;"/>
                    <div class="label">RAGuardian is thinking...</div>
                </div>
            ''', unsafe_allow_html=True)

            request = BatchQuestionRequest(
                query=query,
                batch_size=batch_size,
                max_workers=max_workers,
                run_id=run_id,
                database=final_batch_db  # Pass the selected database
            )

            # Pass database parameter if your controller supports it
            result = asyncio.run(controller.answer_question_batch(request))
 
            placeholder.empty()

            # Add error handling
            if result.get("status") == "error":
                st.error(f"Error in batch processing: {result.get('error', 'Unknown error')}")
                st.stop()

            answers = result.get("answers", [])
            total_duration = result.get("total_duration", 0)
            placeholder.markdown(f'''
                <div class="label answer-fadein">Database: {final_batch_db}</div>
                <div class="label answer-fadein">Batch Size: {batch_size}</div>
                <div class="label answer-fadein">Time Taken: {total_duration:.2f} seconds</div>
            ''', unsafe_allow_html=True)

            for i, answer in enumerate(answers):
                context = answer.get("context", [])
                answer_text = answer.get("answer", "")
                placeholder.markdown(f'''
                    <div class="chat-container answer-fadein" style="opacity:0;">
                        <img src="{LOGO_URL}" class="guardian-logo" alt="Guardian Logo">
                        <div class="result-bubble">
                            <b>Sample Answer {i+1}</b><br>{answer_text}
                        </div>
                    </div>
                    <div class="label answer-fadein">Articles Used: {len(context)}</div>
                ''', unsafe_allow_html=True)

                context_html = f'<div class="context-box"><div class="label">Context {i+1}</div><br>'
                for article in context:
                    title = article.get("title", "Untitled")
                    url = article.get("url", "#")
                    context_html += f'<a class="context-link" href="{url}" target="_blank">{title}</a>'
                context_html += '</div>'
                st.markdown(context_html, unsafe_allow_html=True)
        else:
            st.warning("Enter something before running.")

with tab3:
    config_col1, config_col2, config_col3 = st.columns(3)
    with config_col1:
        max_workers_multi = st.number_input("Max Workers", key="multi_workers", min_value=1, max_value=10, value=2)
    with config_col2:
        run_id_multi = st.text_input("Run ID", value="multi-batch-run", key="multi_run_id")
    with config_col3:
        multi_db = st.selectbox(
            "Database", 
            options=DATABASE_OPTIONS,
            index=0,
            key="multi_db_select"
        )

    query_input = st.text_area("Multi Queries", key="multi_query", height=200, placeholder="Enter one query per line", label_visibility="collapsed")
    
    # Handle custom database for multi query
    if multi_db == "custom":
        multi_custom_db = st.text_input(
            "Custom Database Name", 
            placeholder="Enter custom database name",
            key="multi_custom_db_input"
        )
        final_multi_db = multi_custom_db if multi_custom_db else "guardian"
    else:
        final_multi_db = multi_db

    run_multi_button = st.button("Run", key="run_multi_query")

    if run_multi_button:
        queries = [line.strip() for line in query_input.strip().splitlines() if line.strip()]
        if queries:
            placeholder = st.empty()
            placeholder.markdown(f'''
                <div id="loading" style="display:flex; flex-direction: column; justify-content:center; align-items: center; margin: 20px 0;">
                    <img src="{LOADING_URL}" width="300" style="border-radius: 12px;"/>
                    <div class="label">RAGuardian is thinking...</div>
                </div>
            ''', unsafe_allow_html=True)

            request = MultiBatchRequest(
                queries=queries,
                max_workers=max_workers_multi,
                run_id=run_id_multi,
                database=final_multi_db  # Pass the selected database
            )

            # Pass database parameter if your controller supports it
            result = asyncio.run(controller.answer_questions_multi_batch(request))

            placeholder.empty()

            # Add error handling
            if result.get("status") == "error":
                st.error(f"Error in multi-batch processing: {result.get('error', 'Unknown error')}")
                st.stop()

            answers = result.get("results", [])
            total_duration = result.get("total_duration", 0)

            st.markdown(f'''
                <div class="label answer-fadein">Database: {final_multi_db}</div>
                <div class="label answer-fadein">Queries: {len(queries)}</div>
                <div class="label answer-fadein">Time Taken: {total_duration:.2f} seconds</div>
            ''', unsafe_allow_html=True)

            for i, item in enumerate(answers):
                query_text = item.get("query", "")
                answer_data = item.get("answer", {})
                answer_text = answer_data.get("answer", "")
                context = answer_data.get("context", [])

                st.markdown(f'''
                    <div class="chat-container answer-fadein" style="opacity:0;">
                        <img src="{LOGO_URL}" class="guardian-logo" alt="Guardian Logo">
                        <div class="result-bubble">
                            <b>Q{i+1}: {query_text}</b><br>{answer_text}
                        </div>
                    </div>
                    <div class="label answer-fadein">Articles Used: {len(context)}</div>
                ''', unsafe_allow_html=True)

                context_html = f'<div class="context-box"><div class="label">Context {i + 1}</div><br>'
                for article in context:
                    title = article.get("title", "Untitled")
                    url = article.get("url", "#")
                    context_html += f'<a class="context-link" href="{url}" target="_blank">{title}</a>'
                context_html += '</div>'
                st.markdown(context_html, unsafe_allow_html=True)
        else:
            st.warning("Please enter at least one valid query.")