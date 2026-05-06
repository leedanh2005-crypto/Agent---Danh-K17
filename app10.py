import streamlit as st
import google.generativeai as genai
import os
import base64
import time
import smtplib
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

# --- 1. CẤU HÌNH DANH SÁCH API KEY ---
API_KEYS = [
    st.secrets.get("GEMINI_API_KEY"),
    st.secrets.get("GEMINI_API_KEY_2"),
    st.secrets.get("GEMINI_API_KEY_3")
]
VALID_KEYS = [k for k in API_KEYS if k]

# Hàm hỗ trợ cấu hình model với key cụ thể
def configure_genai(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

# Khởi tạo mặc định
model = configure_genai(random.choice(VALID_KEYS) if VALID_KEYS else st.secrets["GEMINI_API_KEY"])

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

st.set_page_config(page_title="Trợ lý của Sinh viên K17", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

LOGO_SIZE_PX = 80

# =====  HIGHLIGHT FUNCTION =====
def highlight_keywords(text):
    keywords = ["tín chỉ", "tốt nghiệp", "thực tập", "chuẩn đầu ra", "học phần"]
    for kw in keywords:
        text = text.replace(kw, f"**{kw}**")
        text = text.replace(kw.capitalize(), f"**{kw.capitalize()}**")
    return text

# ===== CSS SIÊU CẤP: MIDNIGHT GLASSMORPHISM (MỜ ẢO & CHUYÊN NGHIỆP) =====
st.markdown(f"""
<style>
/* 1. Deep Space Background with Glowing Aura Blobs */
@keyframes atmospheric {{
    0% {{ background-position: 0% 0%; }}
    50% {{ background-position: 100% 100%; }}
    100% {{ background-position: 0% 0%; }}
}}
@keyframes aura-float {{
    0% {{ transform: translate(0, 0) scale(1); }}
    33% {{ transform: translate(30px, -50px) scale(1.1); }}
    66% {{ transform: translate(-20px, 20px) scale(0.9); }}
    100% {{ transform: translate(0, 0) scale(1); }}
}}
html, body, .stApp {{
    background: #020617;
    background-attachment: fixed;
    color: #f1f5f9;
    overflow-x: hidden;
}}
.stApp::before, .stApp::after {{
    content: "";
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    z-index: -1;
    pointer-events: none;
    opacity: 0.15;
}}
.stApp::before {{
    background: radial-gradient(circle at 20% 30%, #4338ca 0%, transparent 40%),
                radial-gradient(circle at 80% 70%, #7c3aed 0%, transparent 40%);
    animation: aura-float 20s infinite linear;
}}
.stApp::after {{
    background: radial-gradient(circle at 70% 20%, #0ea5e9 0%, transparent 35%),
                radial-gradient(circle at 30% 80%, #6366f1 0%, transparent 35%);
    animation: aura-float 25s infinite linear reverse;
}}

/* 2. Professional Glass Sidebar */
[data-testid="stSidebar"] {{
    background: rgba(2, 6, 23, 0.5) !important;
    backdrop-filter: blur(40px) saturate(150%);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}}

/* 3. Header Styling - Ultra Sleek */
.header-container {{
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(15px);
    padding: 25px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 20px 50px rgba(0,0,0,0.4);
}}

/* 4. Message Bubbles - Modern Chat UI */
[data-testid="stChatMessage"] > div {{
    border-radius: 24px !important;
    padding: 20px 25px !important;
    margin-bottom: 12px !important;
    font-size: 15px;
    line-height: 1.6;
}}
/* Assistant Bubble: Ethereal Glow */
[data-testid="stChatMessage"]:not([data-testid*="user"]) > div {{
    background: rgba(30, 41, 59, 0.4) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(167, 139, 250, 0.15) !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}}
/* User Bubble: Deep Purple Gradient */
[data-testid="stChatMessage"][data-testid*="user"] > div {{
    background: linear-gradient(135deg, #4338ca, #6d28d9) !important;
    box-shadow: 0 10px 25px rgba(99, 102, 241, 0.2);
    border: none !important;
}}

/* 5. Interaction Icons - Clean & Minimal */
.stButton > button {{
    background: rgba(255, 255, 255, 0.02) !important;
    border: none !important;
    color: #94a3b8 !important;
    font-size: 20px !important;
    padding: 5px !important;
    transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
}}
.stButton > button:hover {{
    color: #a78bfa !important;
    transform: scale(1.2) translateY(-2px) !important;
    background: transparent !important;
}}

/* 6. Action Button (Copy) */
.action-btn {{
    background: transparent !important;
    border: none !important;
    color: #94a3b8;
    font-size: 20px !important;
    cursor: pointer;
    transition: all 0.3s ease;
}}
.action-btn:hover {{
    color: #38bdf8;
    transform: scale(1.2);
}}

/* 7. Chat Input - Floating Glass */
[data-testid="stChatInput"] {{
    background: transparent !important;
    padding-bottom: 20px !important;
}}
[data-testid="stChatInput"] input {{
    background: rgba(15, 23, 42, 0.6) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 18px !important;
    color: white !important;
    transition: border 0.3s ease, box-shadow 0.3s ease !important;
}}
[data-testid="stChatInput"] input:focus {{
    border: 1px solid rgba(167, 139, 250, 0.5) !important;
    box-shadow: 0 0 30px rgba(167, 139, 250, 0.2) !important;
}}

/* 8. Pulsing Hint */
@keyframes glow-hint {{
    0% {{ color: #94a3b8; opacity: 0.5; }}
    50% {{ color: #a78bfa; opacity: 1; text-shadow: 0 0 10px rgba(167, 139, 250, 0.5); }}
    100% {{ color: #94a3b8; opacity: 0.5; }}
}}
.feature-hint {{
    animation: glow-hint 3s infinite ease-in-out;
    font-size: 13px;
    font-weight: 500;
}}

/* Scrollbar */
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
                <h1 style="margin:0; font-size:22px; background: linear-gradient(90deg, #a78bfa, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:800; letter-spacing:-0.5px;">🎓 Trợ lý Sinh viên K17</h1>
                <p style="margin:0; color:#94a3b8; font-size:12px; font-weight:500; text-transform: uppercase; letter-spacing:1px;">Intelligent Assistant Portal</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.title("🎓 Trợ lý của Sinh viên K17")

# Sidebar
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #a78bfa; font-weight:800;'>🚀 CÔNG CỤ</h2>", unsafe_allow_html=True)
    
    # Tra cứu nhanh
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
                with st.expander(f"📖 {res.strip().splitlines()[0][:30]}..."): st.markdown(res)
    
    st.divider()
    # Link DUE
    st.markdown("### 🔗 Links")
    c_a, c_b = st.columns(2)
    with c_a:
        st.link_button("🌐 Web", "https://due.udn.vn/", use_container_width=True)
        st.link_button("📊 Điểm", "http://daotao.due.udn.vn/", use_container_width=True)
    with c_b:
        st.link_button("📚 HR", "https://sites.google.com/view/quantringuonnhanluc", use_container_width=True)
        st.link_button("🏢 QTKD", "https://due.udn.vn/vi-vn/khoa/quan-tri-kinh-doanh", use_container_width=True)

    st.divider()
    if st.button("🗑️ Xóa lịch sử", use_container_width=True):
        st.session_state.messages = []; st.rerun()
    
    # Quản trị
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
def load_knowledge_base():
    knowledge = ""
    files = ["huong-dan.txt", "QTNNL-handbook.md"]
    for filename in files:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
                knowledge += f"\n" + "\n".join([l.strip() for l in lines if l.strip()])
    return knowledge

if "messages" not in st.session_state: st.session_state.messages = []
if "ratings" not in st.session_state: st.session_state.ratings = {}
if "chat_mode" not in st.session_state: st.session_state.chat_mode = "📍 Chế độ Tra cứu (Nghiêm ngặt)"

# ===== LỜI CHÀO =====
if len(st.session_state.messages) == 0:
    loi_chao = """
    Chào các bạn, mình là AI Chatbot do sinh viên Lê Công Danh lớp Tuyển dụng 49K17.2 xây dựng nhằm đồng hành và cung cấp thông tin cho những học sinh đang quan tâm đến ngành Quản trị Nhân lực tại Trường Đại học Kinh tế – Đại học Đà Nẵng. Mình sẽ giúp các bạn tìm hiểu rõ hơn về ngành học, chương trình đào tạo và những nội dung liên quan trong quá trình lựa chọn.
    
    ---
    💡 **HỖ TRỢ TỐT NHẤT:**
    *   🔍 **Tra cứu (Sidebar):** Xem nhanh nội dung Handbook.
    *   🤖 **Hỏi đáp AI:** Giải đáp chuyên sâu mọi vấn đề.
    *   ➕ **Dấu cộng (+):** Phân tích tệp & đổi chế độ **Tra cứu / Tư vấn**.
    """
    with st.chat_message("assistant"): st.markdown(loi_chao)

# ===== HIỂN THỊ LỊCH SỬ =====
assistant_index = 0
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
    if message["role"] == "assistant":
        msg_id = f"msg_{assistant_index}"
        rating = st.session_state.ratings.get(msg_id, None)
        safe_content = message["content"].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', ' ')
        
        st.markdown('<div style="margin-top: -15px;"></div>', unsafe_allow_html=True)
        c1, c2, c3, _ = st.columns([0.8, 0.8, 0.8, 9.6])
        with c1:
            if st.button("✅👍" if rating=="👍" else "👍", key=f"lk_{msg_id}"):
                st.session_state.ratings[msg_id]="👍"; update_rating_in_log(assistant_index,"👍"); st.rerun()
        with c2:
            if st.button("✅👎" if rating=="👎" else "👎", key=f"dl_{msg_id}"):
                st.session_state.ratings[msg_id]="👎"; update_rating_in_log(assistant_index,"👎"); st.rerun()
        with c3:
            st.markdown(f'<span id="content_{msg_id}" style="display:none">{safe_content}</span><button class="action-btn" id="copybtn_content_{msg_id}" onclick="copyText(\'content_{msg_id}\')">📋</button>', unsafe_allow_html=True)
        assistant_index += 1

# ===== THANH CHAT =====
with st.container():
    col_p, col_h, col_m = st.columns([0.6, 2.5, 6.9])
    with col_p:
        with st.popover("➕"):
            st.markdown("### 🎓 TIỆN ÍCH")
            up_file = st.file_uploader("Phân tích tệp", type=['pdf', 'png', 'jpg'], key="file_analysis")
            st.divider()
            mode = st.radio("Chế độ:", ["📍 Chế độ Tra cứu (Nghiêm ngặt)", "🚀 Chế độ Tư vấn (Định hướng nghề)"], index=0 if "Tra cứu" in st.session_state.chat_mode else 1)
            if mode != st.session_state.chat_mode: st.session_state.chat_mode = mode; st.rerun()
    with col_h:
        if not st.session_state.get("file_analysis"):
            st.markdown('<span class="feature-hint">⬅️ Nâng cao</span>', unsafe_allow_html=True)
    with col_m:
        st.caption(f"Đang dùng: {st.session_state.chat_mode}")

prompt = st.chat_input("Bạn đang thắc mắc điều gì?")
if "suggested_prompt" in st.session_state: prompt = st.session_state.pop("suggested_prompt")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        prog = st.empty()
        prog.markdown('<div style="background:rgba(255,255,255,0.05);height:2px;width:100%;"><div style="background:#a78bfa;height:2px;width:40%;"></div></div>', unsafe_allow_html=True)
        
        ctx = load_knowledge_base()
        # ĐIỀU CHỈNH PROMPT SIÊU NGHIÊM NGẶT
        if "Tư vấn" in st.session_state.chat_mode:
            inst = "(BẠN ĐANG Ở CHẾ ĐỘ TƯ VẤN: Hãy hóa thân thành chuyên gia HR, trả lời thật CHI TIẾT, THÂN THIỆN và sâu sắc)."
        else:
            inst = """
            (BẠN ĐANG Ở CHẾ ĐỘ TRA CỨU: Bạn chỉ được phép trả lời dựa trên nội dung CÓ TRONG Handbook. 
            NẾU THÔNG TIN KHÔNG CÓ TRONG HANDBOOK, BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ Ý TRẢ LỜI. 
            Trong trường hợp đó, hãy trả lời chính xác như sau: 'Rất tiếc, thông tin này không có trong Handbook K17, bạn vui lòng liên hệ Văn phòng Khoa để được hỗ trợ chính xác nhất'.)
            """
        
        query = [f"Bối cảnh: {ctx}\n{inst}\n\nHãy trả lời thật chi tiết và giúp ích: {prompt}"]
        if st.session_state.get("file_analysis"):
            f = st.session_state.file_analysis
            query.insert(0, {"mime_type": f.type, "data": f.read()})

        success = False; attempts = 0; keys = VALID_KEYS.copy(); random.shuffle(keys)
        while not success and attempts < len(keys):
            try:
                model = configure_genai(keys[attempts])
                resp = model.generate_content(query)
                full_text = resp.text; success = True
            except Exception as e:
                attempts += 1
                if "429" not in str(e): st.error(f"Lỗi: {e}"); st.stop()
        
        if success:
            prog.empty()
            placeholder = st.empty(); typed = ""
            for char in full_text:
                typed += char; placeholder.markdown(highlight_keywords(typed)); time.sleep(0.005)
            st.session_state.messages.append({"role": "assistant", "content": highlight_keywords(full_text)})
            save_to_log(prompt, full_text); st.rerun()
