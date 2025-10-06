import streamlit as st
import requests
from datetime import datetime

# 🔥 THÊM PHẦN NÀY: Khởi tạo session state
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "collection_id" not in st.session_state:
    st.session_state.collection_id = 5  # Giá trị mặc định
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# Brand CSS hiện đại
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background: linear-gradient(145deg, #5b4bff 0%, #8b3cff 100%);
        min-height: 100vh;
        padding: 1rem;
    }

    .app-hero {
        text-align: center;
        margin-top: 10vh;
        padding: 2.5rem;
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
        margin-left: auto;
        margin-right: auto;
        max-width: 700px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        animation: fadeIn 1s ease;
    }

    .app-hero h1 {
        font-size: 3rem;
        background: linear-gradient(145deg, #5b4bff 0%, #8b3cff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }

    .app-hero p {
        color: #64748b;
        font-size: 1.15rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    .feature-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin-top: 2rem;
    }

    .feature-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(91, 75, 255, 0.2);
    }

    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        color: #5b4bff;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="app-hero">
    <h1>👨🏻‍⚕️ Pluto Care</h1>
    <p>Trợ lý y tế thông minh - Tư vấn sức khỏe 24/7</p>
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div>AI Thông Minh</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔒</div>
            <div>Bảo Mật Tuyệt Đối</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <div>Hỗ Trợ Tiếng Việt</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div>Phản Hồi Nhanh</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Điều hướng dựa trên trạng thái đăng nhập (GIỮ NGUYÊN LOGIC)
if st.session_state.user and st.session_state.conversation_id:
    st.switch_page("pages/ChatPage.py")
else:
    st.switch_page("pages/LoginPage.py")