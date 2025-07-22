#!/bin/bash
source venv/bin/activate
streamlit run llm/langchain_gui.py
read -p "Press enter to exit"