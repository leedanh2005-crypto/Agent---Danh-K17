import csv
import os
from datetime import datetime, timedelta

def generate_names(count):
    ho = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng"]
    dem = ["Văn", "Thị", "Thanh", "Minh", "Quốc", "Gia", "Đình", "Ngọc", "Hữu", "Anh"]
    ten = ["Anh", "Bình", "Chi", "Dũng", "Em", "Lâm", "Hải", "Hương", "Khánh", "Linh", "Mai", "Nam", "Phúc", "Quân", "Sơn", "Thảo", "Tuấn", "Vân", "Yến", "Đức"]
    
    names = []
    for i in range(count):
        # Variety: full name vs short name
        if i % 3 == 0:
            names.append(f"{random_choice(ho)} {random_choice(ten)}")
        elif i % 3 == 1:
            names.append(f"{random_choice( ten )}")
        else:
            names.append(f"{random_choice(ho)} {random_choice(dem)} {random_choice(ten)}")
    return names

import random
def random_choice(lst):
    return random.choice(lst)

input_file = 'chat_history.csv'
output_file = 'chat_history.csv'

# 1. Read the template rows (50 to 150)
templates = []
with open(input_file, mode='r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    all_rows = list(reader)
    # Get 100 templates from message 50 (index 49)
    templates = all_rows[49:149]

# 2. Generate new data
new_rows = []
start_time = datetime(2026, 5, 10, 6, 45, 0)
names = generate_names(100)

for i in range(100):
    timestamp = start_time + timedelta(seconds=i * 27) # 45 mins / 100 entries approx 27s
    name = names[i]
    question = templates[i % len(templates)][2]
    answer = templates[i % len(templates)][3]
    new_rows.append([timestamp.strftime('%Y-%m-%d %H:%M:%S'), name, question, answer])

# 3. Append to file
with open(output_file, mode='a', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerows(new_rows)

print(f"Successfully added 100 entries to {output_file}")
