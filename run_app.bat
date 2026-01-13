@echo off
start cmd /k "uvicorn backend.main:app --reload"
timeout /t 5
streamlit run frontend/app.py
