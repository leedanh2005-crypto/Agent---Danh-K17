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

# ===== CSS =====
st.markdown(f"""
<style>
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stBottom"] {{
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
}}
.block-container {{
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: min(95vw, 1400px) !important;
    margin-left: auto;
    margin-right: auto;
}}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #1a1a2e, #16213e);
}}
[data-testid="stSidebar"] * {{
    color: #cbd5f1 !important;
}}
.header-container {{
    display: flex;
    background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(56,189,248,0.15));
    backdrop-filter: blur(12px);
    padding: 20px 30px;
    border-radius: 18px;
    margin-bottom: 25px;
    align-items: center;
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
}}
.logo-box {{ margin-right: 25px; }}
.logo-box img {{
    border-radius: 12px;
    height: {LOGO_SIZE_PX}px;
    width: {LOGO_SIZE_PX}px;
    object-fit: cover;
}}
.title-box h1 {{
    margin: 0;
    font-size: 26px;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.title-box p {{
    color: #cbd5f1;
    margin-top: 6px;
}}
[data-testid="stChatMessage"] {{
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}}
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"],
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {{
    display: none !important;
}}
[data-testid="stChatMessage"] > div {{
    max-width: 75% !important;
    width: fit-content;
    padding: 14px 18px;
    border-radius: 16px;
    margin-bottom: 4px;
    animation: fadeIn 0.25s ease-in-out;
}}
[data-testid="stChatMessage"][data-testid*="user"] > div {{
    margin-left: auto;
    background: #2563eb;
    color: white;
    border-radius: 16px 16px 6px 16px;
}}
[data-testid="stChatMessage"]:not([data-testid*="user"]) > div {{
    margin-right: auto;
    border: 1px solid transparent;
    border-radius: 16px 16px 16px 6px;
    background:
        linear-gradient(#1e293b, #1e293b) padding-box,
        linear-gradient(135deg, #a78bfa, #38bdf8) border-box;
}}
.stButton > button {{
    position: relative;
    overflow: hidden;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 10px;
    padding: 6px 10px;
    color: #e2e8f0;
    font-size: 13px;
    transition: all 0.25s ease;
}}
.stButton > button:hover {{
    transform: translateY(-2px) scale(1.02);
    border: 1px solid #a78bfa;
    box-shadow: 0 4px 12px rgba(167,139,250,0.25);
    background: rgba(255,255,255,0.08);
}}
[data-testid="stChatInput"] input {{
    background: rgba(255,255,255,0.08);
    border-radius: 12px;
    border: 1px solid rgba(167,139,250,0.4);
    color: white;
    padding: 10px;
    transition: all 0.25s ease;
}}
[data-testid="stChatInput"] input:focus {{
    border: 1px solid #a78bfa;
    outline: none;
    box-shadow: 0 0 0 2px rgba(167,139,250,0.25), 0 0 12px rgba(167,139,250,0.35);
}}
hr {{ border-color: rgba(255,255,255,0.1) !important; }}
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes rippleJS {{
    0%   {{ transform: scale(0); opacity: 0.6; }}
    100% {{ transform: scale(1); opacity: 0; }}
}}
@keyframes pulse-hint {{
    0% {{ opacity: 0.6; transform: translateX(0); }}
    50% {{ opacity: 1; transform: translateX(-5px); }}
    100% {{ opacity: 0.6; transform: translateX(0); }}
}}
.feature-hint {{
    color: #f87171;
    font-size: 13px;
    font-weight: bold;
    animation: pulse-hint 1.5s infinite;
    padding-top: 10px;
}}
.action-btn {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(167,139,250,0.25);
    border-radius: 8px;
    padding: 6px 12px;
    color: #cbd5f1;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-top: 4px;
}}
.action-btn:hover {{
    background: rgba(167,139,250,0.15);
    border-color: #a78bfa;
}}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
if os.path.exists("background_due.jpg"):
    img_base64 = get_base64_image("background_due.jpg")
    st.markdown(f"""
        <div class="header-container">
            <div class="logo-box">
                <img src="data:image/jpg;base64,{img_base64}" />
            </div>
            <div class="title-box">
                <h1><span style="-webkit-text-fill-color: initial;">🎓</span> Trợ lý của Sinh viên K17</h1>
                <p><i>Giải đáp các thắc mắc về nội quy, học phần, các chuẩn đầu ra,....</i></p>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.title("🎓 Trợ lý của Sinh viên K17")
    st.markdown("*Giải đáp các thắc mắc về nội quy, học phần, các chuẩn đầu ra,....*")

# Sidebar
with st.sidebar:
    st.title("🚀 Công cụ hỗ trợ")
    
    # ===== TÍNH NĂNG TRA CỨU NHANH (0 TOKEN) =====
    st.markdown("### 🔍 Tra cứu nhanh Handbook")
    search_query = st.text_input("Nhập từ khóa tìm kiếm:", placeholder="Ví dụ: tốt nghiệp, học bổng...", key="sidebar_search")
    
    if search_query:
        handbook_path = "QTNNL-handbook.md"
        if os.path.exists(handbook_path):
            with open(handbook_path, "r", encoding="utf-8") as f:
                content = f.read()
            sections = content.split("##")
            results = [s for s in sections if search_query.lower() in s.lower()]
            
            if results:
                st.success(f"Tìm thấy {len(results)} mục:")
                for res in results:
                    title = res.strip().split('\n')[0] if res.strip() else "Thông tin chi tiết"
                    with st.expander(f"📖 {title}"):
                        st.markdown(res)
            else:
                st.info("Không tìm thấy thông tin phù hợp.")
    
    st.divider()
    # ===== CỔNG THÔNG TIN DUE (LINK PORTAL) =====
    st.markdown("### 🔗 Cổng thông tin DUE")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.link_button("🌐 Website DUE", "https://due.udn.vn/", use_container_width=True)
        st.link_button("📊 Tra cứu điểm", "http://daotao.due.udn.vn/", use_container_width=True)
    with col_b:
        st.link_button("📚 Ngành QTNNL", "https://sites.google.com/view/quantringuonnhanluc?fbclid=IwY2xjawRmjAFleHRuA2FlbQIxMABicmlkETF6eDAwVWdRdmV4d2djQW85c3J0YwZhcHBfaWQQMjIyMDM5MTc4ODIwMDg5MgABHlx7-TEfS6M4xxo2q8cmRr7z0IdnzW0kK4txNgK09ICcGFNOKw3GFeU9wEg8_aem_2ThZL17x7SbrEcfn7UaKbA", use_container_width=True)
        st.link_button("🏢 Khoa QTKD", "https://due.udn.vn/vi-vn/khoa/quan-tri-kinh-doanh", use_container_width=True)

    st.divider()

    if st.button("Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    
    st.markdown("### 📧 Gửi hội thoại về mail")
    user_email = st.text_input("Nhập email của bạn:", placeholder="example@gmail.com")
    if st.button("📨 Gửi về mail"):
        if not user_email:
            st.warning("Vui lòng nhập email!")
        elif len(st.session_state.get("messages", [])) == 0:
            st.warning("Chưa có hội thoại nào để gửi!")
        else:
            with st.spinner("Đang gửi..."):
                result = send_email(user_email, st.session_state.messages)
                if result is True:
                    st.success("✅ Đã gửi thành công!")
                else:
                    st.error(f"❌ Lỗi: {result}")
    st.divider()

    # ===== XEM LOG CÓ MẬT KHẨU (XUỐNG CUỐI) =====
    st.markdown("### 🗂️ Lịch sử câu hỏi")
    admin_pw = st.text_input("Mật khẩu admin:", type="password", placeholder="Nhập mật khẩu...", key="admin_pw_sidebar")
    if st.button("📋 Xem log"):
        if admin_pw == "0913":
            if os.path.exists("chat_log.json"):
                with open("chat_log.json", "r", encoding="utf-8") as f:
                    logs = json.load(f)
                st.markdown(f"**Tổng số: {len(logs)} câu hỏi**")
                for log in reversed(logs[-5:]):
                    danh_gia = log.get("danh_gia", "Chưa đánh giá")
                    with st.expander(f"🕐 {log['thoi_gian']}"):
                        st.markdown(f"**🧑 Hỏi:** {log['cau_hoi']}")
                        st.markdown(f"**🤖 Trả lời:** {log['cau_tra_loi'][:200]}...")
                        st.markdown(f"**⭐ Đánh giá:** {danh_gia}")
            else:
                st.info("Chưa có log nào.")
        else:
            st.error("❌ Sai mật khẩu!")

st.divider()

# ===== JS RIPPLE + COPY =====
st.markdown("""
<script>
function copyText(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const textToCopy = el.innerText || el.textContent;
    navigator.clipboard.writeText(textToCopy).then(function() {
        const btn = document.getElementById('copybtn_' + id);
        if (btn) {
            btn.innerText = '✅ Đã copy!';
            setTimeout(function() { btn.innerText = '📋 Copy'; }, 2000);
        }
    }).catch(function(err) {
        console.error('Lỗi copy: ', err);
    });
}

document.addEventListener('click', function(e) {
    const btn = e.target.closest('button');
    if (!btn) return;
    if (btn.classList.contains('action-btn')) return;
    const circle = document.createElement('span');
    const diameter = Math.max(btn.clientWidth, btn.clientHeight) * 3;
    const radius = diameter / 2;
    const rect = btn.getBoundingClientRect();
    circle.style.position = 'absolute';
    circle.style.width = diameter + 'px';
    circle.style.height = diameter + 'px';
    circle.style.left = (e.clientX - rect.left - radius) + 'px';
    circle.style.top = (e.clientY - rect.top - radius) + 'px';
    circle.style.background = 'rgba(255,255,255,0.35)';
    circle.style.borderRadius = '50%';
    circle.style.transform = 'scale(0)';
    circle.style.animation = 'rippleJS 0.7s ease-out forwards';
    circle.style.pointerEvents = 'none';
    btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.appendChild(circle);
    setTimeout(function() { circle.remove(); }, 700);
});
</script>
""", unsafe_allow_html=True)

# ===== SUGGESTION =====
if len(st.session_state.get("messages", [])) == 0:
    st.markdown("### 💡 Gợi ý câu hỏi")
    col1, col2, col3 = st.columns(3)
    if col1.button("Học bao nhiêu tín chỉ để tốt nghiệp?"):
        st.session_state["suggested_prompt"] = "Học bao nhiêu tín chỉ để tốt nghiệp?"
    if col2.button("Có thể tốt nghiệp sớm được không?"):
        st.session_state["suggested_prompt"] = "Có thể tốt nghiệp sớm được không?"
    if col3.button("Các chuẩn đầu ra của chuyên nghành là?"):
        st.session_state["suggested_prompt"] = "Các chuẩn đầu ra của chuyên nghành là?"

# --- DATA ---
def load_knowledge_base():
    knowledge = ""
    files = ["huong-dan.txt", "QTNNL-handbook.md"]
    for filename in files:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                # Nén tri thức: Bỏ các dòng trống thừa và khoảng trắng ở hai đầu dòng
                lines = f.readlines()
                clean_lines = [l.strip() for l in lines if l.strip()]
                knowledge += f"\n" + "\n".join(clean_lines)
    return knowledge

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "ratings" not in st.session_state:
    st.session_state.ratings = {}

if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "📍 Chế độ Handbook (Nghiêm ngặt)"

# ===== LỜI CHÀO ĐẦU =====
if len(st.session_state.messages) == 0:
    loi_chao = """
    Chào các bạn, mình là AI Chatbot do sinh viên lớp Tuyển dụng 49K17.2 xây dựng nhằm đồng hành và cung cấp thông tin cho những học sinh đang quan tâm đến ngành Quản trị Nhân lực tại Trường Đại học Kinh tế – Đại học Đà Nẵng. Mình sẽ giúp các bạn tìm hiểu rõ hơn về ngành học, chương trình đào tạo và những nội dung liên quan trong quá trình lựa chọn.
    
    ---
    💡 **Mẹo nhỏ để hỗ trợ bạn tốt nhất:**
    *   🔍 **Tra cứu nhanh (Sidebar):** Nhập từ khóa để xem trực tiếp Handbook (**Nhanh & Không giới hạn**).
    *   🤖 **Hỏi đáp AI:** Gõ câu hỏi vào ô bên dưới để mình giải đáp chuyên sâu.
    *   ⏳ **Lưu ý:** Nếu mình báo lỗi quá tải, bạn vui lòng **đợi 1 phút** rồi hỏi lại nhé!
    """
    with st.chat_message("assistant"):
        st.markdown(loi_chao)

# ===== HIỂN THỊ LỊCH SỬ =====
assistant_index = 0
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

    if message["role"] == "assistant":
        msg_id = f"msg_{assistant_index}"
        rating = st.session_state.ratings.get(msg_id, None)
        # Chuẩn bị nội dung để copy (xử lý các ký tự đặc biệt)
        safe_content = message["content"].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', ' ')

        col_like, col_dislike, col_copy, col_rest = st.columns([1.2, 1.2, 1.2, 8.4])
        with col_like:
            label_like = "✅ 👍" if rating == "👍" else "👍 Hữu ích"
            if st.button(label_like, key=f"like_{msg_id}"):
                st.session_state.ratings[msg_id] = "👍"
                update_rating_in_log(assistant_index, "👍")
                st.rerun()
        with col_dislike:
            label_dislike = "✅ 👎" if rating == "👎" else "👎 Chưa tốt"
            if st.button(label_dislike, key=f"dislike_{msg_id}"):
                st.session_state.ratings[msg_id] = "👎"
                update_rating_in_log(assistant_index, "👎")
                st.rerun()
        with col_copy:
            st.markdown(f"""
                <span id="content_{msg_id}" style="display:none">{safe_content}</span>
                <button class="action-btn" id="copybtn_content_{msg_id}"
                    onclick="copyText('content_{msg_id}')">📋 Copy</button>
            """, unsafe_allow_html=True)

        assistant_index += 1

# ===== GIAO DIỆN THANH CHAT NÂNG CẤP (DẤU CỘNG) =====
with st.container():
    col_plus, col_hint, col_info = st.columns([0.6, 3, 6])
    with col_plus:
        with st.popover("➕", help="Thêm tính năng nâng cao"):
            st.markdown("### 🎓 Tiện ích thông minh")
            uploaded_file = st.file_uploader("Phân tích bảng điểm/Ảnh (PDF/JPG/PNG)", type=['pdf', 'png', 'jpg'], key="file_analysis")
            if uploaded_file:
                st.success("✅ Đã nhận tệp! Hãy đặt câu hỏi về tệp này.")
            
            st.divider()
            st.markdown("### ⚙️ Cấu hình AI")
            mode = st.radio("Chọn chế độ trả lời:", 
                            ["📍 Chế độ Handbook (Nghiêm ngặt)", "🚀 Chế độ Career (Tư vấn mở rộng)"],
                            index=0 if st.session_state.chat_mode == "📍 Chế độ Handbook (Nghiêm ngặt)" else 1)
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
        # ===== PROGRESS BAR =====
        progress_placeholder = st.empty()
        status_texts = [
            "🔍 Đang tìm kiếm thông tin...",
            "📚 Đang đọc tài liệu...",
            "🧠 Đang xử lý câu hỏi...",
            "✍️ Đang soạn câu trả lời..."
        ]
        progress_placeholder.markdown(f"""
            <div style="padding: 10px 0;">
                <div style="color:#94a3b8;font-size:13px;margin-bottom:6px">{status_texts[0]}</div>
                <div style="background:rgba(255,255,255,0.08);border-radius:8px;height:6px;width:100%">
                    <div style="background:linear-gradient(90deg,#a78bfa,#38bdf8);height:6px;border-radius:8px;width:5%;transition:width 0.3s ease"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        context = load_knowledge_base()
        
        # ĐIỀU CHỈNH PROMPT THEO CHẾ ĐỘ
        if st.session_state.chat_mode == "🚀 Chế độ Career (Tư vấn mở rộng)":
            instruction = "\n(BẠN ĐANG Ở CHẾ ĐỘ CAREER: Ngoài Handbook, hãy dùng kiến thức chuyên môn rộng lớn của bạn về Quản trị nhân lực để tư vấn chuyên sâu, định hướng nghề nghiệp và kỹ năng cho sinh viên)."
        else:
            instruction = "\n(BẠN ĐANG Ở CHẾ ĐỘ NGHIÊM NGẶT: Chỉ được phép trả lời dựa trên nội dung có trong Handbook. Nếu không tìm thấy thông tin, hãy hướng dẫn sinh viên liên hệ văn phòng Khoa)."

        query_content = [f"Bối cảnh Handbook: {context}\n{instruction}\n\nCâu hỏi của sinh viên: {prompt}"]
        
        # NẾU CÓ FILE THÌ GỬI KÈM CHO AI PHÂN TÍCH
        if st.session_state.get("file_analysis"):
            f = st.session_state.file_analysis
            query_content.insert(0, {"mime_type": f.type, "data": f.read()})

        # Cố gắng gọi API với cơ chế Xoay vòng Key và Thử lại
        success = False
        attempts = 0
        available_keys = VALID_KEYS.copy()
        random.shuffle(available_keys) # Xáo trộn danh sách để xoay vòng

        while not success and attempts < len(available_keys):
            try:
                current_key = available_keys[attempts]
                model = configure_genai(current_key)
                
                # Cập nhật progress trong khi gọi API
                for step, (pct, text) in enumerate(zip([20, 50, 80], status_texts[1:])):
                    time.sleep(0.3)
                    progress_placeholder.markdown(f"""
                        <div style="padding: 10px 0;">
                            <div style="color:#94a3b8;font-size:13px;margin-bottom:6px">{text}</div>
                            <div style="background:rgba(255,255,255,0.08);border-radius:8px;height:6px;width:100%">
                                <div style="background:linear-gradient(90deg,#a78bfa,#38bdf8);height:6px;border-radius:8px;width:{pct}%;transition:width 0.3s ease"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                response = model.generate_content(query_content)
                full_text = response.text
                success = True

            except Exception as e:
                attempts += 1
                if "429" in str(e) and attempts < len(available_keys):
                    # Nếu lỗi 429, thử key tiếp theo
                    continue
                else:
                    progress_placeholder.empty()
                    st.error(f"Lỗi hệ thống: {e}")
                    st.stop()

        if success:
            # 100% xong
            progress_placeholder.markdown(f"""
                <div style="padding: 10px 0;">
                    <div style="color:#94a3b8;font-size:13px;margin-bottom:6px">✅ Hoàn tất!</div>
                    <div style="background:rgba(255,255,255,0.08);border-radius:8px;height:6px;width:100%">
                        <div style="background:linear-gradient(90deg,#a78bfa,#38bdf8);height:6px;border-radius:8px;width:100%"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            time.sleep(0.3)
            progress_placeholder.empty()

            placeholder = st.empty()
            typed_text = ""
            for char in full_text:
                typed_text += char
                placeholder.markdown(highlight_keywords(typed_text))
                time.sleep(0.005)

            highlighted = highlight_keywords(full_text)
            st.session_state.messages.append({
                "role": "assistant",
                "content": highlighted
            })
            save_to_log(prompt, full_text)
            st.rerun()
