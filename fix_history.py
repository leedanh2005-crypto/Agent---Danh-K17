import pandas as pd
import csv
from datetime import datetime, timedelta
import io
import os
import re

def fix_mojibake(text):
    if not isinstance(text, str):
        return text
    # Common UTF-8 interpreted as Windows-1252 fixes
    replacements = {
        'Ã¡': 'á', 'Ã ': 'à', 'Ã³': 'ó', 'Ã²': 'ò', 'Ãº': 'ú', 'Ã¹': 'ù',
        'Ã©': 'é', 'Ã¨': 'è', 'Ã­': 'í', 'Ã¬': 'ì', 'Ã¢': 'â', 'Ãª': 'ê',
        'Ã´': 'ô', 'Æ°': 'ư', 'Æ¡': 'ơ', 'Ä‘': 'đ', 'Ã£': 'ã', 'Ã±': 'ñ',
        'Ã¬': 'ì', 'Ã ': 'à', 'Ã´': 'ô', 'Ã³': 'ó', 'Ã¹': 'ù', 'Ãº': 'ú',
        'Äƒ': 'ă', 'Ã¢': 'â', 'Ãª': 'ê', 'Ã´': 'ô', 'Æ¡': 'ơ', 'Æ°': 'ư',
        'Ã¹': 'ù', 'Ãº': 'ú', 'Ã²': 'ò', 'Ã³': 'ó', 'Ã ': 'à', 'Ã¡': 'á',
        'Ã ': 'à', 'Ã¡': 'á', 'Ã¢': 'â', 'Ã£': 'ã', 'Ã¤': 'ä', 'Ã¥': 'å',
        'Ã¦': 'æ', 'Ã§': 'ç', 'Ã¨': 'è', 'Ã©': 'é', 'Ãª': 'ê', 'Ã«': 'ë',
        'Ã¬': 'ì', 'Ã­': 'í', 'Ã®': 'î', 'Ã¯': 'ï', 'Ã°': 'ð', 'Ã±': 'ñ',
        'Ã²': 'ò', 'Ã³': 'ó', 'Ã´': 'ô', 'Ãµ': 'õ', 'Ã¶': 'ö', 'Ã·': '÷',
        'Ã¸': 'ø', 'Ã¹': 'ù', 'Ãº': 'ú', 'Ã»': 'û', 'Ã¼': 'ü', 'Ã½': 'ý',
        'Ã¾': 'þ', 'Ã¿': 'ÿ', 'Ä‘': 'đ', 'Äƒ': 'ă', 'Ä‚': 'Ă', 'Ä ': 'Đ'
    }
    # More aggressive regex for common Vietnamese mojibake patterns
    try:
        # Try to fix by double-encoding/decoding if it's pure mojibake
        # But safer to just use a targeted list for now to avoid breaking correct text
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text
    except:
        return text

file_path = 'chat_history.csv'
temp_path = 'chat_history_temp.csv'

# Read existing data
data = []
with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) >= 4:
            # Fix font errors in all rows
            row = [fix_mojibake(cell) for row in row for cell in [row]] # wait this is wrong
            row = [fix_mojibake(cell) for cell in row]
            data.append(row)

total_entries = len(data)
print(f"Total entries: {total_entries}")

# Update timestamps from entry 250 (0-indexed) to the end
# "câu 250" usually means the 250th question.
start_time = datetime(2026, 5, 9, 8, 0, 0)
if total_entries > 250:
    num_to_fix = total_entries - 249 # fix from index 249 onwards
    # Distribute over 12 hours (8:00 to 20:00)
    total_seconds = 12 * 3600
    increment = total_seconds / num_to_fix
    
    for i in range(249, total_entries):
        current_time = start_time + timedelta(seconds=int((i - 249) * increment))
        data[i][0] = current_time.strftime('%Y-%m-%d %H:%M:%S')

# Write back
with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    writer.writerows(data)

print("Done.")
