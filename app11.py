import streamlit as st
import google.generativeai as genai
import os
import base64
import time
import smtplib
import json
import csv
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

# --- 1. CẤU HÌNH API KEY ---
API_KEYS = [
    "AIzaSyBSH9Hg8s8_kdVTCMcjo7ULH-NZk4Tx4XA", # API Chính
    "AIzaSyBktMdWJ6QSDfK6c4VqnfOaZLtU6ZLwpn8", # API Backup 1
    "AIzaSyBgApLVBR8HTof40s4R_tuH3KKXc6TyDhA", # API Backup 2
    "AIzaSyAL3lt2KGkh1eY9UZuOCKT0HqCYImS9aFo", # API Backup 3
    "AIzaSyAPcvGxu5e0o-_BRoxBM4ilam-o-7LwzEk", # API Backup 4
]
VALID_KEYS = [k for k in API_KEYS if k]

if not VALID_KEYS:
    st.error("❌ Không tìm thấy API key hợp lệ!")
    st.stop()

# Hàm cấu hình model với key cụ thể
def configure_genai(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-flash-latest')  # 

# Khởi tạo mặc định
model = configure_genai(random.choice(VALID_KEYS))

def get_document_content(doc_name):
    """Lấy nội dung đầy đủ của một tài liệu dựa trên tên file."""
    doc_map = {
        "huong-dan.txt": "huong-dan.txt",
        "QTNNL-handbook.md": "QTNNL-handbook.md",
        "CHRO-ADVISOR": "claude-skills/c-level-advisor/chro-advisor/SKILL.md",
        "CULTURE-ARCHITECT": "claude-skills/c-level-advisor/culture-architect/SKILL.md",
        "EXECUTIVE-MENTOR": "claude-skills/c-level-advisor/executive-mentor/SKILL.md",
        "documentation-standards.md": "claude-skills/standards/documentation/documentation-standards.md"
    }
    
    # Tìm đường dẫn tương đối
    path = None
    for key in doc_map:
        if key.lower() in doc_name.lower():
            path = doc_map[key]
            break
            
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Không tìm thấy nội dung văn bản gốc."

# ===== CẤU HÌNH GMAIL =====
SENDER_EMAIL = "leedanh2005@gmail.com"
SENDER_PASSWORD = "bgoa ftww iqvr xqap"

def send_email(to_email, chat_history):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "📚 Lịch sử hội thoại - Trợ lý Sinh viên K17"
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        body = "Dưới đây là nội dung hội thoại của bạn với Trợ lý K17:\n\n"
        body += "=" * 50 + "\n\n"
        for m in chat_history:
            role = "🧑 Bạn" if m["role"] == "user" else "🤖 Trợ lý"
            body += f"{role}:\n{m['content']}\n\n"
            body += "-" * 40 + "\n\n"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        return str(e)

# ===== LƯU LOG =====
def save_to_log(question, answer, danh_gia=None):
    log_file = "chat_log.json"
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append({
        "thoi_gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cau_hoi": question,
        "cau_tra_loi": answer,
        "danh_gia": danh_gia
    })
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

# ===== LƯU CSV =====
def save_to_csv(user_name, question, answer):
    try:
        # Sử dụng đường dẫn tuyệt đối để đảm bảo lưu đúng thư mục
        csv_file = os.path.join(os.getcwd(), "chat_history.csv")
        file_exists = os.path.isfile(csv_file)
        # Sử dụng utf-8-sig để Excel nhận diện đúng tiếng Việt
        with open(csv_file, mode='a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Thời gian", "Tên người dùng", "Câu hỏi", "Câu trả lời"])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                user_name,
                question,
                answer
            ])
        return True
    except PermissionError:
        st.error("⚠️ Không thể lưu vào file CSV vì file đang được mở bởi một chương trình khác (như Excel).")
        st.info("💡 Vui lòng đóng file 'chat_history.csv' và thử lại để dữ liệu được lưu chính xác.")
        return False
    except Exception as e:
        st.error(f"❌ Lỗi khi lưu CSV: {str(e)}")
        return False

