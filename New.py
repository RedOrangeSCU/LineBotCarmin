from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import pandas as pd
import jieba
from flask import Flask, request, abort

from mongodb_function import *

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])
# 讀取 CSV 檔案
df = pd.read_csv('FormatData_1.1.csv')

# 載入字典
file_path = 'Real_userdict_1.txt'
jieba.load_userdict(file_path)

# 建立一個字典，儲存使用者和提問次數
user_questions = {}

# 設定預設詞彙列表
special_words = {"好", "早安", "晚安", "午安", "有問題", "嗨", "你好", "您好", "HI", "hi", "Hello"}

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
            jiebaQuestionList = jieba.cut(questionSentance) # text_message = ' | '.join(jiebaQuestionList)  # 將生成器轉換為字串
            jieba.initialize() # 載入 jieba 詞典        
            words = jieba.cut(questionSentance)# 斷詞
            dictionary_words = set(jieba.dt.FREQ.keys())  # 獲取jieba詞典
            with open('Real_userdict_1.txt', 'r', encoding='utf-8') as f:  # 加入Real_userdict_1.txt 中的詞彙
                for line in f:
                    word = line.strip().split(' ')[0]
                    dictionary_words.add(word)
            matched_words = [word for word in words if word in dictionary_words] # 篩選出字典中存在的詞彙
            dictWords = ("|".join(matched_words))  # 輸出匹配的詞彙
            if matched_words:
                confirmMessate = '原來你對' + matched_words[0] + "有興趣呀?"
                message1 = TextSendMessage(text=confirmMessate)
                splitWords = dictWords.split('|')
                #line_bot_api.reply_message(event.reply_token,TextSendMessage(text=confirmMessate))
                returnValues = usingNPY(questionSentance)
                #message2 = TextSendMessage(text=returnValues)
                print(returnValues)
                message2 =  TextSendMessage(text="returnValues")
                line_bot_api.reply_message(event.reply_token,[message1,message2])
                #if splitWords[0] in df.columns:
                #    matched_values = df[splitWords[0]].unique() # 取得 splitWords[0] 欄位的所有唯一值
                #    matched_rows = pd.DataFrame()  # 建立一個空的 DataFrame 來儲存所有匹配的
                #    for matched_value in matched_values:## 迭代所有 matched_values，找到符合條件的列
                #        matched_row = df[df[splitWords[0]] == matched_value]  # 找到符合條件的列
                #        matched_rows = pd.concat([matched_rows, matched_row])  # 將匹配的列加入 matched_rows      
                #    if not matched_row.empty: # 使用 dictWords 搜尋符合的資料     
                #        first_match = matched_row.iloc[0]  # 取得第一筆符合的資料
                #        feedback = first_match.to_dict()  # 將 Series 轉換為 dict
                #        feedback = {key: value for key, value in feedback.items() if pd.notna(value)}  # 篩選掉 value 為 nan 的 key-value pairs                   
                #        feedback_str = "Carmin小幫手推薦這張信用卡:\n" + "\n".join([f"{key}: {value}" for key, value in feedback.items()])  # 組合回覆訊息
                #        message2 = TextSendMessage(text=feedback_str)
                #        line_bot_api.reply_message(event.reply_token,[message1,message2])
                #    else:
                #        line_bot_api.reply_message(event.reply_token, [message1, "抱歉，找不到符合您需求的信用卡"])
                #else:
                #    # 處理 splitWords[0] 不存在的情況，例如：
                #    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，我找不到相關資訊"))
            else:
                # 處理 matched_words 為空的情況，例如：
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，我不明白您的意思"))
                


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
