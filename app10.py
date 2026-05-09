import streamlit as st
import google.generativeai as genai
import os
import base64
import time
import smtplib
import json
import csv
import re
import io
import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import Counter
from gtts import gTTS

# --- 1. CONFIG & SESSION ---
st.set_page_config(
    page_title="Hệ thống Trợ lý Sinh viên K17", 
    page_icon="🎓", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Initialize Session States
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "📍 Chế độ Tra cứu (Nghiêm ngặt)"
if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False
if "api_key_index" not in st.session_state:
    st.session_state.api_key_index = 0
if "last_response" not in st.session_state:
    st.session_state.last_response = ""

# --- USER NAME GATE ---
if "user_name" not in st.session_state:
    st.markdown("""
    <style>
    .gate-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        max-width: 600px;
        margin: 100px auto;
    }
    .gate-title { color: #a78bfa; font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; }
    .gate-subtitle { color: #94a3b8; font-size: 1.1rem; margin-bottom: 30px; }
    </style>
    <div class="gate-container">
        <div class="gate-title">👋 Xin chào!</div>
        <div class="gate-subtitle">Chào mừng bạn đến với Trợ lý K17. Vui lòng nhập tên để bắt đầu.</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name_input = st.text_input("Tên của bạn:", key="input_user_name", placeholder="Ví dụ: Nguyễn Văn A")
        if st.button("🚀 Vào hệ thống", use_container_width=True):
            if name_input.strip():
                st.session_state.user_name = name_input.strip()
                st.rerun()
            else:
                st.error("⚠️ Vui lòng nhập tên của bạn!")
    st.stop()

# --- 2. API KEYS & ROTATION ---
API_KEYS = [
    "AIzaSyCj4pscK0i9elDxr9vdjBJfDEoN6JB78Ik",
    "AIzaSyCOtyj9DzIJzCMVuYnD1t6Y7QfxulXDrOA",
    "AIzaSyA5WUHRZrtN5VTZ-hPOXflktQVj0LdY1Aw"
]

def get_gemini_model():
    key = API_KEYS[st.session_state.api_key_index % len(API_KEYS)]
    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-1.5-flash-latest')

def rotate_api_key():
    st.session_state.api_key_index += 1

# --- 3. PREMIUM UI (CSS) ---
st.markdown("""
<style>
    /* Global Glassmorphism */
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
        color: #f1f5f9;
    }
    
    /* Radial Gradients for specific modes */
    .search-mode { background: radial-gradient(circle, #083344 0%, #0f172a 100%); }
    .consult-mode { background: radial-gradient(circle, #2e1065 0%, #0f172a 100%); }

    /* Shimmer Progress Bar */
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    .shimmer-bar {
        height: 4px;
        width: 100%;
        background: linear-gradient(90deg, #3b82f6 25%, #60a5fa 50%, #3b82f6 75%);
        background-size: 200% 100%;
        animation: shimmer 2s infinite linear;
        border-radius: 2px;
        margin: 10px 0;
    }

    /* Thinking Wave */
    .wave {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 5px;
        padding: 10px;
    }
    .dot {
        width: 8px;
        height: 8px;
        background: #a78bfa;
        border-radius: 50%;
        animation: wave 1.5s infinite ease-in-out;
    }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes wave {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }

    /* Message Bubbles */
    .user-msg {
        background: rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 15px;
        border-radius: 15px 15px 0 15px;
        margin: 10px 0;
        backdrop-filter: blur(5px);
    }
    .ai-msg {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 15px 15px 15px 0;
        margin: 10px 0;
        backdrop-filter: blur(5px);
    }
    
    /* Citation Buttons */
    .cite-btn {
        display: inline-block;
        padding: 2px 8px;
        margin: 0 2px;
        background: #334155;
        color: #94a3b8;
        border-radius: 4px;
        font-size: 0.8rem;
        text-decoration: none;
        cursor: pointer;
        border: 1px solid #475569;
    }
    .cite-btn:hover { background: #475569; color: #f1f5f9; }
</style>
""", unsafe_allow_html=True)

# --- 4. INTELLIGENT RAG & KNOWLEDGE ---
def load_rag_knowledge(query):
    knowledge = ""
    # 1. Base Handbook
    paths = ["huong-dan.txt", "QTNNL-handbook.md"]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                knowledge += f"\n[NGUỒN: {p}]\n{f.read()}\n"
    
    # 2. Selective Skills
    skills_root = "claude-skills"
    if os.path.exists(skills_root):
        domain_keywords = {
            "c-level-advisor": ["lãnh đạo", "giám đốc", "quản trị", "chiến lược", "ceo", "cto", "cfo"],
            "project-management": ["dự án", "kế hoạch", "tiến độ", "nhóm", "quản lý dự án"],
            "engineering": ["kỹ thuật", "lập trình", "code", "phát triển", "kiến trúc"],
            "finance": ["tài chính", "ngân sách", "chi phí", "lương", "đầu tư"],
            "marketing-skill": ["marketing", "truyền thông", "quảng cáo", "nội dung", "seo"]
        }
        
        q_lower = query.lower()
        matched_domains = [d for d, keywords in domain_keywords.items() if any(k in q_lower for k in keywords)]
        
        # Limit to top 2 matched domains to save context
        for domain in matched_domains[:2]:
            domain_path = os.path.join(skills_root, domain)
            if os.path.isdir(domain_path):
                # Look for SKILL.md in subdirectories
                for root, dirs, files in os.walk(domain_path):
                    if "SKILL.md" in files:
                        with open(os.path.join(root, "SKILL.md"), "r", encoding="utf-8") as f:
                            knowledge += f"\n[NGUỒN KỸ NĂNG: {root}]\n{f.read()}\n"
    return knowledge

# --- 5. CITATIONS & SIDEBAR ---
def parse_and_display_citations(res_text, context):
    citations = re.findall(r"\[(\d+)\]", res_text)
    if citations:
        with st.sidebar:
            st.divider()
            st.subheader("📖 Đối chiếu nguồn gốc")
            # In a real app, we'd map [1] to a specific part of 'context'.
            # For this demo, we'll split context by sources.
            sources = context.split("[NGUỒN")
            for c in sorted(set(citations)):
                idx = int(c)
                if idx < len(sources):
                    with st.expander(f"Nguồn [{c}]"):
                        st.write(sources[idx].strip() if idx > 0 else sources[0].strip())
                else:
                    st.caption(f"Nguồn [{c}] từ tri thức hệ thống.")

# --- 6. VOICE OUTPUT ---
def generate_voice(text):
    try:
        clean_text = re.sub(r'\[\d+\]', '', text) # Remove citations
        clean_text = re.sub(r'```.*?```', '', clean_text, flags=re.DOTALL) # Remove code
        tts = gTTS(text=clean_text[:500], lang='vi') # Limit to first 500 chars for speed
        tts.save("temp_tts.mp3")
        with open("temp_tts.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
            st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Lỗi giọng nói: {e}")

# --- 7. SIDEBAR & ADMIN ---
with st.sidebar:
    st.title("🛠️ Công cụ & Cài đặt")
    st.info(f"👤 Người dùng: **{st.session_state.user_name}**")
    
    st.session_state.chat_mode = st.selectbox(
        "Chế độ hoạt động:",
        ["📍 Chế độ Tra cứu (Nghiêm ngặt)", "💡 Chế độ Tư vấn (Sáng tạo)"]
    )
    
    st.divider()
    
    # Handbook Search
    st.subheader("📖 Tra cứu Handbook")
    search_query = st.text_input("Tìm nhanh trong tài liệu:")
    if search_query:
        # Simple grep logic
        if os.path.exists("QTNNL-handbook.md"):
            with open("QTNNL-handbook.md", "r", encoding="utf-8") as f:
                content = f.read()
                results = re.findall(f".{{0,50}}{search_query}.{{0,50}}", content, re.IGNORECASE)
                if results:
                    for r in results[:5]: st.caption(f"...{r}...")
                else: st.warning("Không tìm thấy.")

    st.divider()
    
    # Links & History
    with st.expander("🔗 Liên kết hữu ích"):
        st.markdown("- [Cổng thông tin sinh viên](https://sv.example.com)")
        st.markdown("- [Lịch học & thi](https://lich.example.com)")
        st.markdown("- [Thư viện số](https://lib.example.com)")

    # Admin Dashboard
    with st.expander("🔒 Admin Dashboard"):
        pw = st.text_input("Mật khẩu:", type="password")
        if pw == "0913":
            st.success("Quyền Admin được xác nhận")
            
            # API Status
            st.write(f"API Key Index: {st.session_state.api_key_index}")
            st.progress((st.session_state.api_key_index % 3 + 1) / 3)
            
            # Plotly Charts
            df_log = pd.DataFrame([
                {"Topic": "Học bổng", "Count": 45},
                {"Topic": "Đăng ký tín chỉ", "Count": 32},
                {"Topic": "Tốt nghiệp", "Count": 18},
                {"Topic": "Khác", "Count": 10}
            ])
            fig = px.pie(df_log, values='Count', names='Topic', title='Chủ đề quan tâm')
            st.plotly_chart(fig, use_container_width=True)
            
            # Satisfaction
            fig2 = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = 85,
                title = {'text': "Độ hài lòng (%)"},
                gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#a78bfa"}}
            ))
            st.plotly_chart(fig2, use_container_width=True)

# --- 8. MAIN CHAT INTERFACE ---
st.title("🎓 Trợ lý Sinh viên K17")
st.caption("AI được huấn luyện dựa trên Handbook và Tri thức chuyên gia")

# Suggestions Chips
st.markdown("---")
cols = st.columns(3)
with cols[0]:
    if st.button("💳 Quy định học phí"): st.session_state.messages.append({"role": "user", "content": "Quy định về đóng học phí và các khoản phí như thế nào?"})
with cols[1]:
    if st.button("🎓 Điều kiện tốt nghiệp"): st.session_state.messages.append({"role": "user", "content": "Điều kiện để được xét tốt nghiệp là gì?"})
with cols[2]:
    if st.button("⏩ Học vượt / Rút môn"): st.session_state.messages.append({"role": "user", "content": "Thủ tục đăng ký học vượt hoặc rút bớt học phần?"})

# Display Chat
for i, msg in enumerate(st.session_state.messages):
    div_class = "user-msg" if msg["role"] == "user" else "ai-msg"
    st.markdown(f'<div class="{div_class}">{msg["content"]}</div>', unsafe_allow_html=True)
    if msg["role"] == "assistant" and i == len(st.session_state.messages) - 1:
        if st.button("🔊 Nghe", key=f"voice_{i}"):
            generate_voice(msg["content"])

# Chat Input
if prompt := st.chat_input("Hỏi tôi bất cứ điều gì về quy định sinh viên..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)

    with st.chat_message("assistant"):
        # Thinking Animation
        status_placeholder = st.empty()
        status_placeholder.markdown("""
        <div class="wave"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
        <div style="text-align:center; color:#94a3b8; font-size:0.9rem;">Đang kết nối tri thức...</div>
        <div class="shimmer-bar"></div>
        """, unsafe_allow_html=True)
        
        try:
            # RAG
            context = load_rag_knowledge(prompt)
            model = get_gemini_model()
            
            sys_instr = f"""Bạn là Trợ lý Sinh viên K17. 
            Tên người dùng: {st.session_state.user_name}.
            Chế độ: {st.session_state.chat_mode}.
            Sử dụng ngữ cảnh sau để trả lời: {context}
            
            QUY TẮC:
            1. Trả lời chuyên nghiệp, thân thiện.
            2. Sử dụng Markdown (đậm, nghiêng, danh sách).
            3. Nếu có quy trình phức tạp, hãy tạo sơ đồ Mermaid.
            4. Trích dẫn nguồn bằng [1], [2] tương ứng với các đoạn văn bản trong ngữ cảnh.
            5. Nếu không có trong ngữ cảnh, hãy nói bạn không chắc chắn nhưng gợi ý hướng tìm kiếm.
            """
            
            full_prompt = f"{prompt}\n\nHãy trả lời chi tiết và kèm theo trích dẫn."
            
            response = model.generate_content([sys_instr, full_prompt])
            res_text = response.text
            
            status_placeholder.empty()
            st.markdown(f'<div class="ai-msg">{res_text}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": res_text})
            
            # Citations
            parse_and_display_citations(res_text, context)
            
            st.rerun()

        except Exception as e:
            status_placeholder.empty()
            if "429" in str(e):
                st.warning("🔄 Đang chuyển đổi API Key...")
                rotate_api_key()
                st.rerun()
            else:
                st.error(f"Đã xảy ra lỗi: {e}")

# --- 9. FOOTER ---
st.markdown("""
<div style="text-align:center; margin-top:50px; color:#64748b; font-size:0.8rem;">
    Hệ thống hỗ trợ sinh viên tự động v2.0 | © 2024 K17 Student Assistant
</div>
""", unsafe_allow_html=True)
