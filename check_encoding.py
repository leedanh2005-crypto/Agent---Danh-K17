
import sys

file_path = "D:\\Agent A.I\\chat_history.csv"
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if 'Ã' in line:
                print(f"First occurrence of 'Ã' at line {i}")
                print(line[:100])
                break
except Exception as e:
    print(f"Error: {e}")
