import win32com.client
import os

word = win32com.client.Dispatch("Word.Application")
word.Visible = False
doc_path = r"d:\projects\Github\iot\G7\E6公共接口使用手册.doc"

try:
    doc = word.Documents.Open(doc_path)
    text = doc.Content.Text
    with open(r"d:\projects\Github\iot\G7\doc_text_utf8.txt", "w", encoding="utf-8") as f:
        f.write(text)
    doc.Close()
except Exception as e:
    print(f"Error: {e}")
finally:
    word.Quit()
print("Done")
