import csv
import os
import re

def fix_vietnamese_mojibake(text):
    if not isinstance(text, str):
        return text
    try:
        # Try to fix by encoding as cp1252 and decoding as utf-8
        # This fixes common 'Ã¡' -> 'á' etc.
        fixed = text.encode('cp1252').decode('utf-8')
        return fixed
    except:
        # If it fails, fall back to manual map or return original
        # Some specific ones that often fail the above:
        manual_map = {
            'á»¹': 'ỹ', 'áº¡': 'ạ', 'á»©': 'ứ', 'á»­': 'ử', 'á»‘': 'ố',
            'á»“': 'ồ', 'á»—': 'ỗ', 'á»™': 'ộ', 'á»›': 'ớ', 'á»': 'ờ',
            'á»Ÿ': 'ở', 'á»¡': 'ỡ', 'á»£': 'ợ', 'á»¥': 'ụ', 'á»§': 'ủ',
            'á»©': 'ứ', 'á»«': 'ừ', 'á»­': 'ử', 'á»¯': 'ữ', 'á»±': 'ự',
            'áº£': 'ả', 'áº¡': 'ạ', 'áº¥': 'ấ', 'áº§': 'ầ', 'áº©': 'ẩ',
            'áº«': 'ẫ', 'áº­': 'ậ', 'áº¯': 'ắ', 'áº±': 'ằ', 'áº³': 'ẳ',
            'áºµ': 'ẵ', 'áº·': 'ặ', 'áº¹': 'ẹ', 'áº»': 'ẻ', 'áº½': 'ẽ',
            'áº¿': 'ế', 'á»': 'ề', 'á»ƒ': 'ể', 'á»…': 'ễ', 'á»‡': 'ệ',
            'á»‰': 'ỉ', 'á»‹': 'ị', 'á»': 'ọ', 'á»‘': 'ố', 'á»“': 'ồ',
            'á»•': 'ổ', 'á»—': 'ỗ', 'á»™': 'ộ', 'á»›': 'ớ', 'á»': 'ờ',
            'á»Ÿ': 'ở', 'á»¡': 'ỡ', 'á»£': 'ợ', 'á»¥': 'ụ', 'á»§': 'ủ',
            'á»©': 'ứ', 'á»«': 'ừ', 'á»­': 'ử', 'á»¯': 'ữ', 'á»±': 'ự',
            'á»³': 'ỳ', 'á»µ': 'ỵ', 'á»·': 'ỷ', 'á»¹': 'ỹ', 'Ä‘': 'đ',
            'Äƒ': 'ă', 'Ä‚': 'Ă', 'Ä': 'Đ', 'Ã ': 'à', 'Ã¡': 'á',
            'Ã¢': 'â', 'Ã£': 'ã', 'Ã¨': 'è', 'Ã©': 'é', 'Ãª': 'ê',
            'Ã¬': 'ì', 'Ã­': 'í', 'Ã²': 'ò', 'Ã³': 'ó', 'Ã´': 'ô',
            'Ãµ': 'õ', 'Ã¹': 'ù', 'Ãº': 'ú', 'Ã½': 'ý', 'Ã ': 'À',
            'Ã': 'Á', 'Ã‚': 'Â', 'Ãƒ': 'Ã', 'Ãˆ': 'È', 'Ã‰': 'É',
            'ÃŠ': 'Ê', 'ÃŒ': 'Ì', 'Ã': 'Í', 'Ã’': 'Ò', 'Ã“': 'Ó',
            'Ã”': 'Ô', 'Ã•': 'Õ', 'Ã™': 'Ù', 'Ãš': 'Ú', 'Ã': 'Ý',
            'Æ¡': 'ơ', 'Æ°': 'ư', 'Æ¯': 'Ư', 'Æ ': 'Ơ'
        }
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

print("Font errors fixed.")
