import csv
import random
from datetime import datetime, timedelta

# List of courses from the handbook
courses_vi = [
    "Hành vi tổ chức", "Quản trị nguồn nhân lực", "Quan hệ lao động", "Luật lao động", 
    "Quản trị nguồn nhân lực quốc tế", "Thương lượng", "Hoạch định nguồn nhân lực", 
    "Phát triển nguồn nhân lực", "Quản trị thành tích", "Thù lao", "Tuyển dụng", 
    "Phân tích nhân viên", "Quản trị nguồn nhân lực số", "Tâm lý học", 
    "Đề án Thiết kế chính sách nguồn nhân lực", "Quản trị chiến lược", "Lý thuyết và thiết kế tổ chức"
]

courses_en = [
    "Organizational Behavior", "Human Resource Management", "Labor Relations", "Labor Law",
    "International HRM", "Negotiation", "HR Planning", "Human Resource Development",
    "Performance Management", "Compensation and Benefits", "Recruitment", "People Analytics",
    "Digital HRM", "Psychology", "HR Policy Design Project", "Strategic Management", "Organization Theory and Design"
]

names_vi = ["Nguyễn Văn An", "Trần Thị Bình", "Lê Văn Cường", "Phạm Thị Dung", "Hoàng Văn Em", "Võ Thị Phương", "Đặng Văn Giang", "Bùi Thị Hạnh", "Đỗ Văn Hùng", "Ngô Thị Hoa"]
names_en = ["John Doe", "Jane Smith", "Michael Brown", "Emily Davis", "Chris Wilson", "Sarah Miller", "David Taylor", "Jessica Anderson", "Thomas Jackson", "Linda White"]

topics_vi = [
    "tầm quan trọng của phân tích dữ liệu trong {course}",
    "cách xây dựng hệ thống KPI hiệu quả cho {course}",
    "xu hướng chuyển đổi số trong {course} tại các doanh nghiệp Việt Nam",
    "mối liên hệ giữa {course} và chiến lược kinh doanh của tổ chức",
    "thách thức về đạo đức nghề nghiệp trong {course}",
    "các mô hình hiện đại được áp dụng trong {course}",
    "kỹ năng cần thiết cho một chuyên gia trong lĩnh vực {course}",
    "tác động của AI đến quy trình thực hiện {course}",
    "tối ưu hóa trải nghiệm nhân viên thông qua {course}",
    "vai trò của văn hóa doanh nghiệp trong việc triển khai {course}"
]

topics_en = [
    "the importance of data analytics in {course}",
    "how to build an effective KPI system for {course}",
    "digital transformation trends in {course} at global enterprises",
    "the link between {course} and organizational business strategy",
    "ethical challenges in {course}",
    "modern models applied in {course}",
    "essential skills for a specialist in the field of {course}",
    "the impact of AI on {course} processes",
    "optimizing employee experience through {course}",
    "the role of corporate culture in implementing {course}"
]

def generate_answer_vi(course, topic_template):
    topic = topic_template.format(course=course)
    greeting = "Chào bạn!"
    
    body = f"""
Rất vui được thảo luận sâu hơn cùng bạn về {topic}. Trong chương trình đào tạo tại Trường Đại học Kinh tế - ĐHĐN [1], đây là một nội dung trọng tâm giúp sinh viên hình thành tư duy quản trị hiện đại.

Để phân tích sâu về vấn đề này, trước hết chúng ta cần hiểu rằng {course} không chỉ đơn thuần là một học phần lý thuyết mà là một hệ thống các công cụ thực tế. Khi áp dụng vào môi trường doanh nghiệp Việt Nam, chúng ta thường gặp phải những thách thức về sự khác biệt thế hệ và văn hóa vùng miền. Việc triển khai {topic} đòi hỏi nhà quản trị phải có cái nhìn đa chiều, kết hợp giữa yếu tố tâm lý con người và các chỉ số đo lường khoa học [2].

Thứ nhất, xét về góc độ chiến lược, {course} đóng vai trò là "xương sống" để kết nối mục tiêu cá nhân với mục tiêu tổ chức. Như PLO 3 đã chỉ ra, việc tích hợp các chức năng nhân sự với lợi thế cạnh tranh là yếu tố sống còn. Khi bạn thực hiện {topic}, bạn đang trực tiếp góp phần vào việc tối ưu hóa nguồn lực quý giá nhất của công ty. 

Thứ hai, trong kỷ nguyên số, chúng ta không thể bỏ qua vai trò của công nghệ. Quản trị nguồn nhân lực số (Digital HR) đang làm thay đổi cách thức chúng ta tiếp cận {course}. Thay vì những bảng tính thủ công, các hệ thống AI và Big Data cho phép chúng ta dự báo xu hướng biến động nhân sự và phân tích hiệu suất làm việc theo thời gian thực [3].

Thứ ba, yếu tố đạo đức và pháp luật luôn phải được đặt lên hàng đầu. Trong học phần Luật lao động, sinh viên DUE được trang bị kiến thức vững chắc để đảm bảo mọi chính sách liên quan đến {course} đều công bằng và minh bạch. Điều này giúp xây dựng lòng tin bền vững giữa người lao động và tổ chức [4].

Cuối cùng, việc rèn luyện kỹ năng mềm như giao tiếp và tư duy phản biện (theo chuẩn PLO 5 và 6) sẽ giúp bạn triển khai {topic} một cách hiệu quả nhất. Đừng chỉ nhìn vào con số, hãy nhìn vào con người đứng sau những con số đó.

Chúc bạn luôn giữ được lửa đam mê với ngành Quản trị nhân lực!
"""
    
    sources = "\n\n---TRÍCH DẪN NGUỒN---\n[1] Sổ tay sinh viên DUE - Phần 0: Chương trình đào tạo ngành QTNNL.\n[2] Giáo trình Quản trị nguồn nhân lực, NXB Kinh tế TP.HCM.\n[3] Chuẩn đầu ra PLO ngành Quản trị nhân lực DUE.\n[4] Quy chế đào tạo trình độ đại học DUE."
    
    full_text = f"{greeting} {body.strip()}{sources}"
    return full_text

