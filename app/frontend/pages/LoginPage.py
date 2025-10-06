import streamlit as st
import requests
from datetime import datetime

# 🔥 QUAN TRỌNG: Khởi tạo session state ở ĐẦU TIÊN, trước mọi thứ khác
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "collection_id" not in st.session_state:
    st.session_state.collection_id = 5  # Giá trị mặc định
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# Config (giữ nguyên)
BASE_URL = "http://127.0.0.1:18080"
AUTH_REGISTER_URL = f"{BASE_URL}/auth/register"
AUTH_LOGIN_URL = f"{BASE_URL}/auth/login"
COLLECTION_URL = f"{BASE_URL}/kb_collections/collections/"
FAQ_UPLOAD_URL = f"{BASE_URL}/kb_faq/{{collection_id}}/faqs/upload"

# Các hàm API (giữ nguyên hoàn toàn)
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

def api_call_form(url, data=None, headers=None, timeout=30):
    try:
        response = requests.post(url, data=data, headers=headers, timeout=timeout)
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
            return {"error": "Tên đăng nhập hoặc mật khẩu không đúng."}
        elif status == 422:
            return {"error": f"422 Unprocessable Entity: {error_detail}"}
        elif status == 500:
            return {"error": "Lỗi server: Vui lòng thử lại sau."}
        return {"error": f"Lỗi HTTP: {error_detail}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Lỗi kết nối: {str(e)}"}

def register_user(username, password, role, date_of_birth, phone, email):
    try:
        datetime.strptime(date_of_birth, "%Y-%m-%d")
        data = {
            "username": username,
            "password": password,
            "role": role,
            "date_of_birth": date_of_birth,
            "phone": phone,
            "email": email
        }
        return api_call_json(AUTH_REGISTER_URL, data=data)
    except ValueError:
        return {"error": "Ngày sinh phải có định dạng YYYY-MM-DD"}

def login_user(username, password):
    data = {"username": username, "password": password}
    return api_call_form(AUTH_LOGIN_URL, data=data)

def create_collection(name, description, language="vi"):
    data = {"name": name, "description": description, "language": language}
    return api_call_json(COLLECTION_URL, data=data)

def upload_faq_file(collection_id, file):
    files = {"file": (file.name, file.getvalue(), "application/json")}
    return api_call_json(FAQ_UPLOAD_URL.format(collection_id=collection_id), files=files)

def create_conversation(collection_id, topic="Healthcare Chat"):
    url = f"{BASE_URL}/chat/{collection_id}/conversations"
    data = {"topic": topic}
    return api_call_json(url, data=data)

