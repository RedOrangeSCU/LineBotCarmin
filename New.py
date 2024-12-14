from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import pandas as pd
import jieba
from flask import Flask, request, abort

from mongodb_function import *

import json


app = Flask(__name__)
line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])
# 讀取 CSV 檔案
df = pd.read_csv('CSV_20241208_Base.csv')

# 載入字典
file_path = 'Real_userdict_1.txt'
jieba.load_userdict(file_path)
# 讀取 CSV 檔案
df = pd.read_csv('CSV_20241208_Base.csv')

# 載入字典
file_path2 = 'Real_userdict_2.txt'

# 建立一個字典來儲存詞彙和權重
dictionary_words = {}  
with open(file_path2, 'r', encoding='utf-8') as f:
    for line in f:
        word, weight = line.strip().split(' ')
        dictionary_words[word] = int(weight)  # 將權重轉換為整數

# 載入 JSON 檔案
with open('LMStudio_V1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取問答配對
qa_pairs = []
for message in data['messages']:
    if len(message['versions']) > 0 and message['versions'][0]['role'] == 'user':
        question = message['versions'][0]['content'][0]['text']
    if len(message['versions']) > 1 and len(message['versions'][1]['content']) > 0:
        answer = message['versions'][1]['content'][0]['text']
    else:
    # 處理 message['versions'][1]['content'] 列表為空的情況
        answer = "找不到答案"  # 或其他預設回覆
    qa_pairs.append((question, answer))

# 建立問答知識庫
qa_dict = {question: answer for question, answer in qa_pairs}


# 建立一個字典，儲存使用者和提問次數
user_questions = {}

# 設定預設詞彙列表
special_words = { "早安", "晚安", "午安", "有問題", "嗨", "你好", "您好", "HI", "hi", "Hello"}

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    write_one_data(eval(body.replace('false','False')))

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# 建立一個函式來處理特殊詞彙
def handle_special_words(sentence):
    for word in special_words:
        if word in sentence: # 遇到特殊詞彙就 return None
            return None  
    return 0
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        user_id = event.source.user_id
        questionSentance = event.message.text  # 使用者啟動對話之內容
        if '@載入' in questionSentance:
            LoadCSV()
            message = TextSendMessage(text=f'載入成功')
            
            line_bot_api.reply_message(event.reply_token,message)
            return
        elif '@讀取' in questionSentance:
            datas = read_many_datas()
            datas_len = len(datas)
            message = TextSendMessage(text=f'資料數量，一共{datas_len}條')
            line_bot_api.reply_message(event.reply_token, message)
        elif '@查詢' in questionSentance:
            datas = col_find('events')
            message = TextSendMessage(text=str(datas))
            line_bot_api.reply_message(event.reply_token, message)
        elif '@對話紀錄' in questionSentance:
            datas = read_chat_records()
            print(type(datas))
            n = 0
            text_list = []
            for data in datas:
                if '@' in data:
                     continue
                else:
                     text_list.append(data)
                     n+=1
            data_text = '\n'.join(text_list)
            message = TextSendMessage(text=data_text[:5000])
            line_bot_api.reply_message(event.reply_token, message)
        elif '@刪除' in questionSentance:
            text = delete_all_data()
            message = TextSendMessage(text=text)
            line_bot_api.reply_message(event.reply_token, message)

    #======MongoDB操作範例======
        result = handle_special_words(questionSentance)
        if result is None:    
            noneMessage ='您好！請問您想了解哪方面的資訊呢？'
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=noneMessage))

        else:
                        # 清空 Jieba 預設詞典
            jieba.dt.FREQ = {}  
            
            # 載入自訂詞典
            jieba.load_userdict(file_path)
            
            # 使用搜索引擎模式切分
            words = jieba.cut_for_search(questionSentance)            

            # 篩選出字典中存在的詞彙
            matched_words = [word for word in words if word in dictionary_words]
            
            # 根據權重排序 matched_words (權重高的詞彙排前面)
            matched_words.sort(key=lambda word: dictionary_words[word], reverse=True)

           
            #根據user 問題,排除special_words後,再將問題split 後再去資料集裡面尋找資料
            dictWords = ("|".join(matched_words))  # 輸出匹配的詞彙
            if matched_words:
                confirmMessate = '原來你對' + matched_words[0] + "有興趣呀?"
                splitWords = dictWords.split('|')
                # 使用者傳送的訊息
                user_message = event
                # 迭代 splitWords 中的每個詞彙
                matched_rows = pd.DataFrame()  # 建立一個空的 DataFrame 來儲存所有匹配的列
                for word in splitWords:# 迭代 DataFrame 的每一欄
                    for col in df.columns:                    # 在當前欄位中搜尋符合的資料
                        matched_row = df[df[col].astype(str).str.contains(word)]
                        if not matched_row.empty:
                            matched_rows = pd.concat([matched_rows, matched_row])
                            break  # 找到匹配的資料後跳出內層迴圈

                if not matched_rows.empty:
                    # 將所有匹配的列整理成字串
                    feedback_str = ""
                    for idx, row in matched_rows.iterrows():
                        if feedback_str in f"{row['Bank']}{row['CreditCard']}":
                            feedback_str = f"{row['Bank']}{row['CreditCard']}擁有 {row['discount']} "
                            if not pd.isna(row['discountInfo']):
                                feedback_str+=f"，{row['discountInfo']}"
                            feedback_str+=f"\n"
                        else:
                            if "還有還有" in feedback_str:
                                if "以及，" in feedback_str:
                                    feedback_str += f"最重要的{row['discount']}在等著你"

                                else:
                                    feedback_str += f"以及，{row['discount']}"                                    
                            else:
                                feedback_str += f"還有還有，{row['discount']}"                         

                            if not pd.isna(row['discountInfo']):
                                feedback_str+=f"，{row['discountInfo']}"
                            feedback_str+=f"\n"
                            if "最重要的" in feedback_str:
                                break
                    line_bot_api.reply_message(event.reply_token,[confirmMessate,feedback_str,f"\n希望以上資訊有滿足您的需求！"])
                else:
                    line_bot_api.reply_message(event.reply_token,[confirmMessate, "抱歉，找不到符合您需求的信用卡"])
            else:    # 處理 matched_words 為空的情況，例如：
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text="抱歉，我不明白您的意思"))
               


    except Exception as e:
        print(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='發生錯誤')
        )

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
