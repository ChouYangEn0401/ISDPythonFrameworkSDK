import pandas as pd
from sqlalchemy import create_engine
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os


# ---------------- Tkinter GUI ----------------
def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)


def start_upload():
    excel_path = entry_file.get()
    if not excel_path or not os.path.isfile(excel_path):
        messagebox.showerror("錯誤", "請先選擇有效的 Excel 檔案")
        return

    # 讀取 Excel
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        messagebox.showerror("錯誤", f"讀取 Excel 檔案失敗: {e}")
        return

    # 建立 SQLAlchemy 連線
    server = os.getenv('DB_SERVER')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_DATABASE')
    connection_string = f'mssql+pyodbc://{user}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server'
    engine = create_engine(connection_string)

    # 分批寫入 DataFrame，更新進度條
    batch_size = 5000
    total_rows = len(df)
    num_batches = (total_rows // batch_size) + 1

    progress_bar['maximum'] = num_batches
    root.update_idletasks()

    try:
        for i in range(num_batches):
            start_row = i * batch_size
            end_row = min((i + 1) * batch_size, total_rows)
            df.iloc[start_row:end_row].to_sql('表單名稱', con=engine, schema='dbo',
                                              if_exists='append' if i > 0 else 'replace', index=False)
            progress_bar['value'] = i + 1
            root.update_idletasks()

        messagebox.showinfo("完成", f"成功將 {total_rows} 筆資料寫入 SQL Server！")

    except Exception as e:
        messagebox.showerror("錯誤", f"寫入 SQL Server 發生錯誤: {e}")


# ---------------- GUI 介面 ----------------
root = tk.Tk()
root.title("Excel 上傳 SQL Server")

tk.Label(root, text="選擇 Excel 檔案:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
entry_file = tk.Entry(root, width=50)
entry_file.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="瀏覽", command=select_file).grid(row=0, column=2, padx=10, pady=10)

# 預設先填入 pris_aca_export_test.xlsx
default_file = os.path.join(os.getcwd(), "pris_aca_export_test.xlsx")
if os.path.isfile(default_file):
    entry_file.insert(0, default_file)

tk.Button(root, text="開始上傳", command=start_upload).grid(row=1, column=0, columnspan=3, pady=10)

progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
progress_bar.grid(row=2, column=0, columnspan=3, padx=10, pady=20)

root.mainloop()
