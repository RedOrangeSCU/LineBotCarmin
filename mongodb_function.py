import os
from pymongo import MongoClient
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders import CSVLoader

from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import MongoDBAtlasVectorSearch

import json
import numpy as np
#from sentence_transformers import SentenceTransformer  # 匯入 SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# 從環境變數中獲取 MongoDB URI
MONGODB_URI = os.environ.get('MONGODB_URI')

OPENAI_APIKEY = os.environ.get('OPENAI_APIKEY')
# 建立 MongoClient
client = MongoClient(MONGODB_URI)

# 建立数据库和 Collection，使用更有意义的名称
db = client['linebot_db']  
col = db['Info']  

#判斷key是否在指定的dictionary當中，若有則return True
def dicMemberCheck(key, dicObj):
    if key in dicObj:
        return True
    else:
        return False

def LoadCSV():
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_APIKEY)
    loader = CSVLoader(file_path="FormatData_1.1.csv")# 載入 CSV 資料到 MongoDB
    documents = loader.load()
    # 初始化 MongoDBAtlasVectorSearch
    print(f"已將 {len(documents)} 筆文件儲存!")

    vectorstore = MongoDBAtlasVectorSearch.from_documents( 
        documents, 
        embeddings, 
        index_name="card_index",
        collection=col)
    

#寫入資料data是dictionary
def write_one_data(data):
    col.insert_one(data)

#寫入多筆資料，data是一個由dictionary組成的list
def write_many_datas(data):
    col.insert_many(data)

#讀取所有LINE的webhook event紀錄資料
def read_many_datas():
    data_list = []
    for data in col.find():
        data_list.append(str(data))

    print(data_list)
    return data_list

#讀取LINE的對話紀錄資料
def read_chat_records():
    data_list = []
    for data in col.find():
        if dicMemberCheck('events',data):
            if dicMemberCheck('message',data['events'][0]):
                if dicMemberCheck('text',data['events'][0]['message']):
                    print(data['events'][0]['message']['text'])
                    data_list.append(data['events'][0]['message']['text'])
        else:
            print('非LINE訊息',data)

    print(data_list)
    return data_list

#刪除所有資料
def delete_all_data():
    data_list = []
    for x in col.find():
        data_list.append(x)   

    datas_len = len(data_list)

    col.delete_many({})

    if len(data_list)!=0:
        return f"資料刪除完畢，共{datas_len}筆"
    else:
        return "資料刪除出錯"

#找到最新的一筆資料
def col_find(key):
    for data in col.find({}).sort('_id',-1):
        if dicMemberCheck(key,data):
            data = data[key]
            break
    print(data)
    return data

#def usingNPY(question):
#    with open('qa_pairs.json', 'r', encoding='utf-8') as f:     # 載入 JSON 檔案
#        data = json.load(f)     
#    embeddings = np.load('embeddings.npy') # 載入 Embedding
#    texts = [f"{item['question']} - {item['answer']}" for item in data] # 假設您的 JSON 檔案包含 "text" 鍵 或者，組合多個鍵的值
#    
#    llm = OpenAI(temperature=0) # 初始化 LLM
#    query = question # 使用者查詢
#    # 初始化 Sentence-BERT 模型
#    model = SentenceTransformer('all-mpnet-base-v2')  # 初始化模型
#    # 嵌入查詢 (如果需要重新計算 Embedding)
#    query_embedding = model.encode(query)
#    #計算相似度
#    similarities = cosine_similarity(query_embedding.reshape(1, -1), embeddings)
#    # 找到最相似的項目
#    most_similar_index = np.argmax(similarities)
#    # 獲取最相似項目的上下文資訊
#    context = texts[most_similar_index]
#    # 將上下文資訊和查詢一起傳遞給 LLM
#    prompt = f"根據以下資訊回答問題：\n\n{context}\n\n問題：{query}"
#    answer = llm(prompt)
#    return answer


#這個函式會從一個問題列表中找到與使用者訊息最相似的問題。
def find_most_similar_question(user_message, questions):
 
  # 使用 TF-IDF 將文字轉換為向量
  vectorizer = TfidfVectorizer()
  print(questions)
  tfidf_matrix = vectorizer.fit_transform([user_message] + list(questions.keys()))

  # 計算餘弦相似度
  similarities = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:])

  # 找到最相似的問題
  most_similar_index = similarities.argmax()
  most_similar_question = questions[most_similar_index]

  return most_similar_question

if __name__ == '__main__':
    print(read_many_datas())
