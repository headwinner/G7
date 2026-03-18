import win32com.client
import os

word = win32com.client.Dispatch("Word.Application")
word.Visible = False

doc_path = r"d:\projects\Github\iot\G7\E6公共接口使用手册.doc"
txt_path = r"d:\projects\Github\iot\G7\doc_text.txt"

try:
    doc = word.Documents.Open(doc_path)
    doc.SaveAs(txt_path, FileFormat=2) # 2 = wdFormatText
    doc.Close()
except Exception as e:
    print(f"Error: {e}")
finally:
    word.Quit()
print("Done")
