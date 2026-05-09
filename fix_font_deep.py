import csv
import os

def fix_vietnamese_mojibake(text):
    if not isinstance(text, str):
        return text
    
    # List of known double-garbled or persistent mojibake
    manual_map = {
        'DáºªN': 'DẪN',
        'NGUá»’N': 'NGUỒN',
        'lÄ©nh': 'lĩnh',
        'Há»c': 'Học',
        'pháº§n': 'phần',
        'TrÃ­ch': 'Trích',
        'táº¡i': 'tại',
        'dưá»£c': 'được',
        'vá»›i': 'với',
        'nhá»¯ng': 'những',
        'vá»‹': 'vị',
        'trí': 'trí',
        'thưá»ng': 'thường',
        'vá»': 'về',
        'ká»¹': 'kỹ',
        'năng': 'năng',
        'đÃ o': 'đào',
        'táº¡o': 'tạo',
        'tá»•': 'tổ',
        'chá»©c': 'chức',
        'táº­p': 'tập',
        'trá»ng': 'trọng',
        'hiá»‡u': 'hiệu',
        'quáº£': 'quả',
        'chá»©ng': 'chứng',
        'minh': 'minh',
        'giá': 'giá',
        'trá»‹': 'trị',
        'hoáº¡t': 'hoạt',
        'đá»™ng': 'động',
        'lãnh': 'lãnh',
        'đáº¡t': 'đạt',
        'hÃ nh': 'hành',
        'vi': 'vi',
        'pháº£i': 'phải',
        'ngưá»i': 'người',
        'nghiá»‡p': 'nghiệp',
        'chuáº©n': 'chuẩn',
        'quá»‘c': 'quốc',
        'gia': 'gia',
        'sá»­': 'sử',
        'dá»¥ng': 'dụng',
        'thÃ nh': 'thành',
        'tháº¡o': 'thạo',
        'pháº§n': 'phần',
        'má»m': 'mềm',
        'á»©ng': 'ứng',
        'dá»¥ng': 'dụng',
        'quáº£n': 'quản',
        'trá»‹': 'trị',
        'nguá»“n': 'nguồn',
        'nhân': 'nhân',
        'lá»±c': 'lực',
        'thá»‘ng': 'thống',
        'kê': 'kê',
        'táº¿': 'tế',
        'vÃ ': 'và',
        'kinh': 'kinh',
        'Sá»±': 'Sự',
        'khác': 'khác',
        'biá»‡t': 'biệt',
        'giá»¯a': 'giữa',
        'dưá»£c': 'được'
    }
    
    # Try the standard fix first
    try:
        fixed = text.encode('cp1252').decode('utf-8')
        # Check if it still has common garble indicators
        if 'Ã' in fixed or 'áº' in fixed or 'á»' in fixed:
             for k, v in manual_map.items():
                fixed = fixed.replace(k, v)
        return fixed
    except:
        for k, v in manual_map.items():
            text = text.replace(k, v)
        return text

file_path = 'chat_history.csv'
data = []

with open(file_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) >= 4:
            row = [fix_vietnamese_mojibake(cell) for cell in row]
            data.append(row)

with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    writer.writerows(data)

print("Font errors deep cleaned.")
