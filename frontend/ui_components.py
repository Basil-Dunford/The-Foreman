import streamlit as st

def apply_custom_css():
    st.markdown("""
        <style>
        /* Hutton Construction Brand Palette - Refined */
        :root {
            --primary-color: #003C69; /* Hutton Navy */
            --accent-color: #E9B34B; /* Hutton Gold/Yellow */
            --text-primary: #1A1A1A; /* Near Black for readability */
            --text-secondary: #4A4A4A; /* Dark Gray */
            --danger-color: #D32F2F;
            --success-color: #2E7D32;
        }

        /* Global Typography & Spacing */
        .stApp {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            letter-spacing: -0.2px;
        }
        
        h1, h2, h3 {
            color: var(--primary-color) !important;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        h1 {
            border-bottom: 4px solid var(--accent-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
            font-size: 2.2rem;
        }

        /* Sidebar Polish */
        [data-testid="stSidebar"] {
            border-right: 1px solid #D1D5DB;
            background-color: #F8F9FA;
        }
        
        /* Buttons - Industrial & Sharp */
        .stButton > button {
            color: #FFFFFF;
            background-color: var(--primary-color);
            border: 1px solid var(--primary-color);
            border-radius: 2px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 0.6rem 1.2rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            transition: all 0.2s ease-in-out;
        }

        .stButton > button:hover {
            background-color: var(--accent-color);
            color: var(--primary-color);
            border-color: var(--accent-color);
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
        }

        /* Input Fields - High Contrast */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background-color: #FFFFFF;
            color: var(--text-primary);
            border: 1px solid #9CA3AF;
            border-radius: 2px;
        }
        
        .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 1px var(--primary-color);
        }

        /* Chat Messages */
        .stChatMessage {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-left: 5px solid var(--accent-color);
            border-radius: 4px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        /* Risk Cards - Enhanced Visibility */
        .risk-card {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 4px;
            padding: 1.5rem;
            border-left: 6px solid var(--primary-color);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin-bottom: 1rem;
        }
        .risk-high { border-left-color: var(--danger-color); }
        .risk-med { border-left-color: var(--accent-color); }
        .risk-low { border-left-color: var(--success-color); }
        
        strong {
            color: var(--primary-color);
            font-weight: 700;
        }
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #F3F4F6;
            border-radius: 4px 4px 0 0;
            padding: 10px 20px;
            color: #6B7280;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF;
            color: var(--primary-color);
            font-weight: bold;
            border-top: 3px solid var(--primary-color);
        }
        
        </style>
    """, unsafe_allow_html=True)

def render_header():
    col1, col2 = st.columns([1, 6])
    with col1:
        # Placeholder for a simplified logo using the brand colors
        st.markdown(
            """
            <div style='background-color: #003C69; color: #E9B34B; 
            width: 60px; height: 60px; display: flex; align-items: center; 
            justify_content: center; font-size: 30px; font-weight: bold; 
            border-radius: 5px;'>H</div>
            """, 
            unsafe_allow_html=True
        )
    with col2:
        st.title("THE FOREMAN")
        st.caption("powered by Hutton Construction Intelligence")

def risk_card(risk_flag):
    st.markdown(f"""
    <div class="risk-card risk-med">
        <strong>⚠️ HUTTON RISK ASSESSMENT</strong>
        <p style="color: #565A5C;">{risk_flag}</p>
    </div>
    """, unsafe_allow_html=True)
