from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os

app = Flask(__name__)
#LineBotApi('ONToG1s1uHdXBa7I0xwDDCvzFZGZHbxSr9iEsqCZMc+7wWobVKAF1bMTgiK3fE61wh1c6sjoYlxesyC8TKTVvtVBh8XA0EW0WDI/xmOl6ggnMtjwq73+fvEagcmkA/Y7FI4EW8Qr11TDezuHEhfXfgdB04t89/1O/w1cDnyilFU=')  # <-- 請替換成你的 Channel Access Token
line_bot_api = LineBotApi(os.environ['ONToG1s1uHdXBa7I0xwDDCvzFZGZHbxSr9iEsqCZMc+7wWobVKAF1bMTgiK3fE61wh1c6sjoYlxesyC8TKTVvtVBh8XA0EW0WDI/xmOl6ggnMtjwq73+fvEagcmkA/Y7FI4EW8Qr11TDezuHEhfXfgdB04t89/1O/w1cDnyilFU=TOKEN'])
handler = WebhookHandler(os.environ['7a57233f3ad1fb9f3a7679bb09fac3c3'])


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = TextSendMessage(text=event.message.text)
    line_bot_api.reply_message(event.reply_token, message)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)