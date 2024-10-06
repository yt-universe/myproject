from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
import streamlit as st
import pandas as pd
import pymongo
from bson.objectid import ObjectId
from datetime import datetime
import gridfs
from PIL import Image
import io

# 設定 Streamlit 頁面為寬模式
st.set_page_config(layout="wide")

'''# 連接到 MongoDB 資料庫
client = pymongo.MongoClient("mongodb://localhost:27017/")
# 創建及選擇數據庫
mydb = client["lost_database"]

# 創建及選擇集合
mycollection = mydb["lose_found"] '''

# 替換原本的本地 MongoDB 連接，改為 MongoDB Atlas 連接字串

# 替換 <your_username> 和 <your_password> 為你的 MongoDB Atlas 帳戶資訊
uri = "mongodb+srv://aaa0972947323:12@cluster0.lkadm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# 建立 MongoDB 客戶端並連接到 Atlas
client = MongoClient(uri, server_api=ServerApi('1'))

# 選擇你在 MongoDB Atlas 中建立的資料庫
mydb = client["lost_database"]

# 選擇集合
mycollection = mydb["lose_found"]

# 初始化 GridFS
fs = gridfs.GridFS(mydb)


# 網站的標題
st.title("失物招領網站")

# 創建三個分頁，將"查看所有遺失物"和"遺失物列表"位置交換
tab1, tab3, tab2 = st.tabs(["失物招領通報", "查看所有遺失物", "遺失物列表（僅限管理者）"])

# 失物招領通報
with tab1:
    with st.form("失物招領表單", clear_on_submit=True):
        item_name = st.text_input("物品名稱", placeholder="必填")
        item_campus = st.text_input("通報校區", placeholder="必填")
        item_block = st.text_input("通報棟別", placeholder="必填")
        item_classroom_code = st.text_input("通報教室代號", placeholder="必填")
        item_place = st.text_input("通報地點", placeholder="必填")
        item_time = st.date_input("通報時間")
        item_time = datetime(item_time.year, item_time.month, item_time.day)
        item_people = st.text_input("通報人", placeholder="必填")
        item_number = st.text_input("通報人電話", placeholder="必填")

        # 新增照片上傳
        uploaded_file = st.file_uploader("上傳物品照片", type=["jpg", "png", "jpeg"])

        button = st.form_submit_button("送出")

        if button:
            if not item_name or not item_campus or not item_block or not item_classroom_code or not item_place or not item_people or not item_number:
                st.error("所有欄位均為必填，請填寫完整資訊。")
            elif uploaded_file is None:
                st.error("請上傳物品照片。")
            else:
                # 將文件儲存到 GridFS
                file_id = fs.put(uploaded_file.read(),
                                 filename=uploaded_file.name)
                # 插入資料到 MongoDB，保存圖片的文件 ID
                mydict = {
                    "name": item_name,
                    "campus": item_campus,
                    "block": item_block,
                    "classroom_code": item_classroom_code,
                    "place": item_place,
                    "time": item_time,
                    "people": item_people,
                    "number": item_number,
                    "photo_id": file_id,
                }
                insert_result = mycollection.insert_one(mydict)
                if insert_result.acknowledged:
                    st.success("資料已成功插入！")
                else:
                    st.error("資料插入失敗，請再試一次")

