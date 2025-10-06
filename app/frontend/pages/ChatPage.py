import streamlit as st
import requests

# Config
BASE_URL = "http://127.0.0.1:18080"

# Hàm gọi API chung (giữ nguyên)
def api_call_json(url, data=None, files=None, headers=None, timeout=30):
    try:
        if files:
            response = requests.post(url, files=files, headers=headers, timeout=timeout)
        else:
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else None
        try:
            error_detail = e.response.json().get("detail", str(e)) if e.response and e.response.content else str(e)
        except:
            error_detail = str(e)
        if status == 400:
            return {"error": f"Dữ liệu không hợp lệ: {error_detail}"}
        elif status == 401:
            return {"error": "401 Unauthorized: Vui lòng đăng nhập lại hoặc kiểm tra thông tin."}
        elif status == 404:
            return {"error": f"404 Not Found: {error_detail}"}
        elif status == 422:
            return {"error": f"422 Unprocessable Entity: {error_detail}"}
        elif status == 500:
            return {"error": "Lỗi server: Vui lòng thử lại sau."}
        return {"error": f"Lỗi HTTP: {error_detail}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Lỗi kết nối: {str(e)}"}

# Hàm gửi message (giữ nguyên)
def send_message(collection_id, conversation_id, content, role="user"):
    url = f"{BASE_URL}/chat/{collection_id}/conversations/{conversation_id}/messages"
    data = {"conversation_id": conversation_id, "role": role, "content": content}
    headers = get_auth_header()
    return api_call_json(url, data=data, headers=headers)

# Lấy header auth từ session (giữ nguyên)
def get_auth_header():
    if "user" in st.session_state and st.session_state.user and st.session_state.user.get("access_token"):
        return {"Authorization": f"Bearer {st.session_state.user['access_token']}"}
    return {}

# CSS hiện đại cho chat page
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background: linear-gradient(145deg, #5b4bff 0%, #8b3cff 100%);
        padding: 1rem;
    }

    .chat-container {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        min-height: 60vh;
        max-height: 70vh;
        overflow-y: auto;
        margin-bottom: 1rem;
    }

    .message-user {
        background: linear-gradient(145deg, #5b4bff 0%, #8b3cff 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 16px 16px 4px 16px;
        margin: 10px 0;
        max-width: 75%;
        margin-left: auto;
        box-shadow: 0 3px 10px rgba(91, 75, 255, 0.3);
        animation: slideInRight 0.3s ease;
    }

    .message-user::before {
        content: "🙋🏻‍♂️";
        margin-right: 8px;
    }

    .message-assistant {
        background: #f6f9ff;
        color: #1e293b;
        padding: 12px 16px;
        border-radius: 16px 16px 16px 4px;
        margin: 10px 0;
        max-width: 75%;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        animation: slideInLeft 0.3s ease;
    }

    .message-assistant::before {
        content: "👾";
        margin-right: 8px;
    }

    .stChatInput {
        background: transparent !important;
        backdrop-filter: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    .stChatInput input {
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 12px 16px 12px 40px !important;
        font-size: 15px !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="%2364748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>');
        background-repeat: no-repeat;
        background-position: 12px center;
    }

    .stChatInput input:focus {
        border-color: #5b4bff !important;
        box-shadow: 0 0 0 3px rgba(91, 75, 255, 0.25) !important;
        outline: none !important;
    }

    .action-buttons {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-top: 1rem;
    }

    .stButton > button {
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }

    .btn-clear {
        background: linear-gradient(145deg, #ff6b6b 0%, #ff8e53 100%) !important;
        color: white !important;
    }

    .btn-logout {
        background: linear-gradient(145deg, #2bcbba 0%, #0abde3 100%) !important;
        color: white !important;
    }

    .chat-container::-webkit-scrollbar {
        width: 8px;
    }

    .chat-container::-webkit-scrollbar-track {
        background: #f6f9ff;
        border-radius: 12px;
    }

    .chat-container::-webkit-scrollbar-thumb {
        background: linear-gradient(145deg, #5b4bff 0%, #8b3cff 100%);
        border-radius: 12px;
    }

    @keyframes slideInRight {
        from { transform: translateX(50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    @keyframes slideInLeft {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Kiểm tra trạng thái đăng nhập (giữ nguyên logic)
if not st.session_state.user or not st.session_state.conversation_id:
    st.error("❌ Vui lòng đăng nhập lại.")
    if st.button("🔙 Quay về trang đăng nhập", use_container_width=True):
        st.session_state.user = None
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.switch_page("pages/LoginPage.py")
    st.stop()

# CSS cho header
st.markdown("""
<style>
.header-container {
    background: linear-gradient(135deg, #e3f2fd 0%, #b3e5fc 100%);
    backdrop-filter: blur(12px);
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    transition: all 0.3s ease;
}
.header-container h2 {
    margin: 0;
    color: #1e293b;
    font-weight: 700;
}
.header-container p {
    margin: 0;
    color: #475569;
    font-size: 0.9rem;
}
.status-badge {
    background: linear-gradient(145deg, #5b4bff 0%, #8b3cff 100%);
    padding: 8px 16px;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 6px;
}
.status-badge span {
    display: inline-block;
    width: 10px;
    height: 10px;
    background: #22c55e;
    border-radius: 50%;
}
</style>
""", unsafe_allow_html=True)

# Header hiện đại
st.markdown(f"""
<div class="header-container">
    <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div>
                <h2>💬 Xin chào, {st.session_state.user['username']}!</h2>
                <p>Trợ lý y tế thông minh</p>
            </div>
        </div>
        <div class="status-badge">
            <span></span> Đang hoạt động
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Chat container
# st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for message in st.session_state.messages:
    role = message["role"]
    if role == "user":
        st.markdown(f'''
            <div class="message-user">
                {message["content"]}
            </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
            <div class="message-assistant">
                {message["content"]}
            </div>
        ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("💭 Nhập câu hỏi y tế của bạn...", key="chat_input")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.markdown(f'''
        <div class="message-user">
            {user_input}
        </div>
    ''', unsafe_allow_html=True)

    with st.spinner("🤖 AI đang phân tích và trả lời..."):
        result = send_message(st.session_state.collection_id, st.session_state.conversation_id, user_input)
        if "content" in result:
            reply = result["content"]
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.markdown(f'''
                <div class="message-assistant">
                    {reply}
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.error(f"❌ {result.get('error', 'Lỗi khi gửi tin nhắn!')}")

# Action buttons với style mới
st.markdown("""
<style>
    .stButton > button:first-child {
        background: linear-gradient(145deg, #ff6b6b 0%, #ff8e53 100%);
        color: white;
    }

    .stButton > button:last-child {
        background: linear-gradient(145deg, #2bcbba 0%, #0abde3 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
with col2:
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.user = None
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.switch_page("pages/LoginPage.py")