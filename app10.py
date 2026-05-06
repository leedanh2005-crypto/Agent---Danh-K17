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

# ===== CSS NÂNG CẤP: FOCUS VÀO ĐỘ RÕ NÉT =====
st.markdown(f"""
<style>
/* 1. Animated Background */
@keyframes gradientBG {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}
html, body, .stApp {{
    background: linear-gradient(-45deg, #0f0c29, #1a1a2e, #24243e, #0f0c29);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
}}

/* 2. Glassmorphism Sidebar */
[data-testid="stSidebar"] {{
    background: rgba(15, 12, 41, 0.7) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255,255,255,0.05);
}}

/* 3. Header Container */
.header-container {{
    display: flex;
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(12px);
    padding: 20px 30px;
    border-radius: 20px;
    margin-bottom: 25px;
    align-items: center;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}}

/* 4. Glowing Chat Input */
[data-testid="stChatInput"] input {{
    background: rgba(15, 23, 42, 0.8) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(167, 139, 250, 0.3) !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
}}

/* 5. Message Bubbles - Làm đậm bối cảnh để icon nổi bật */
[data-testid="stChatMessage"] > div {{
    border-radius: 18px !important;
    padding: 15px 20px !important;
}}
[data-testid="stChatMessage"]:not([data-testid*="user"]) > div {{
    background: rgba(30, 41, 59, 0.7) !important;
    border: 1px solid rgba(167, 139, 250, 0.1) !important;
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}}
[data-testid="stChatMessage"][data-testid*="user"] > div {{
    background: #3b82f6 !important;
}}

/* 6. Rating Buttons - TRONG SUỐT HOÀN TOÀN ĐỂ HIỆN ICON */
.stButton > button {{
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: #cbd5f1 !important;
    padding: 2px 8px !important;
    font-size: 12px !important;
    transition: all 0.2s ease !important;
}}
.stButton > button:hover {{
    border-color: #a78bfa !important;
    background: rgba(167, 139, 250, 0.1) !important;
    transform: translateY(-1px);
}}

/* 7. Action Button (Copy) */
.action-btn {{
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 4px 10px;
    color: #cbd5f1;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
}}
.action-btn:hover {{
    border-color: #a78bfa;
    background: rgba(167, 139, 250, 0.1) !important;
}}

/* Animation cho nhãn gợi ý */
@keyframes pulse-hint {{
    0% {{ opacity: 0.7; transform: scale(1); }}
    50% {{ opacity: 1; transform: scale(1.05); color: #fb7185; }}
    100% {{ opacity: 0.7; transform: scale(1); }}
}}
.feature-hint {{
    animation: pulse-hint 2s infinite;
    font-size: 13px;
    font-weight: 600;
    color: #f87171;
}}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
if os.path.exists("background_due.jpg"):
    img_base64 = get_base64_image("background_due.jpg")
    st.markdown(f"""
        <div class="header-container">
            <div class="logo-box">
                <img src="data:image/jpg;base64,{img_base64}" style="border-radius: 12px; width:70px; height:70px; object-fit: cover;" />
            </div>
            <div class="title-box">
                <h1 style="margin:0; font-size:26px; background: linear-gradient(90deg, #a78bfa, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:800;">🎓 Trợ lý của Sinh viên K17</h1>
                <p style="margin:2px 0 0 0; color:#cbd5f1; font-style:italic; font-size:14px; opacity:0.8;">Giải đáp thắc mắc chuyên sâu về ngành Quản trị Nhân lực...</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.title("🎓 Trợ lý của Sinh viên K17")

# Sidebar
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #a78bfa; margin-bottom:20px;'>🚀 CÔNG CỤ</h2>", unsafe_allow_html=True)
    
    # ===== TÍNH NĂNG TRA CỨU NHANH (0 TOKEN) =====
    st.markdown("### 🔍 Tra cứu nhanh")
    search_query = st.text_input("Nhập từ khóa:", placeholder="Ví dụ: tốt nghiệp, học bổng...", key="sidebar_search")
    
    if search_query:
        handbook_path = "QTNNL-handbook.md"
        if os.path.exists(handbook_path):
            with open(handbook_path, "r", encoding="utf-8") as f:
                content = f.read()
            sections = content.split("##")
            results = [s for s in sections if search_query.lower() in s.lower()]
            if results:
                for res in results[:5]:
                    title = res.strip().split('\n')[0] if res.strip() else "Thông tin"
                    with st.expander(f"📖 {title}"): st.markdown(res)
            else: st.info("Không tìm thấy.")
    
    st.divider()
    # ===== CỔNG THÔNG TIN DUE (LINK PORTAL) =====
    st.markdown("### 🔗 Link hữu ích")
    col_a, col_b = st.columns(2)
    with col_a:
        st.link_button("🌐 Website", "https://due.udn.vn/", use_container_width=True)
        st.link_button("📊 Tra điểm", "http://daotao.due.udn.vn/", use_container_width=True)
    with col_b:
        st.link_button("📚 Ngành HR", "https://sites.google.com/view/quantringuonnhanluc?fbclid=IwY2xjawRmjAFleHRuA2FlbQIxMABicmlkETF6eDAwVWdRdmV4d2djQW85c3J0YwZhcHBfaWQQMjIyMDM5MTc4ODIwMDg5MgABHlx7-TEfS6M4xxo2q8cmRr7z0IdnzW0kK4txNgK09ICcGFNOKw3GFeU9wEg8_aem_2ThZL17x7SbrEcfn7UaKbA", use_container_width=True)
        st.link_button("🏢 Khoa QTKD", "https://due.udn.vn/vi-vn/khoa/quan-tri-kinh-doanh", use_container_width=True)

    st.divider()
    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []; st.rerun()
    
    st.markdown("### 📧 Mail lịch sử")
    user_email = st.text_input("Email nhận:", placeholder="example@gmail.com")
    if st.button("📨 Gửi ngay", use_container_width=True):
        if user_email and len(st.session_state.get("messages", [])) > 0:
            with st.spinner("Đang gửi..."):
                if send_email(user_email, st.session_state.messages) is True: st.success("✅ Đã gửi!")

# ===== JS COPY =====
st.markdown("""
<script>
function copyText(id) {
    const el = document.getElementById(id);
    if (!el) return;
    navigator.clipboard.writeText(el.innerText || el.textContent).then(function() {
        const btn = document.getElementById('copybtn_' + id);
        if (btn) {
            btn.innerText = '✅ Đã copy!';
            setTimeout(function() { btn.innerText = '📋 Copy'; }, 2000);
        }
    });
}
</script>
""", unsafe_allow_html=True)

# ===== SUGGESTION =====
if len(st.session_state.get("messages", [])) == 0:
    st.markdown("<p style='color:#a78bfa; font-weight:bold; margin-bottom:10px;'>💡 GỢI Ý CÂU HỎI:</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    if col1.button("🎓 Tín chỉ tốt nghiệp?"): st.session_state["suggested_prompt"] = "Học bao nhiêu tín chỉ để tốt nghiệp?"
    if col2.button("⏱️ Tốt nghiệp sớm?"): st.session_state["suggested_prompt"] = "Có thể tốt nghiệp sớm được không?"
    if col3.button("📜 Chuẩn đầu ra?"): st.session_state["suggested_prompt"] = "Các chuẩn đầu ra của chuyên nghành là?"

# --- DATA ---
def load_knowledge_base():
    knowledge = ""
    files = ["huong-dan.txt", "QTNNL-handbook.md"]
    for filename in files:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
                clean_lines = [l.strip() for l in lines if l.strip()]
                knowledge += f"\n" + "\n".join(clean_lines)
    return knowledge

# --- CHAT ---
if "messages" not in st.session_state: st.session_state.messages = []
if "ratings" not in st.session_state: st.session_state.ratings = {}
if "chat_mode" not in st.session_state: st.session_state.chat_mode = "📍 Chế độ Tra cứu (Nghiêm ngặt)"

# ===== LỜI CHÀO ĐẦU =====
if len(st.session_state.messages) == 0:
    loi_chao = """
    Chào các bạn, mình là AI Chatbot do sinh viên Lê Công Danh lớp Tuyển dụng 49K17.2 xây dựng nhằm đồng hành và cung cấp thông tin cho những học sinh đang quan tâm đến ngành Quản trị Nhân lực tại Trường Đại học Kinh tế – Đại học Đà Nẵng. Mình sẽ giúp các bạn tìm hiểu rõ hơn về ngành học, chương trình đào tạo và những nội dung liên quan trong quá trình lựa chọn.
    
    ---
    💡 **HỖ TRỢ TỐT NHẤT CHO BẠN:**
    *   🔍 **Tra cứu (Sidebar):** Xem Handbook nhanh & không giới hạn.
    *   🤖 **Hỏi đáp AI:** Giải đáp chuyên sâu mọi thắc mắc.
    *   ➕ **Dấu cộng (+):** Phân tích tệp tin và chuyển đổi linh hoạt giữa **Tra cứu** & **Tư vấn**.
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
        
        # Row của các nút tương tác
        st.markdown('<div style="margin-top: -10px;"></div>', unsafe_allow_html=True)
        c1, c2, c3, _ = st.columns([1.2, 1.2, 1.2, 8.4])
        with c1:
            if st.button("👍" if rating=="👍" else "👍 Hữu ích", key=f"lk_{msg_id}"):
                st.session_state.ratings[msg_id]="👍"; update_rating_in_log(assistant_index,"👍"); st.rerun()
        with c2:
            if st.button("👎" if rating=="👎" else "👎 Chưa tốt", key=f"dl_{msg_id}"):
                st.session_state.ratings[msg_id]="👎"; update_rating_in_log(assistant_index,"👎"); st.rerun()
        with c3:
            st.markdown(f'<span id="content_{msg_id}" style="display:none">{safe_content}</span><button class="action-btn" id="copybtn_content_{msg_id}" onclick="copyText(\'content_{msg_id}\')">📋 Copy</button>', unsafe_allow_html=True)
        assistant_index += 1

# ===== GIAO DIỆN THANH CHAT =====
with st.container():
    col_p, col_h, col_m = st.columns([0.6, 2.8, 6.6])
    with col_p:
        with st.popover("➕"):
            st.markdown("### 🎓 TIỆN ÍCH")
            up_file = st.file_uploader("Phân tích tài liệu", type=['pdf', 'png', 'jpg'], key="file_analysis")
            st.divider()
            mode = st.radio("Chế độ AI:", ["📍 Chế độ Tra cứu (Nghiêm ngặt)", "🚀 Chế độ Tư vấn (Định hướng nghề)"], index=0 if st.session_state.chat_mode == "📍 Chế độ Tra cứu (Nghiêm ngặt)" else 1)
            if mode != st.session_state.chat_mode: st.session_state.chat_mode = mode; st.rerun()
    with col_h:
        if not st.session_state.get("file_analysis"):
            st.markdown('<span class="feature-hint">⬅️ Tính năng mới</span>', unsafe_allow_html=True)
    with col_m:
        st.caption(f"Đang dùng: {st.session_state.chat_mode}")

prompt = st.chat_input("Bạn đang thắc mắc điều gì?")
if "suggested_prompt" in st.session_state: prompt = st.session_state.pop("suggested_prompt")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        prog = st.empty()
        prog.markdown('<div style="background:rgba(255,255,255,0.05);height:2px;width:100%;"><div style="background:#a78bfa;height:2px;width:30%;"></div></div>', unsafe_allow_html=True)
        
        ctx = load_knowledge_base()
        inst = "\n(BẠN ĐANG Ở CHẾ ĐỘ TƯ VẤN: Hãy dùng kiến thức chuyên môn HR để tư vấn chuyên sâu)." if "Tư vấn" in st.session_state.chat_mode else "\n(BẠN ĐANG Ở CHẾ ĐỘ TRA CỨU: Chỉ trả lời dựa trên Handbook)."
        query = [f"Bối cảnh: {ctx}\n{inst}\n\nCâu hỏi: {prompt}"]
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