def generate_answer_en(course, topic_template):
    topic = topic_template.format(course=course)
    greeting = "Hello!"
    
    body = f"""
I am delighted to discuss {topic} in depth with you. Within the curriculum at the University of Economics - DUE [1], this is a core subject that helps students develop modern management thinking.

To analyze this issue thoroughly, we must first understand that {course} is not merely a theoretical subject but a system of practical tools. When applied in a real corporate environment, we often face challenges regarding generational differences and regional cultural nuances. Implementing {topic} requires managers to have a multi-dimensional perspective, combining human psychology with scientific measurement metrics [2].

Firstly, from a strategic standpoint, {course} serves as the 'backbone' connecting individual goals with organizational objectives. As PLO 3 points out, integrating HR functions with competitive advantage is vital. When you implement {topic}, you are directly contributing to optimizing the company's most valuable resource.

Secondly, in the digital era, we cannot ignore the role of technology. Digital HRM is transforming the way we approach {course}. Instead of manual spreadsheets, AI and Big Data systems allow us to forecast personnel turnover trends and analyze performance in real-time [3].

Thirdly, ethical and legal factors must always be prioritized. In the Labor Law course, DUE students are equipped with solid knowledge to ensure that all policies related to {course} are fair and transparent. This helps build trust and sustainable engagement between employees and the organization [4].

Finally, practicing soft skills such as communication and critical thinking (according to PLO 5 and 6 standards) will help you implement {topic} most effectively. Don't just look at the numbers; look at the people behind those numbers.

Wishing you continued passion for the Human Resource Management field!
"""
    
    sources = "\n\n---SOURCES---\n[1] DUE Student Handbook - Section 0: HRM Program Curriculum.\n[2] HRM Textbook, University of Economics Publishing House.\n[3] PLO Outcomes for HRM Major at DUE.\n[4] DUE Undergraduate Training Regulations."
    
    full_text = f"{greeting} {body.strip()}{sources}"
    return full_text

def main():
    start_time = datetime.strptime("2026-05-09 20:00:00", "%Y-%m-%d %H:%M:%S")
    entries = []
    
    used_questions = set()
    
    for i in range(100):
        timestamp = (start_time + timedelta(seconds=i*30)).strftime("%Y-%m-%d %H:%M:%S")
        
        is_vi = random.random() < 0.8
        
        if is_vi:
            name = random.choice(names_vi)
            course = random.choice(courses_vi)
            topic_template = random.choice(topics_vi)
            question = f"Hãy phân tích {topic_template.format(course=course)} trong thực tế."
            
            while question in used_questions:
                course = random.choice(courses_vi)
                topic_template = random.choice(topics_vi)
                question = f"Hãy phân tích {topic_template.format(course=course)} trong thực tế."
            used_questions.add(question)
            
            answer = generate_answer_vi(course, topic_template)
        else:
            name = random.choice(names_en)
            course = random.choice(courses_en)
            topic_template = random.choice(topics_en)
            question = f"Please analyze {topic_template.format(course=course)} in practice."
            
            while question in used_questions:
                course = random.choice(courses_en)
                topic_template = random.choice(topics_en)
                question = f"Please analyze {topic_template.format(course=course)} in practice."
            used_questions.add(question)
            
            answer = generate_answer_en(course, topic_template)
            
        entries.append([timestamp, name, question, answer])
        
    with open('D:\\Agent A.I\\new_entries.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(entries)

if __name__ == "__main__":
    main()
