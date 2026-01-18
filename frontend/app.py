import streamlit as st
import requests
import time
import json
from ui_components import apply_custom_css, render_header, risk_card

# Configuration
API_URL = "https://the-foreman.onrender.com"

st.set_page_config(page_title="The Foreman", page_icon="🏗️", layout="wide")
apply_custom_css()

# Sidebar: Document Ingestion
with st.sidebar:
    st.header("📋 PROJECT DOCUMENTS")
    uploaded_file = st.file_uploader("Upload Construction Docs (PDF/Txt)", type=['pdf', 'txt', 'md'])
    
    if uploaded_file is not None:
        if st.button("Ingest Document"):
            with st.spinner("Chunking & Embedding..."):
                try:
                    files = {'file': (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    response = requests.post(f"{API_URL}/ingest", files=files)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Ingested {data['chunks_processed']} chunks from {data['filename']}")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")
                    st.warning("Make sure the Backend API is running!")

# Main App Logic
render_header()

tab1, tab2 = st.tabs(["💬 Semantic Search", "🔍 Hutton Risk Scouter"])

# Tab 1: Semantic Search
with tab1:
    st.markdown("### Ask about past projects")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: How did we handle moisture in 2022?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            sources = []
            
            try:
                payload = {"query": prompt, "top_k": 3}
                # Use st.status to show backend activity
                with st.status("Reading Project Docs...", expanded=True) as status:
                    response = requests.post(f"{API_URL}/query", json=payload, stream=True)
                    
                    if response.status_code == 200:
                        for line in response.iter_lines():
                            if line:
                                chunk = json.loads(line.decode('utf-8'))
                                if chunk["type"] == "status":
                                    status.update(label=chunk["content"])
                                elif chunk["type"] == "answer":
                                    full_response += chunk["content"]
                                    message_placeholder.markdown(full_response + "▌")
                                elif chunk["type"] == "source":
                                    sources = chunk["content"]
                        
                        status.update(label="✅ Analysis Complete", state="complete", expanded=False)
                        message_placeholder.markdown(full_response)
                        
                        if sources:
                            st.markdown("### 📚 Sources Used")
                            for s in sources:
                                meta = s.get('metadata', {})
                                score = s.get('score', 0.0)
                                file_name = meta.get('file_name', 'Unknown Document')
                                page_label = meta.get('page_label', 'N/A')
                                
                                with st.expander(f"📄 {file_name} - Page {page_label} (Match: {score:.2f})"):
                                    st.markdown(f"**Content:**\n\n{s['content']}")
                                    st.caption(f"Path: {meta.get('file_path', 'N/A')}")
                        
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    else:
                        status.update(label="❌ Error retrieving response", state="error")
                        message_placeholder.error(f"Failed to get response from backend: {response.text}")
            except Exception as e:
                message_placeholder.error(f"Backend unavailable: {str(e)}")

# Tab 2: Hutton Risk Scouter
with tab2:
    st.markdown("### 🛡️ Risk Assessment Mode")
    st.info("Paste a new project description to benchmark against historical 'pain points'.")
    
    project_desc = st.text_area("New Project Description", height=200, placeholder="We are building a 5-story cold storage unit in humid climate...")
    
    if st.button("Run Risk Analysis"):
        with st.spinner("Scouting risks..."):
            try:
                payload = {"project_description": project_desc}
                response = requests.post(f"{API_URL}/risk-scout", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Analysis")
                        st.write(data['analysis'])
                    
                    with col2:
                        st.subheader("Relevant Past Projects")
                        for proj in data['relevant_past_projects']:
                            st.code(proj)
                            
                        st.subheader("Potential Risks")
                        # If structure allows, loop. For now, analysis text likely covers it.
                        risk_card("Check specific details in Analysis.")
                else:
                    st.error("Analysis failed.")
            except Exception as e:
                st.error(f"Backend error: {e}")