# ===== CẬP NHẬT ĐÁNH GIÁ VÀO LOG =====
def update_rating_in_log(index, danh_gia):
    log_file = "chat_log.json"
    if not os.path.exists(log_file):
        return
    with open(log_file, "r", encoding="utf-8") as f:
        logs = json.load(f)
    if index < len(logs):
        logs[index]["danh_gia"] = danh_gia
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

st.set_page_config(
    page_title="Trợ lý của Sinh viên K17",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# ===== HIGHLIGHT FUNCTION =====
def highlight_keywords(text):
    keywords = ["tín chỉ", "tốt nghiệp", "thực tập", "chuẩn đầu ra", "học phần"]
    for kw in keywords:
        text = text.replace(kw, f"**{kw}**")
        text = text.replace(kw.capitalize(), f"**{kw.capitalize()}**")
    return text

# ===== CSS =====
st.markdown(f"""
<style>
@keyframes atmospheric {{
    0% {{ background-position: 0% 0%; }}
    50% {{ background-position: 100% 100%; }}
    100% {{ background-position: 0% 0%; }}
}}
html, body, .stApp {{
    background: radial-gradient(circle at top right, #1e1b4b, #020617),
                radial-gradient(circle at bottom left, #0f172a, #020617);
    background-attachment: fixed;
    color: #f1f5f9;
}}
[data-testid="stSidebar"] {{
    background: rgba(2, 6, 23, 0.5) !important;
    backdrop-filter: blur(40px) saturate(150%);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}}
.header-container {{
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(15px);
    padding: 25px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 20px 50px rgba(0,0,0,0.4);
}}
[data-testid="stChatMessage"] > div {{
    border-radius: 24px !important;
    padding: 20px 25px !important;
    margin-bottom: 12px !important;
    font-size: 15px;
    line-height: 1.6;
}}
[data-testid="stChatMessage"]:not([data-testid*="user"]) > div {{
    background: rgba(15, 23, 42, 0.9) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(167, 139, 250, 0.2) !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}}
[data-testid="stChatMessage"][data-testid*="user"] > div {{
    background: linear-gradient(135deg, #4338ca, #6d28d9) !important;
    box-shadow: 0 10px 25px rgba(99, 102, 241, 0.2);
    border: none !important;
}}
.stButton > button {{
    background: transparent !important;
    border: none !important;
    color: white !important;
    font-size: 18px !important;
    padding: 0 !important;
    min-height: unset !important;
    line-height: 1 !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    opacity: 0.8;
}}
.stButton > button:hover {{
    transform: scale(1.3) rotate(5deg) !important;
    opacity: 1 !important;
    text-shadow: 0 0 15px rgba(167, 139, 250, 0.8);
}}
.action-btn {{
    background: transparent !important;
    border: none !important;
    color: white !important;
    font-size: 18px !important;
    cursor: pointer;
    transition: all 0.3s ease;
    opacity: 0.8;
}}
.action-btn:hover {{
    transform: scale(1.3) !important;
    opacity: 1 !important;
    text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);
}}
[data-testid="stChatInput"] input {{
    background: rgba(15, 23, 42, 0.6) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 18px !important;
    color: white !important;
}}
[data-testid="stChatInput"] input:focus {{
    border: 1px solid rgba(167, 139, 250, 0.5) !important;
    box-shadow: 0 0 30px rgba(167, 139, 250, 0.2) !important;
}}
@keyframes glow-hint {{
    0% {{ color: #f87171; opacity: 0.6; }}
    50% {{ color: #fb7185; opacity: 1; text-shadow: 0 0 10px #f87171; }}
    100% {{ color: #f87171; opacity: 0.6; }}
}}
.feature-hint {{
    animation: glow-hint 3s infinite ease-in-out;
    font-size: 13px;
    font-weight: bold;
}}
.status-text {{
    font-size: 12px;
    color: #a78bfa;
    margin-bottom: 5px;
    font-weight: 500;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}
.progress-container {{
    background: rgba(255, 255, 255, 0.05);
    height: 4px;
    width: 100%;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 20px;
}}
.progress-bar {{
    background: linear-gradient(90deg, #a78bfa, #38bdf8);
    height: 100%;
    border-radius: 10px;
    box-shadow: 0 0 15px rgba(167, 139, 250, 0.6);
    transition: width 0.5s ease-in-out;
}}
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
if os.path.exists("background_due.jpg"):
    img_base64 = get_base64_image("background_due.jpg")
    st.markdown(f"""
        <div class="header-container" style="display:flex; align-items:center;">
            <div class="logo-box" style="margin-right:20px;">
                <img src="data:image/jpg;base64,{img_base64}" style="border-radius: 14px; width:60px; height:60px; object-fit: cover;" />
            </div>
            <div class="title-box">
                <h1 style="margin:0; font-size:22px; font-weight:800; letter-spacing:-0.5px;">
                    <span style="color: white;">🎓</span> 
                    <span style="background: linear-gradient(90deg, #a78bfa, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Trợ lý Sinh viên K17</span>
                </h1>
                <p style="margin:0; color:#94a3b8; font-size:12px; font-weight:500; text-transform: uppercase; letter-spacing:1px;">Intelligent Assistant Portal</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<h1 style='font-size:32px;'>🎓 <span style='background: linear-gradient(90deg, #a78bfa, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Trợ lý của Sinh viên K17</span></h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    if st.session_state.get("view_cited_text"):
        cited_content = st.session_state.view_cited_text
        lang = st.session_state.get("last_lang", "vi")
        if st.button(UI_LANG[lang]["back"], use_container_width=True):
            st.session_state.view_cited_text = None
            st.rerun()
        
        st.markdown(f"### {UI_LANG[lang]['verify']}")
        st.markdown('<div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; font-size: 14px; line-height: 1.6; color: #cbd5e1; border-left: 4px solid #a78bfa;">' + cited_content.replace("\n", "<br>") + '</div>', unsafe_allow_html=True)
        st.info(UI_LANG[lang]["verified_hint"])
    else:
        st.markdown("<h2 style='text-align: center; color: #a78bfa; font-weight:800;'>🚀 CÔNG CỤ</h2>", unsafe_allow_html=True)
# ... rest of sidebar ...

    st.markdown("### 🔍 Tìm kiếm")
    search_query = st.text_input("Từ khóa:", placeholder="Gõ để tìm...", key="sidebar_search")
    if search_query:
        handbook_path = "QTNNL-handbook.md"
        if os.path.exists(handbook_path):
            with open(handbook_path, "r", encoding="utf-8") as f:
                content = f.read()
            sections = content.split("##")
            results = [s for s in sections if search_query.lower() in s.lower()]
            for res in results[:3]:
                with st.expander(f"📖 {res.strip().splitlines()[0][:30]}..."):
                    st.markdown(res)

    st.divider()
    st.markdown("### 🔗 Links")
    c_a, c_b = st.columns(2)
    with c_a:
        st.link_button("🌐 Web", "https://due.udn.vn/", use_container_width=True)
        st.link_button("📊 Tra điểm", "http://daotao.due.udn.vn/", use_container_width=True)
    with c_b:
        st.link_button("📚 HR", "https://sites.google.com/view/quantringuonnhanluc", use_container_width=True)
        st.link_button("🏢 QTKD", "https://due.udn.vn/vi-vn/khoa/quan-tri-kinh-doanh", use_container_width=True)

    st.divider()
    if st.button("🗑️ Xóa lịch sử", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    with st.expander("🛠️ Admin"):
        admin_pw = st.text_input("Pass:", type="password")
        if st.button("Logs", use_container_width=True):
            if admin_pw == "0913" and os.path.exists("chat_log.json"):
                with open("chat_log.json", "r", encoding="utf-8") as f:
                    st.write(f"Tổng: {len(json.load(f))}")

# ===== JS COPY =====
st.markdown("""
<script>
function copyText(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const textToCopy = el.innerText || el.textContent;
    navigator.clipboard.writeText(textToCopy).then(function() {
        const btn = document.getElementById('copybtn_' + id);
        if (btn) {
            btn.innerHTML = '✅';
            setTimeout(function() { btn.innerHTML = '📋'; }, 2000);
        }
    });
}
</script>
""", unsafe_allow_html=True)

# --- DATA & CHAT STATE ---
import re

UI_LANG = {
    "vi": {
        "analyzing": "🧠 Chuyên gia AI đang phân tích...",
        "scanning": "🔍 Đang quét tri thức Handbook & Skills...",
        "scanning_std": "🔍 Đang quét tri thức Handbook & Standards...",
        "finalizing": "✅ Hoàn tất!",
        "writing": "✍️ Đang soạn câu trả lời...",
        "source": "📖 Cơ sở văn bản",
        "verify": "🔍 Đối chiếu văn bản gốc",
        "back": "⬅️ Quay lại Công cụ",
        "view_source_hint": "Bấm vào các nút dưới đây để đối chiếu từng nguồn:",
        "verified_hint": "💡 Đây là đoạn văn bản gốc mà AI đã trích dẫn để đưa ra câu trả lời."
    },
    "en": {
        "analyzing": "🧠 AI Expert is analyzing...",
        "scanning": "🔍 Scanning Handbook & Skills knowledge...",
        "scanning_std": "🔍 Scanning Handbook & Standards knowledge...",
        "finalizing": "✅ Completed!",
        "writing": "✍️ Drafting response...",
        "source": "📖 Source Information",
        "verify": "🔍 Verify Source Text",
        "back": "⬅️ Back to Tools",
        "view_source_hint": "Click the buttons below to verify each source:",
        "verified_hint": "💡 This is the original text cited by the AI for its response."
    }
}

def detect_language(text):
    """Nhận diện ngôn ngữ: Ưu tiên tiếng Việt nếu có dấu hoặc từ vựng tiếng Việt."""
    # 1. Kiểm tra ký tự có dấu
    vi_chars = "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
    if any(c in vi_chars for c in text.lower()):
        return "vi"
    
    # 2. Kiểm tra từ vựng tiếng Việt không dấu phổ biến
    vi_words = {
        "hoc", "sinh", "vien", "nganh", "nghe", "tot", "nghiep", "dang", "ky", 
        "tin", "chi", "truong", "co", "va", "nhung", "la", "cua", "trong", 
        "cho", "duoc", "nguoi", "khong", "phai", "nao", "dau", "sao", "nay", "thi", "lam"
    }
    words = set(re.findall(r'\b\w+\b', text.lower()))
    if words.intersection(vi_words):
        return "vi"
        
    return "en"

def parse_citations(text):
    """Phân tách phần trích dẫn nguồn thành từ mục riêng lẻ."""
    if "---TRÍCH DẪN NGUỒN---" not in text:
        return {}
    
    source_section = text.split("---TRÍCH DẪN NGUỒN---")[1].strip()
    # Tìm các mục dạng [n] Nội dung
    pattern = r"\[(\d+)\](.*?)(?=\s*\[\d+\]|$)"
    matches = re.findall(pattern, source_section, re.DOTALL)
    
    citations = {}
    for num, content in matches:
        citations[num] = content.strip()
    return citations

def get_document_content(doc_name):
# ... rest of helper functions ...
    """Lấy nội dung đầy đủ của một tài liệu dựa trên tên file."""
    doc_map = {
        "huong-dan.txt": "huong-dan.txt",
        "QTNNL-handbook.md": "QTNNL-handbook.md",
        "CHRO-ADVISOR": "claude-skills/c-level-advisor/chro-advisor/SKILL.md",
        "CULTURE-ARCHITECT": "claude-skills/c-level-advisor/culture-architect/SKILL.md",
        "EXECUTIVE-MENTOR": "claude-skills/c-level-advisor/executive-mentor/SKILL.md",
        "documentation-standards.md": "claude-skills/standards/documentation/documentation-standards.md"
    }
    
    # Tìm đường dẫn tương đối
    path = None
    for key in doc_map:
        if key.lower() in doc_name.lower():
            path = doc_map[key]
            break
            
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Không tìm thấy nội dung văn bản gốc."

def load_knowledge_base(include_skills=False, include_standards=False):
    knowledge = ""
    # 1. Load Handbook
    files = ["huong-dan.txt", "QTNNL-handbook.md"]
    for filename in files:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
                knowledge += f"\n--- NỘI DUNG HANDBOOK ({filename}) ---\n" + "\n".join([l.strip() for l in lines if l.strip()])
    
    # 2. Load Claude Skills if requested
    if include_skills:
        skill_paths = [
            "claude-skills/c-level-advisor/chro-advisor/SKILL.md",
            "claude-skills/c-level-advisor/culture-architect/SKILL.md",
            "claude-skills/c-level-advisor/executive-mentor/SKILL.md"
        ]
        for path in skill_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    skill_name = path.split("/")[-2].upper()
                    knowledge += f"\n\n--- CHUYÊN GIA KỸ NĂNG: {skill_name} ---\n{content}"
    
    # 3. Load Standards if requested
    if include_standards:
        std_path = "claude-skills/standards/documentation/documentation-standards.md"
        if os.path.exists(std_path):
            with open(std_path, "r", encoding="utf-8") as f:
                content = f.read()
                knowledge += f"\n\n--- TIÊU CHUẨN TRÌNH BÀY VĂN BẢN ---\n{content}"
                
    return knowledge

if "messages" not in st.session_state:
    st.session_state.messages = []
if "ratings" not in st.session_state:
    st.session_state.ratings = {}
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "📍 Chế độ Tra cứu (Nghiêm ngặt)"

# ===== NHẬP TÊN NGƯỜI DÙNG =====
if "user_name" not in st.session_state:
    st.markdown("""
        <div style='background: rgba(255, 255, 255, 0.05); padding: 30px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; margin-top: 50px;'>
            <h2 style='color: #a78bfa;'>👋 Chào mừng bạn đến với Trợ lý K17!</h2>
            <p style='color: #94a3b8;'>Để bắt đầu cuộc trò chuyện, vui lòng cho mình biết tên của bạn:</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name = st.text_input("Tên của bạn:", key="input_user_name", placeholder="Ví dụ: Nguyễn Văn A")
        if st.button("🚀 Bắt đầu ngay", use_container_width=True):
            if name.strip():
                st.session_state.user_name = name.strip()
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập tên để tiếp tục!")
    st.stop()

# ===== LỜI CHÀO =====
if len(st.session_state.messages) == 0:
    loi_chao = """
Chào các bạn, mình là AI Chatbot do sinh viên Lê Công Danh lớp Tuyển dụng 49K17.2 xây dựng nhằm đồng hành và cung cấp thông tin cho những học sinh đang quan tâm đến ngành Quản trị Nhân lực tại Trường Đại học Kinh tế – Đại học Đà Nẵng. Mình sẽ giúp các bạn tìm hiểu rõ hơn về ngành học, chương trình đào tạo và những nội dung liên quan trong quá trình lựa chọn.

---
💡 **HỖ TRỢ TỐT NHẤT:**
*   🔍 **Tra cứu (Sidebar):** Xem nhanh nội dung Handbook.
*   🤖 **Hỏi đáp AI:** Giải đáp chuyên sâu mọi vấn đề.
*   ➕ **Dấu cộng (+):** Phân tích tệp tin/bảng điểm và chuyển đổi linh hoạt giữa **Chế độ Tra cứu** (Đúng quy định) & **Chế độ Tư vấn** (Định hướng nghề nghiệp).
    """
    with st.chat_message("assistant"):
        st.markdown(loi_chao)

# ===== HIỂN THỊ LỊCH SỬ =====
assistant_index = 0
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            content_parts = message["content"].split("---TRÍCH DẪN NGUỒN---")
            main_content = content_parts[0].strip()
            st.markdown(main_content)
            if len(content_parts) > 1:
                with st.expander("📖 Cơ sở văn bản"):
                    citations = parse_citations(message["content"])
                    if citations:
                        st.markdown("Bấm vào các nút dưới đây để đối chiếu từng nguồn:")
                        # Hiển thị hàng nút bấm cho từng trích dẫn
                        cols = st.columns(len(citations) if len(citations) <= 5 else 5)
                        for idx, (num, text) in enumerate(citations.items()):
                            col_idx = idx % 5
                            with cols[col_idx]:
                                if st.button(f"[{num}]", key=f"btn_{i}_{num}", use_container_width=True):
                                    st.session_state.view_cited_text = text
                                    st.rerun()
                    else:
                        st.markdown(content_parts[1].strip())
        else:
            st.markdown(message["content"])
            
    if message["role"] == "assistant":
        msg_id = f"msg_{assistant_index}"
# ... rest of history display ...
# ... rest of the history display ...
# ... rest of the display loop ...
            
    if message["role"] == "assistant":
        msg_id = f"msg_{assistant_index}"
        rating = st.session_state.ratings.get(msg_id, None)
        # Lấy nội dung chính để copy, bỏ phần trích dẫn nguồn
        full_text_for_copy = message["content"].split("---TRÍCH DẪN NGUỒN---")[0].strip()
        safe_content = (
            full_text_for_copy
            .replace('"', '&quot;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('\n', ' ')
        )

        st.markdown('<div style="margin-top: -15px;"></div>', unsafe_allow_html=True)
        c1, c2, c3, _ = st.columns([0.8, 0.8, 0.8, 9.6])
        with c1:
            if st.button("✅👍" if rating == "👍" else "👍", key=f"lk_{msg_id}"):
                st.session_state.ratings[msg_id] = "👍"
                update_rating_in_log(assistant_index, "👍")
                st.rerun()
        with c2:
            if st.button("✅👎" if rating == "👎" else "👎", key=f"dl_{msg_id}"):
                st.session_state.ratings[msg_id] = "👎"
                update_rating_in_log(assistant_index, "👎")
                st.rerun()
        with c3:
            st.markdown(
                f'<span id="content_{msg_id}" style="display:none">{safe_content}</span>'
                f'<button class="action-btn" id="copybtn_content_{msg_id}" onclick="copyText(\'content_{msg_id}\')">📋</button>',
                unsafe_allow_html=True
            )
        assistant_index += 1

# ===== THANH CHAT NÂNG CẤP (DẤU CỘNG) =====
with st.container():
    col_plus, col_hint, col_info = st.columns([0.6, 3, 6])
    with col_plus:
        with st.popover("➕", help="Thêm tính năng nâng cao"):
            st.markdown("### 🎓 Tiện ích thông minh")
            uploaded_file = st.file_uploader(
                "Phân tích bảng điểm/Ảnh (PDF/JPG/PNG)",
                type=['pdf', 'png', 'jpg'],
                key="file_analysis"
            )
            if uploaded_file:
                st.success("✅ Đã nhận tệp! Hãy đặt câu hỏi về tệp này.")

            st.divider()
            st.markdown("### ⚙️ Cấu hình AI")
            mode = st.radio(
                "Chọn chế độ trả lời:",
                ["📍 Chế độ Tra cứu (Nghiêm ngặt)", "🚀 Chế độ Tư vấn (Định hướng nghề)"],
                index=0 if "Tra cứu" in st.session_state.chat_mode else 1
            )
            if mode != st.session_state.chat_mode:
                st.session_state.chat_mode = mode
                st.rerun()
    with col_hint:
        if not st.session_state.get("file_analysis"):
            st.markdown('<span class="feature-hint">⬅️ Tính năng nâng cao</span>', unsafe_allow_html=True)
    with col_info:
        st.caption(f"Đang dùng: {st.session_state.chat_mode}")

prompt = st.chat_input("Bạn đang thắc mắc điều gì?")
if "suggested_prompt" in st.session_state:
    prompt = st.session_state.pop("suggested_prompt")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        prog_placeholder = st.empty()

        def update_prog(text, width):
            prog_placeholder.markdown(f"""
                <div class="status-text">{text}</div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {width}%;"></div>
                </div>
            """, unsafe_allow_html=True)

        # 1. Nhận diện ngôn ngữ
        is_consulting = "Tư vấn" in st.session_state.chat_mode
        lang = detect_language(prompt)
        st.session_state.last_lang = lang # Lưu để Sidebar dùng
        ui = UI_LANG[lang]

        update_prog(ui["scanning"] if is_consulting else ui["scanning_std"], 20)
        ctx = load_knowledge_base(include_skills=is_consulting, include_standards=not is_consulting)

        update_prog(ui["analyzing"], 50)

        # 2. Xây dựng Prompt theo ngôn ngữ
        lang_instruction = ""
        if lang == "en":
            lang_instruction = """
LANGUAGE REQUIREMENT: 
- The user is asking in English. 
- You MUST translate all relevant information from the Handbook and Skills into professional English.
- Your entire response, including citations, must be 100% in English. 
- Do not use any Vietnamese words in your answer."""

        if is_consulting:
            inst = f"""
(BẠN ĐANG Ở CHẾ ĐỘ TƯ VẤN: Bạn là Hội đồng Chuyên gia HR cao cấp.
Bối cảnh tri thức của bạn đã được mở rộng bằng các bộ kỹ năng chuyên sâu từ thư mục 'claude-skills'.
{lang_instruction}

NHIỆM VỤ CỦA BẠN:
1. Vận dụng 100% các khung tư duy (frameworks), quy tắc hành xử và logic chuyên môn từ 3 bộ kỹ năng.
2. Nếu có câu hỏi liên quan đến tính toán, hãy áp dụng logic từ các công cụ Python đã mô tả.
3. KHÔNG BỊ GIỚI HẠN bởi Handbook trường, hãy tư vấn như một chuyên gia thực thụ.
4. LUÔN trả lời với thái độ chuyên nghiệp, sắc bén.

5. TRÍCH DẪN NGUỒN (CỰC KỲ QUAN TRỌNG): 
- Mỗi khi đưa ra thông tin quan trọng, hãy đánh số [1], [2]... ngay sau thông tin đó. 
- Cuối bài, hãy tạo một mục bắt đầu bằng '---TRÍCH DẪN NGUỒN---'.
- Liệt kê chi tiết theo định dạng: [n] NGUYÊN VĂN CÂU VĂN (Tên file nguồn). (Nếu là English mode, hãy dịch câu trích dẫn sang English).
- TUYỆT ĐỐI KHÔNG chỉ ghi tên tiêu đề hoặc tên chương. Phải copy đúng câu chứa thông tin đó.)
            """
        else:
            inst = f"""
(BẠN ĐANG Ở CHẾ ĐỘ TRA CỨU: Bạn chỉ được phép trả lời dựa trên nội dung CÓ TRONG Handbook.
NẾU THÔNG TIN KHÔNG CÓ TRONG HANDBOOK, BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ Ý TRẢ LỜI.
{lang_instruction}

TUY NHIÊN, về mặt TRÌNH BÀY:
Hãy sử dụng 'TIÊU CHUẨN TRÌNH BÀY VĂN BẢN' để trình bày chuyên nghiệp nhất.

TRÍCH DẪN NGUỒN (CỰC KỲ QUAN TRỌNG): 
- Mỗi khi đưa ra thông tin, hãy đánh số [1], [2]... ngay sau thông tin đó. 
- Cuối bài, hãy tạo một mục bắt đầu bằng '---TRÍCH DẪN NGUỒN---'.
- Liệt kê chi tiết theo định dạng: [n] NGUYÊN VĂN CÂU VĂN (Tên file nguồn). (Nếu là English mode, hãy dịch câu trích dẫn sang English).
- TUYỆT ĐỐI KHÔNG chỉ ghi tên tiêu đề hoặc tên chương. Phải copy đúng câu văn chứa thông tin đó.)
            """

        query = [f"Bối cảnh: {ctx}\n{inst}\n\nHãy trả lời thật chi tiết và giúp ích: {prompt}"]
# ... rest of processing ...

        if st.session_state.get("file_analysis"):
            f = st.session_state.file_analysis
            query.insert(0, {"mime_type": f.type, "data": f.read()})

        success = False
        attempts = 0
        keys = VALID_KEYS.copy()
        random.shuffle(keys)

        while not success and attempts < len(keys):
            try:
                update_prog(f"✍️ Đang soạn câu trả lời (Key {attempts + 1})...", 85)
                model = configure_genai(keys[attempts])
                resp = model.generate_content(query)

                if hasattr(resp, 'text'):
                    full_text = resp.text
                    success = True
                else:
                    # Trường hợp model bị chặn do an toàn hoặc lý do khác
                    full_text = "Rất tiếc, tôi không thể trả lời câu hỏi này vì vi phạm chính sách an toàn của AI hoặc dữ liệu bị chặn."
                    success = True
            except Exception as e:
                attempts += 1
                err_msg = str(e)
                if attempts >= len(keys):
                    st.error(f"❌ Lỗi: {err_msg}")
                    if "429" in err_msg:
                        st.warning("💡 Gợi ý: Có vẻ bạn đã hết hạn ngạch API (Rate Limit). Hãy thử lại sau 1-2 phút hoặc thêm API Key dự phòng.")
                    st.stop()
                time.sleep(1) # Đợi 1 giây trước khi thử key tiếp theo

        if not success:
            st.error("❌ Không thể kết nối với AI. Vui lòng kiểm tra lại API Key hoặc kết nối mạng.")
            st.stop()

        update_prog("✅ Hoàn tất!", 100)
        time.sleep(0.3)
        prog_placeholder.empty()

        # Lưu dữ liệu ngay lập tức
        save_to_log(prompt, full_text)
        save_to_csv(st.session_state.user_name, prompt, full_text)

        # Hiển thị kết quả
        content_parts = full_text.split("---TRÍCH DẪN NGUỒN---")
        main_ans = content_parts[0].strip()
        
        placeholder = st.empty()
        if len(main_ans) > 500:
            placeholder.markdown(highlight_keywords(main_ans))
        else:
            typed = ""
            for char in main_ans:
                typed += char
                placeholder.markdown(highlight_keywords(typed))
                time.sleep(0.005)
        
        if len(content_parts) > 1:
            with st.expander("📖 Cơ sở văn bản"):
                citations = parse_citations(full_text)
                if citations:
                    st.markdown("Bấm vào các nút dưới đây để đối chiếu từng nguồn:")
                    cols = st.columns(len(citations) if len(citations) <= 5 else 5)
                    for idx, (num, text) in enumerate(citations.items()):
                        col_idx = idx % 5
                        with cols[col_idx]:
                            if st.button(f"[{num}]", key=f"now_btn_{num}", use_container_width=True):
                                st.session_state.view_cited_text = text
                                st.rerun()
                else:
                    st.markdown(content_parts[1].strip())

        st.session_state.messages.append({"role": "assistant", "content": highlight_keywords(full_text)})
        st.rerun()