# 新增的查看所有遺失物品頁面 (供使用者查看)
with tab3:
    st.header("目前登記的所有遺失物")

    # 從 MongoDB 中檢索所有數據
    cursor = mycollection.find({}).sort("time", -1)
    count = 0
    col1, col2 = st.columns(2)  # 將資料分兩欄顯示

    for row in cursor:
        if count % 2 == 0:  # 偶數放在左邊
            with col1:
                # 使用 columns 讓圖片與資訊併排顯示，並在兩者之間加入空白
                col_data1, col_space1, col_image1 = st.columns(
                    [2, 0.5, 1])  # 增加 col_space 做為空白
                with col_data1:
                    st.write(f"物品名稱: {row['name']}")
                    st.write(f"校區: {row['campus']}")
                    st.write(f"棟別: {row['block']}")
                    st.write(f"教室代號: {row['classroom_code']}")
                    st.write(f"通報地點: {row['place']}")
                    # 檢查時間欄位是否存在並且格式化顯示
                    if isinstance(row['time'], datetime):
                        st.write(
                            f"通報時間: {row['time'].strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        st.write("通報時間: 資料無效")
                    st.write(f"通報人: {row['people']}")
                    st.write(f"電話: {row['number']}")

                with col_image1:
                    # 顯示圖片（如果有）
                    if 'photo_id' in row and row['photo_id'] is not None:
                        try:
                            file_id = ObjectId(row['photo_id'])
                            file_data = fs.get(file_id).read()
                            image = Image.open(io.BytesIO(file_data))
                            st.image(image, caption="物品照片",
                                     use_column_width=True)
                        except Exception as e:
                            st.error(f"無法顯示圖片: {e}")
                    else:
                        st.write("無照片")
                st.write("---")  # 分隔每個物品
        else:  # 奇數放在右邊
            with col2:
                col_data2, col_space2, col_image2 = st.columns([2, 0.5, 1])
                with col_data2:
                    st.write(f"物品名稱: {row['name']}")
                    st.write(f"校區: {row['campus']}")
                    st.write(f"棟別: {row['block']}")
                    st.write(f"教室代號: {row['classroom_code']}")
                    st.write(f"通報地點: {row['place']}")
                    if isinstance(row['time'], datetime):
                        st.write(
                            f"通報時間: {row['time'].strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        st.write("通報時間: 資料無效")
                    st.write(f"通報人: {row['people']}")
                    st.write(f"電話: {row['number']}")

                with col_image2:
                    if 'photo_id' in row and row['photo_id'] is not None:
                        try:
                            file_id = ObjectId(row['photo_id'])
                            file_data = fs.get(file_id).read()
                            image = Image.open(io.BytesIO(file_data))
                            st.image(image, caption="物品照片",
                                     use_column_width=True)
                        except Exception as e:
                            st.error(f"無法顯示圖片: {e}")
                    else:
                        st.write("無照片")
                st.write("---")  # 分隔每個物品
        count += 1


# 添加身份驗證以查看管理者頁面
with tab2:
    st.header("遺失物列表與刪除功能（僅限管理者）")

    # 讓用戶輸入密碼
    password = st.text_input("請輸入管理者密碼以檢視資料", type="password")

    if password == "123":  # 假設密碼為 'admin123'
        # 從 MongoDB 中檢索數據
        cursor = mycollection.find({})
        df = pd.DataFrame(list(cursor))
        df['_id'] = df['_id'].astype(str)  # 將 ObjectId 轉換為字符串

        if df.empty:
            st.warning("目前沒有遺失物記錄")
        else:
            # 顯示資料，每行有對應的刪除按鈕
            for index, row in df.iterrows():
                # 使用 st.columns() 來控制列的寬度，確保每列顯示更整潔
                col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(
                    [1.5, 1.5, 1.5, 1.5, 1.5, 2, 1.5, 2, 1])

                col1.write(row['name'])
                col2.write(row['campus'])
                col3.write(row['block'])
                col4.write(row['classroom_code'])
                col5.write(row['place'])
                # 檢查時間欄位是否存在並格式化顯示
                if isinstance(row['time'], datetime):
                    col6.write(row['time'].strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    col6.write("資料無效")
                col7.write(row['people'])
                col8.write(row['number'])

                # 刪除按鈕
                if col9.button("刪除", key=row['_id']):
                    mycollection.delete_one({"_id": ObjectId(row['_id'])})
                    st.warning(f"已刪除物品: {row['name']}")
                    st.experimental_rerun()  # 刷新頁面
    else:
        st.error("密碼錯誤，請重新嘗試")