# CSS hiện đại
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

    .auth-container {
        max-width: 900px;
        margin: 2rem auto;
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: transparent;
        padding: 0.5rem;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        background: #f6f9ff;
        border-radius: 10px;
        padding: 12px 20px;
        font-weight: 600;
        color: #64748b;
        border: 1px solid #e2e8f0;
        flex: 1;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: #e2e8f0;
        color: #1e293b;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(145deg, #5b4bff 0%, #8b3cff 100%);
        color: white;
        border: none;
    }

    .form-container {
        background: white;
        padding: 1.5rem;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.05);
    }

    .stTextInput input, .stTextInput textarea, .stSelectbox select, .stNumberInput input {
        border: 2px solid #e5e7eb !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        font-size: 15px !important;
        transition: all 0.3s ease;
    }

    .stTextInput input:focus, .stTextInput textarea:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border-color: #5b4bff !important;
        box-shadow: 0 0 0 3px rgba(91, 75, 255, 0.1) !important;
    }

    .stButton > button {
        width: 100%;
        background: linear-gradient(145deg, #5b4bff 0%, #8b3cff 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 15px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(91, 75, 255, 0.3);
    }

    .badge {
        display: inline-block;
        padding: 8px 16px;
        background: linear-gradient(145deg, #5b4bff 0%, #8b3cff 100%);
        color: white;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 1.5rem;
    }

    .feature-card {
        background: linear-gradient(145deg, #5b4bff 0%, #8b3cff 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 14px;
        text-align: center;
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(91, 75, 255, 0.3);
    }

    .toast {
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        animation: slideInToast 0.5s ease, fadeOutToast 0.5s ease 2s forwards;
    }

    .toast-success {
        background: linear-gradient(145deg, #2bcbba 0%, #0abde3 100%);
    }

    .toast-error {
        background: linear-gradient(145deg, #ff6b6b 0%, #ff8e53 100%);
    }

    @keyframes slideInToast {
        from { transform: translateY(100px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }

    @keyframes fadeOutToast {
        from { opacity: 1; }
        to { opacity: 0; }
    }
</style>
""", unsafe_allow_html=True)

# Main container
with st.container():
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h1 style="color: white; font-size: 2.8rem; font-weight: 700; animation: fadeIn 1s ease;">👨🏻‍⚕️ Pluto Care</h1>
        <p style="color: rgba(255, 255, 255, 0.9); font-size: 1.1rem; animation: fadeIn 1.2s ease;">Trợ lý y tế thông minh - Đồng hành sức khỏe của bạn</p>
    </div>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
    """, unsafe_allow_html=True)

    #st.markdown('<div class="auth-container">', unsafe_allow_html=True)

    # Collection badge
    #st.markdown(f'<div class="badge">Collection #{st.session_state.collection_id}</div>',
                #unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "📁 Tạo Collection", "📤 Upload FAQ"])

    with tab1:
        #st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.subheader("🔐 Đăng nhập hệ thống")
        with st.form("login_form"):
            login_username = st.text_input("👤 Tên đăng nhập", placeholder="username")
            login_password = st.text_input("🔒 Mật khẩu", type="password", placeholder="password")
            submitted = st.form_submit_button("Đăng nhập", use_container_width=True)
            if submitted:
                if not login_username or not login_password:
                    st.markdown('<div class="toast toast-error">❌ Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.</div>', unsafe_allow_html=True)
                else:
                    with st.spinner("🔄 Đang xác thực thông tin..."):
                        result = login_user(login_username, login_password)
                        if "access_token" in result:
                            st.session_state.user = {"username": login_username, "access_token": result["access_token"]}
                            with st.spinner("💬 Đang khởi tạo cuộc trò chuyện..."):
                                conversation_result = create_conversation(st.session_state.collection_id)
                                if "conversation_id" in conversation_result:
                                    st.session_state.conversation_id = conversation_result["conversation_id"]
                                    st.markdown('<div class="toast toast-success">✅ Đăng nhập và tạo cuộc trò chuyện thành công!</div>', unsafe_allow_html=True)
                                    st.switch_page("pages/ChatPage.py")
                                else:
                                    st.markdown(f'<div class="toast toast-error">❌ {conversation_result.get("error", "Không thể tạo cuộc trò chuyện! Kiểm tra collection_id=5 có tồn tại.")}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="toast toast-error">❌ {result.get("error", "Đăng nhập thất bại!")}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        #st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.subheader("📋 Tạo tài khoản mới")
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                reg_username = st.text_input("👤 Tên đăng nhập", placeholder="username")
                reg_password = st.text_input("🔒 Mật khẩu", type="password", placeholder="password")
                reg_role = st.selectbox("Vai trò", ["user", "adviser"], help="Chọn vai trò phù hợp")
            with col2:
                reg_dob = st.text_input("📅 Ngày sinh", placeholder="YYYY-MM-DD")
                reg_phone = st.text_input("📞 Số điện thoại", placeholder="phone number")
                reg_email = st.text_input("📧 Email", placeholder="email")

            submitted = st.form_submit_button("✨ Đăng ký tài khoản", use_container_width=True)
            if submitted:
                if not all([reg_username, reg_password, reg_dob, reg_phone, reg_email]):
                    st.markdown('<div class="toast toast-error">❌ Vui lòng điền đầy đủ thông tin.</div>', unsafe_allow_html=True)
                else:
                    with st.spinner("🔄 Đang tạo tài khoản..."):
                        result = register_user(reg_username, reg_password, reg_role, reg_dob, reg_phone, reg_email)
                        if "username" in result:
                            st.markdown(f'<div class="toast toast-success">✅ Đăng ký thành công cho {reg_username}! Hãy đăng nhập.</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="toast toast-error">❌ {result.get("error", "Đăng ký thất bại!")}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        #st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.subheader("📁 Tạo Collection Mới")
        with st.form("create_collection_form"):
            col_name = st.text_input("🏷️ Tên Collection", placeholder="Tên bộ sưu tập kiến thức")
            col_description = st.text_area("📝 Mô tả", placeholder="Mô tả ngắn gọn về collection", height=100)
            col_language = st.selectbox("🌐 Ngôn ngữ", ["vi", "en"], help="Chọn ngôn ngữ chính")
            submitted = st.form_submit_button("🚀 Tạo Collection", use_container_width=True)
            if submitted:
                if col_name and col_description:
                    with st.spinner("🔄 Đang tạo collection..."):
                        result = create_collection(col_name, col_description, col_language)
                        if "collection_id" in result:
                            st.session_state.collection_id = result["collection_id"]
                            st.markdown(f'<div class="toast toast-success">✅ Tạo collection "{col_name}" thành công! ID: {result["collection_id"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="toast toast-error">❌ {result.get("error", "Tạo collection thất bại!")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="toast toast-error">❌ Vui lòng điền đầy đủ tên và mô tả.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        #st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.subheader("📤 Upload Dữ Liệu FAQ")
        with st.form("upload_faq_form"):
            faq_collection_id = st.number_input("🔢 Collection ID", min_value=1,
                                                value=st.session_state.collection_id,
                                                help="ID của collection để upload")
            faq_file = st.file_uploader("📄 Chọn file JSON FAQ", type=["json"],
                                        help="File JSON chứa Q&A theo định dạng {ext_id, question, answer, ...}")
            submitted = st.form_submit_button("📤 Upload FAQ", use_container_width=True)
            if submitted:
                if faq_file:
                    with st.spinner("🔄 Đang xử lý file FAQ..."):
                        result = upload_faq_file(faq_collection_id, faq_file)
                        if isinstance(result, list) and len(result) > 0:
                            st.markdown(f'<div class="toast toast-success">✅ Upload {len(result)} FAQs thành công!</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="toast toast-error">❌ {result.get("error", "Upload FAQ thất bại!")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="toast toast-error">❌ Vui lòng chọn file JSON.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Feature cards
st.markdown("""
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 2rem;">
    <div class="feature-card">
        <div style="font-size: 2rem;">🤖</div>
        <h3>AI Thông Minh</h3>
        <p>Công nghệ AI tiên tiến nhất</p>
    </div>
    <div class="feature-card">
        <div style="font-size: 2rem;">🔒</div>
        <h3>Bảo Mật</h3>
        <p>Dữ liệu được mã hóa an toàn</p>
    </div>
    <div class="feature-card">
        <div style="font-size: 2rem;">💬</div>
        <h3>Tiếng Việt</h3>
        <p>Hỗ trợ ngôn ngữ tiếng Việt</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Xử lý conversation lỗi
if st.session_state.user and not st.session_state.conversation_id:
    st.markdown('<div class="toast toast-error">⚠️ Không thể tạo cuộc trò chuyện. Kiểm tra collection_id và thử lại.</div>', unsafe_allow_html=True)
    if st.button("🔄 Thử tạo lại conversation", use_container_width=True):
        conversation_result = create_conversation(st.session_state.collection_id)
        if "conversation_id" in conversation_result:
            st.session_state.conversation_id = conversation_result["conversation_id"]
            st.markdown('<div class="toast toast-success">✅ Tạo cuộc trò chuyện thành công!</div>', unsafe_allow_html=True)
            st.switch_page("pages/ChatPage.py")
        else:
            st.markdown(f'<div class="toast toast-error">❌ {conversation_result.get("error", "Vẫn thất bại!")}</div>', unsafe_allow_html=True)