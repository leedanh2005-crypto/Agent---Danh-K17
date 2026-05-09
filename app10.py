import streamlit as st
import google.generativeai as genai
import os
import base64
import time
import smtplib
import json
import csv
import random
import re
import io
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from gtts import gTTS

# --- 1. CONFIG & SESSION ---
st.set_page_config(
    page_title="Trợ lý của Sinh viên K17",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "ratings" not in st.session_state:
    st.session_state.ratings = {}
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "📍 Chế độ Tra cứu (Nghiêm ngặt)"

# --- USER NAME GATE ---
if "user_name" not in st.session_state:
    st.markdown(
        """
        <div style='background:rgba(255,255,255,0.05); padding:30px; border-radius:20px; text-align:center; margin-top:50px;'>
            <h2 style='color:#a78bfa;'>👋 Chào mừng bạn đến với Trợ lý K17!</h2>
            <p style='color:#94a3b8;'>Để bắt đầu cuộc trò chuyện, vui lòng cho mình biết tên của bạn:</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_input_name = st.text_input("Tên của bạn:", key="gate_name_input", placeholder="Ví dụ: Nguyễn Văn A")
        if st.button("🚀 Bắt đầu ngay", use_container_width=True, key="start_gate_btn"):
            if user_input_name.strip():
                st.session_state.user_name = user_input_name.strip()
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập tên!")
    st.stop()

# --- 2. API KEYS ---
try:
    API_KEYS = st.secrets.get("GEMINI_API_KEYS", [])
except Exception:
    API_KEYS = []

if not API_KEYS:
    API_KEYS = [
        "AIzaSyAdBywy8u_cxA1ejgQhvCQvrBXc6vtAh1Y",
        "AIzaSyCnEYLHJH9X4F5VMlv7aj4aNSxa7jhs2IY",
        "AIzaSyAV4IFFRMsiQmeEAl4ptueyNIBwIUTsyco",
        "AIzaSyD_ih6QcgG9KWJV1nnVOnHt9z7V9Ud2geQ",
    ]

VALID_KEYS = [k for k in API_KEYS if k and "VUI_LONG" not in k]

if not VALID_KEYS:
    st.error("❌ Lỗi: API Key chưa được cấu hình!")
    st.stop()

def configure_genai(api_key):
    genai.configure(api_key=api_key)
    # User specifically asked for Gemini 2.5 Flash
    return genai.GenerativeModel('gemini-2.5-flash')

# --- 3. UI LOCALIZATION ---
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
    vi_chars = "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
    if any(c in vi_chars for c in text.lower()):
        return "vi"
    vi_words = {"hoc", "sinh", "vien", "nganh", "nghe", "tot", "nghiep", "dang", "ky", "tin", "chi", "truong", "co", "va", "nhung", "la", "cua", "trong", "cho", "duoc", "nguoi", "khong", "phai", "nao", "dau", "sao", "nay", "thi", "lam"}
    words = set(re.findall(r'\b\w+\b', text.lower()))
    if words.intersection(vi_words):
        return "vi"
    return "en"

# --- 4. HELPERS ---
def parse_citations(text):
    if "---TRÍCH DẪN NGUỒN---" not in text:
        return {}
    parts = text.split("---TRÍCH DẪN NGUỒN---")
    source_section = parts[1].strip()
    pattern = r"\[(\d+)\](.*?)(?=\s*\[\d+\]|$)"
    matches = re.findall(pattern, source_section, re.DOTALL)
    return {num: content.strip() for num, content in matches}

def load_knowledge_base(include_skills=False, include_standards=False, query=""):
    knowledge = ""
    # 1. Load Handbook (Luôn nạp vì là nền tảng)
    files = ["huong-dan.txt", "QTNNL-handbook.md"]
    for filename in files:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
                knowledge += f"\n--- NỘI DUNG HANDBOOK ({filename}) ---\n" + content
    
    # 2. Load Skills thông minh (Chỉ nạp domain liên quan để tiết kiệm Token)
    if include_skills:
        skills_dir = "claude-skills"
        # Bản đồ từ khóa để định hướng AI nạp đúng bộ Skill
        domain_map = {
            "c-level-advisor/chro-advisor": ["lương", "tuyển dụng", "định biên", "nhân sự", "hr", "compensation", "hiring"],
            "c-level-advisor/culture-architect": ["văn hóa", "môi trường", "gắn kết", "giá trị", "culture", "engagement"],
            "c-level-advisor/executive-mentor": ["kỹ năng", "lãnh đạo", "nghề nghiệp", "phát triển", "mentor", "leadership", "career"],
            "project-management": ["dự án", "nhóm", "kế hoạch", "tiến độ", "project", "planning"]
        }
        
        q_lower = query.lower()
        selected_domains = []
        
        # Kiểm tra xem câu hỏi thuộc domain nào
        for domain, keywords in domain_map.items():
            if any(kw in q_lower for kw in keywords):
                selected_domains.append(domain)
        
        # Nếu không khớp domain nào hoặc câu hỏi chung chung, nạp 3 bộ cốt lõi bản rút gọn
        if not selected_domains:
            selected_domains = ["c-level-advisor/chro-advisor", "c-level-advisor/culture-architect", "c-level-advisor/executive-mentor"]
            
        for domain in selected_domains:
            domain_path = os.path.join(skills_dir, domain)
            skill_file = os.path.join(domain_path, "SKILL.md")
            
            # Chỉ nạp file SKILL.md (tinh hoa) để tiết kiệm token tối đa
            if os.path.exists(skill_file):
                try:
                    with open(skill_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        knowledge += f"\n\n--- TRI THỨC CHUYÊN GIA: {domain.upper()} ---\n{content}"
                except Exception:
                    continue
    
    # 3. Load Standards nếu cần
    if include_standards and not include_skills:
        std_path = "claude-skills/standards/documentation/documentation-standards.md"
        if os.path.exists(std_path):
            with open(std_path, "r", encoding="utf-8") as f:
                content = f.read()
                knowledge += f"\n\n--- TIÊU CHUẨN TRÌNH BÀY VĂN BẢN ---\n{content}"
    return knowledge

# ===== CẤU HÌNH GMAIL =====
SENDER_EMAIL = "leedanh2005@gmail.com"
SENDER_PASSWORD = "bgoa ftww iqvr xqap"

def send_email(to_email, chat_history):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "📚 Lịch sử hội thoại - Trợ lý Sinh viên K17"
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        user_name = st.session_state.get('user_name', 'người dùng')
        body = f"Dưới đây là nội dung hội thoại của {user_name} với Trợ lý K17:\n\n"
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

# ===== LOGS =====
def save_to_log(q, a, d=None):
    log_f = "chat_log.json"
    logs = []
    if os.path.exists(log_f):
        with open(log_f, "r", encoding="utf-8") as f:
            logs = json.load(f)
    logs.append({
        "thoi_gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cau_hoi": q,
        "cau_tra_loi": a,
        "danh_gia": d
    })
    with open(log_f, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def save_to_csv(user_name, question, answer):
    try:
        csv_f = os.path.join(os.getcwd(), "chat_history.csv")
        exist = os.path.isfile(csv_f)
        with open(csv_f, mode='a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if not exist:
                writer.writerow(["Thời gian", "Tên người dùng", "Câu hỏi", "Câu trả lời"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_name, question, answer])
        return True
    except Exception:
        return False

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

def speak(text, lang='vi'):
    try:
        clean_text = re.sub(r'\[\d+\]', '', text)
        tts = gTTS(text=clean_text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception:
        return None

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        b64_data = base64.b64encode(img_file.read()).decode()
        return b64_data

def highlight_keywords(text):
    keywords = ["tín chỉ", "tốt nghiệp", "thực tập", "chuẩn đầu ra", "học phần"]
    for kw in keywords:
        text = text.replace(kw, f"**{kw}**")
        text = text.replace(kw.capitalize(), f"**{kw.capitalize()}**")
    return text

# --- CSS ---
st.markdown(
    """
    <style>
    html, body, .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #020617), radial-gradient(circle at bottom left, #0f172a, #020617);
        background-attachment: fixed;
        color: #f1f5f9;
    }
    [data-testid="stSidebar"] {
        background: rgba(2, 6, 23, 0.5) !important;
        backdrop-filter: blur(40px) saturate(150%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    .header-container {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        padding: 25px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stChatMessage"] > div {
        border-radius: 24px !important;
        padding: 20px 25px !important;
        margin-bottom: 12px !important;
    }
    .action-btn {
        background: transparent !important;
        border: none !important;
        color: white !important;
        font-size: 18px !important;
        cursor: pointer;
    }
    .status-text {
        font-size: 12px;
        color: #a78bfa;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .progress-container {
        background: rgba(255, 255, 255, 0.05);
        height: 6px;
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 8px;
    }
    .progress-bar {
        background: linear-gradient(90deg, #a78bfa, #38bdf8, #a78bfa);
        background-size: 200% 100%;
        height: 100%;
        transition: width 0.5s;
        animation: shimmer 2s infinite linear;
        box-shadow: 0 0 15px rgba(167, 139, 250, 0.4);
    }
    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    .thinking-wave {
        display: flex;
        gap: 3px;
        margin-bottom: 20px;
    }
    .thinking-wave div {
        width: 4px;
        height: 12px;
        background: #a78bfa;
        border-radius: 2px;
        animation: wave-pulse 1s infinite ease-in-out;
    }
    .thinking-wave div:nth-child(2) { animation-delay: 0.1s; }
    .thinking-wave div:nth-child(3) { animation-delay: 0.2s; }
    .thinking-wave div:nth-child(4) { animation-delay: 0.3s; }
    @keyframes wave-pulse {
        0%, 100% { height: 8px; opacity: 0.5; }
        50% { height: 18px; opacity: 1; background: #38bdf8; }
    }
    @keyframes glow {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- HEADER ---
if os.path.exists("background_due.jpg"):
    img_b64 = get_base64_image("background_due.jpg")
    st.markdown(
        f"""
        <div class="header-container" style="display:flex; align-items:center;">
            <div style="margin-right:20px;">
                <img src="data:image/jpg;base64,{img_b64}" style="border-radius:14px; width:60px; height:60px; object-fit:cover;"/>
            </div>
            <div>
                <h1 style="margin:0; font-size:22px; font-weight:800;">
                    🎓 <span style="background:linear-gradient(90deg,#a78bfa,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Trợ lý Sinh viên K17</span>
                </h1>
                <p style="margin:0; color:#94a3b8; font-size:12px;">Intelligent Assistant Portal</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.title("🎓 Trợ lý Sinh viên K17")

# --- SIDEBAR ---
with st.sidebar:
    if st.session_state.get("view_cited_text"):
        cited = st.session_state.view_cited_text
        lang = st.session_state.get("last_lang", "vi")
        if st.button(UI_LANG[lang]["back"], use_container_width=True, key="back_to_tools_btn"):
            st.session_state.view_cited_text = None
            st.rerun()
        st.markdown(f"### {UI_LANG[lang]['verify']}")
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border-left:4px solid #a78bfa; color:#cbd5e1;">{cited}</div>',
            unsafe_allow_html=True
        )
        st.info(UI_LANG[lang]["verified_hint"])
    else:
        st.markdown("<h2 style='text-align: center; color: #a78bfa; font-weight:800;'>🚀 CÔNG CỤ</h2>", unsafe_allow_html=True)
        st.markdown("### 🔍 Tìm kiếm")
        sq = st.text_input("Từ khóa:", key="sb_search_input", placeholder="Gõ để tìm...")
        if sq and os.path.exists("QTNNL-handbook.md"):
            with open("QTNNL-handbook.md", "r", encoding="utf-8") as f:
                content = f.read()
            results = [s for s in content.split("##") if sq.lower() in s.lower()]
            for r in results[:3]:
                title = r.strip().splitlines()[0][:30]
                with st.expander(f"📖 {title}..."):
                    st.markdown(r)
        st.divider()
        st.markdown("### 🔗 Links")
        c1, c2 = st.columns(2)
        with c1:
            st.link_button("🌐 Web", "https://due.udn.vn/", use_container_width=True)
            st.link_button("📊 Điểm", "http://daotao.due.udn.vn/", use_container_width=True)
        with c2:
            st.link_button("📚 HR", "https://sites.google.com/view/quantringuonnhanluc", use_container_width=True)
            st.link_button("🏢 QTKD", "https://due.udn.vn/vi-vn/khoa/quan-tri-kinh-doanh", use_container_width=True)
        st.divider()
        if st.button("🗑️ Xóa lịch sử", use_container_width=True, key="clear_history_btn"):
            st.session_state.messages = []
            st.rerun()
        with st.expander("🛠️ Admin & Email"):
            email_input = st.text_input("Gửi lịch sử qua Email:", key="email_send_input")
            if st.button("Gửi Mail", use_container_width=True, key="send_mail_action_btn"):
                if email_input:
                    res = send_email(email_input, st.session_state.messages)
                    if res == True:
                        st.success("Đã gửi!")
                    else:
                        st.error(f"Lỗi: {res}")
            st.divider()
            admin_pw = st.text_input("Pass Admin:", type="password", key="admin_pass_input")
            if st.button("Logs", use_container_width=True, key="view_logs_btn") and admin_pw == "0913":
                if os.path.exists("chat_log.json"):
                    with open("chat_log.json", "r", encoding="utf-8") as f:
                        log_data = json.load(f)
                        st.write(f"Tổng: {len(log_data)}")

# --- JS COPY ---
st.markdown(
    """
    <script>
    function copyText(id){
        const el = document.getElementById(id);
        if(!el) return;
        const t = el.innerText || el.textContent;
        navigator.clipboard.writeText(t).then(function(){
            const btn = document.getElementById('copybtn_' + id);
            if(btn){
                btn.innerHTML = '✅';
                setTimeout(function(){
                    btn.innerHTML = '📋';
                }, 2000);
            }
        });
    }
    </script>
    """,
    unsafe_allow_html=True
)

# --- GREETING ---
if not st.session_state.messages:
    loi_chao = """Chào các bạn, mình là AI Chatbot do sinh viên Lê Công Danh lớp Tuyển dụng 49K17.2 xây dựng nhằm đồng hành và cung cấp thông tin cho những học sinh đang quan tâm đến ngành Quản trị Nhân lực tại Trường Đại học Kinh tế – Đại học Đà Nẵng. Mình sẽ giúp các bạn tìm hiểu rõ hơn về ngành học, chương trình đào tạo và những nội dung liên quan trong quá trình lựa chọn.\n\n---\n💡 **HỖ TRỢ TỐT NHẤT CHO BẠN:**\n*   📍 **Chế độ Tra cứu:** Giải đáp chính xác 100% quy định từ Sổ tay sinh viên.\n*   🚀 **Chế độ Tư vấn:** Kích hoạt "Hội đồng chuyên gia HR" tư vấn chiến lược, nghề nghiệp và kỹ năng thực tế.\n*   📖 **Đối chiếu Nguồn:** Bấm vào các số `[1]`, `[2]` để xem ngay văn bản gốc tại Sidebar.\n*   🔊 **Giọng nói AI:** Bấm biểu tượng loa để nghe AI tư vấn với tốc độ cực nhanh.\n*   ➕ **Tính năng Nâng cao (vẫn đang trong quá trình phát triển):** Nhấn dấu cộng để tải lên Bảng điểm, CV (PDF/Ảnh) và yêu cầu AI phân tích sâu."""
    with st.chat_message("assistant"):
        st.markdown(loi_chao)

# --- HISTORY ---
assistant_idx = 0
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        parts = m["content"].split("---TRÍCH DẪN NGUỒN---")
        main_c = parts[0].strip()
        st.markdown(highlight_keywords(main_c))
        
        if m["role"] == "assistant" and len(parts) > 1:
            with st.expander("📖 Cơ sở văn bản"):
                cits = parse_citations(m["content"])
                if cits:
                    st.markdown("Bấm vào các nút dưới đây để đối chiếu từng nguồn:")
                    cols = st.columns(len(cits) if len(cits) < 6 else 5)
                    for idx, (num, txt) in enumerate(cits.items()):
                        if cols[idx % 5].button(f"[{num}]", key=f"cit_btn_{i}_{num}"):
                            st.session_state.view_cited_text = txt
                            st.rerun()
                else:
                    st.markdown(parts[1].strip())
        
        if m["role"] == "assistant":
            msg_id = f"msg_{assistant_idx}"
            rating = st.session_state.ratings.get(msg_id)
            safe_c = main_c.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', ' ')
            st.markdown('<div style="margin-top: -15px;"></div>', unsafe_allow_html=True)
            c1, c2, c3, c4, _ = st.columns([0.8, 0.8, 0.8, 0.8, 8.8])
            with c1: 
                btn_label = "👍" if rating != "👍" else "✅👍"
                if st.button(btn_label, key=f"like_{msg_id}"):
                    st.session_state.ratings[msg_id] = "👍"
                    update_rating_in_log(assistant_idx, "👍")
                    st.rerun()
            with c2:
                btn_label_down = "👎" if rating != "👎" else "✅👎"
                if st.button(btn_label_down, key=f"dislike_{msg_id}"):
                    st.session_state.ratings[msg_id] = "👎"
                    update_rating_in_log(assistant_idx, "👎")
                    st.rerun()
            with c3:
                st.markdown(
                    f'<span id="content_{msg_id}" style="display:none">{safe_c}</span><button class="action-btn" id="copybtn_content_{msg_id}" onclick="copyText(\'content_{msg_id}\')">📋</button>',
                    unsafe_allow_html=True
                )
            with c4:
                if st.button("🔊", key=f"tts_btn_{msg_id}"):
                    lc = detect_language(m["content"])
                    aud = speak(main_c, lang=lc)
                    if aud:
                        st.session_state[f"playing_{msg_id}"] = aud
            
            if f"playing_{msg_id}" in st.session_state:
                st.audio(st.session_state[f"playing_{msg_id}"], autoplay=True)
            assistant_idx += 1

# --- INPUT ---
with st.container():
    cp, ch, ci = st.columns([0.6, 3, 6])
    with cp:
        with st.popover("➕"):
            up = st.file_uploader("Tệp", type=['pdf','png','jpg'], key="file_uploader_main")
            current_mode_idx = 0 if "Tra cứu" in st.session_state.chat_mode else 1
            mode = st.radio("Chế độ:", ["📍 Chế độ Tra cứu", "🚀 Chế độ Tư vấn"], index=current_mode_idx, key="mode_radio_input")
            if mode != st.session_state.chat_mode:
                st.session_state.chat_mode = mode
                st.rerun()
    with ch: 
        if not st.session_state.get("file_uploader_main"):
            st.markdown('<span style="color:#fb7185;font-weight:bold;font-size:13px;animation: glow 2s infinite;">⬅️ Nâng cao</span>', unsafe_allow_html=True)
    with ci:
        st.caption(f"Đang dùng: {st.session_state.chat_mode}")

prompt = st.chat_input("Hỏi Trợ lý K17...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    u_msg = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant"):
        prog_ph = st.empty()
        
        def up_p(t, w):
            prog_ph.markdown(
                f"""
                <div class="status-text">{t}</div>
                <div class="progress-container"><div class="progress-bar" style="width:{w}%"></div></div>
                <div class="thinking-wave"><div></div><div></div><div></div><div></div></div>
                """,
                unsafe_allow_html=True
            )
        
        is_con = "Tư vấn" in st.session_state.chat_mode
        lang = detect_language(u_msg)
        st.session_state.last_lang = lang
        ui = UI_LANG[lang]
        
        up_p(ui["scanning"], 20)
        ctx = load_knowledge_base(include_skills=is_con, include_standards=not is_con, query=u_msg)
        up_p(ui["analyzing"], 50)
        l_inst = ""
        if lang == "en":
            l_inst = "LANGUAGE REQUIREMENT: Respond 100% in English. Translate all knowledge from Handbook/Skills into professional English."

        if is_con:
            inst = f"""
        (BẠN ĐANG Ở CHẾ ĐỘ TƯ VẤN: Bạn là Hội đồng Chuyên gia HR cao cấp. 
        Bối cảnh tri thức đã được mở rộng bằng các bộ kỹ năng từ thư mục 'claude-skills'.
        {l_inst}

        NHIỆM VỤ:
        1. Vận dụng 100% các khung tư duy (frameworks) và logic chuyên môn từ 3 bộ kỹ năng:
        - CHRO ADVISOR: Chiến lược nhân sự, kế hoạch định biên, khung lương.
        - CULTURE ARCHITECT: Xây dựng văn hóa, môi trường làm việc, gắn kết.
        - EXECUTIVE MENTOR: Phát triển lộ trình nghề nghiệp, kỹ năng lãnh đạo.
        2. KHÔNG BỊ GIỚI HẠN bởi Handbook trường, hãy tư vấn như chuyên gia thực thụ ngoài thực tế.
        3. LUÔN trích dẫn nguồn [n] ngay sau thông tin quan trọng. 
        4. Cuối bài, tạo mục '---TRÍCH DẪN NGUỒN---' và liệt kê: [n] NGUYÊN VĂN CÂU VĂN TRONG NGUỒN (Tên file).)
        """
        else:
            inst = f"""
        (BẠN ĐANG Ở CHẾ ĐỘ TRA CỨU: Bạn chỉ được phép trả lời dựa trên nội dung CÓ TRONG Handbook.
        NẾU THÔNG TIN KHÔNG CÓ TRONG HANDBOOK, BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ Ý TRẢ LỜI.
        {l_inst}

        YÊU CẦU:
        1. Trình bày chuyên nghiệp theo tiêu chuẩn Markdown (Heading, List, Bold).
        2. LUÔN trích dẫn nguồn [n] ngay sau thông tin lấy từ Handbook.
        3. Cuối bài, tạo mục '---TRÍCH DẪN NGUỒN---' và liệt kê: [n] NGUYÊN VĂN CÂU VĂN TRONG NGUỒN (Tên file).)
        """
        
        query = [f"Bối cảnh: {ctx}\n{inst}\n\nCâu hỏi: {u_msg}"]
        if st.session_state.get("file_uploader_main"):
            f = st.session_state.file_uploader_main
            query.insert(0, {"mime_type": f.type, "data": f.read()})
        
        success = False
        attempts = 0
        keys = VALID_KEYS.copy()
        random.shuffle(keys)
        
        full_text = ""
        while not success and attempts < len(keys):
            try:
                up_p(f"{ui['writing']} (Key {attempts+1})", 85)
                # Configure with the specific key
                genai.configure(api_key=keys[attempts])
                current_model = genai.GenerativeModel('gemini-flash-latest')
                resp = current_model.generate_content(query)
                full_text = resp.text
                success = True
            except Exception as e:
                attempts += 1
                last_e = str(e)
                if attempts >= len(keys):
                    st.error(f"❌ Lỗi: {last_e}")
                    st.stop()
                time.sleep(1)
        
        up_p(ui["finalizing"], 100)
        time.sleep(0.3)
        prog_ph.empty()
        
        save_to_log(u_msg, full_text)
        save_to_csv(st.session_state.user_name, u_msg, full_text)
        
        parts = full_text.split("---TRÍCH DẪN NGUỒN---")
        main_ans = parts[0].strip()
        ph = st.empty()
        
        if len(main_ans) > 500:
            ph.markdown(highlight_keywords(main_ans))
        else:
            typed = ""
            for char in main_ans:
                typed += char
                ph.markdown(highlight_keywords(typed))
                time.sleep(0.005)
        
        if len(parts) > 1:
            with st.expander("📖 Cơ sở văn bản"):
                cits = parse_citations(full_text)
                if cits:
                    cols = st.columns(len(cits) if len(cits) < 6 else 5)
                    for idx, (num, txt) in enumerate(cits.items()):
                        if cols[idx % 5].button(f"[{num}]", key=f"now_cit_{num}"):
                            st.session_state.view_cited_text = txt
                            st.rerun()
                else:
                    st.markdown(parts[1].strip())
        
        st.session_state.messages.append({"role": "assistant", "content": highlight_keywords(full_text)})
        st.rerun()
