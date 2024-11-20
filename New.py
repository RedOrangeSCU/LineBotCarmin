from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import pandas as pd
import jieba
from flask import Flask, request, abort

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
special_words = {"信用卡", "好", "早安", "晚安", "午安", "有問題", "嗨", "你好", "您好", "HI", "hi", "Hello"}

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        user_id = event.source.user_id
        questionSentance = event.message.text  # 使用者啟動對話之內容
        # 檢查是否包含特殊詞彙
        for word in special_words:
            if word in questionSentance:
                return  # 遇到特殊詞彙就 return，使用預設回覆

        jiebaQuestionList = jieba.cut(questionSentance)
        # text_message = ' | '.join(jiebaQuestionList)  # 將生成器轉換為字串

        # 載入 jieba 詞典
        jieba.initialize()
        # 斷詞
        words = jieba.cut(questionSentance)
        dictionary_words = set(jieba.dt.FREQ.keys())  # 獲取jieba詞典

        with open('Real_userdict_1.txt', 'r', encoding='utf-8') as f:  # 加入Real_userdict_1.txt 中的詞彙
            for line in f:
                word = line.strip().split(' ')[0]
                dictionary_words.add(word)

        # 篩選出字典中存在的詞彙
        matched_words = [word for word in words if word in dictionary_words]
        dictWords = ("|".join(matched_words))  # 輸出匹配的詞彙
        confirmMessate = '原來你對' + matched_words[0] + "有興趣呀?"
        message1 = TextSendMessage(text=confirmMessate)
        splitWords = dictWords.split('|')
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=confirmMessate))
        # 取得 splitWords[0] 欄位的所有唯一值
        matched_values = df[splitWords[0]].unique()
        # print(confirmMessate)

        ## 迭代所有 matched_values，找到符合條件的列
        matched_rows = pd.DataFrame()  # 建立一個空的 DataFrame 來儲存所有匹配的列
        
        for matched_value in matched_values:
            matched_row = df[df[splitWords[0]] == matched_value]  # 找到符合條件的列
            matched_rows = pd.concat([matched_rows, matched_row])  # 將匹配的列加入 matched_rows
        
        confirmMessate = confirmMessate+':' +matched_rows[0]
       
        # 使用 dictWords 搜尋符合的資料
        if not matched_row.empty:
            # 取得第一筆符合的資料
            first_match = matched_row.iloc[0]  
            # 將 Series 轉換為 dict
            feedback = first_match.to_dict()
            # 篩選掉 value 為 nan 的 key-value pairs
            feedback = {key: value for key, value in feedback.items() if pd.notna(value)}  
            feedback_str = "Carmin小幫手推薦您您可能對這張信用卡感興趣:\n" + "\n".join([f"{key}: {value}" for key, value in feedback.items()])  # 組合回覆訊息
            message2 = TextSendMessage(text=feedback_str)  # 將 feedback_str 轉換為 TextSendMessage 物件
            line_bot_api.reply_message(event.reply_token,[message1,message2])
        else:
            line_bot_api.reply_message(event.reply_token, [message1, "抱歉，找不到符合您需求的信用卡"])


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
