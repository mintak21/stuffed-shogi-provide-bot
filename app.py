import json
import logging
import os
from random import randint

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
)


def _read_json_master(path='static/pseudo_db_master.json'):
    """マスタとなるJSONファイルを読み込む
    Args:
        path (str, optional): 対象ファイルパス。 Defaults to 'static/pseudo_db_master.json'.

    Returns:
        dict: 辞書形式マスタ
    """
    with open(path, mode='r', encoding='utf-8') as file:
        prof = file.read()
    result = json.loads(prof)
    app.logger.debug('master loaded')
    return result


# グローバル変数群
MIN = 7
MAX = 17
app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
handler = WebhookHandler(os.getenv('SSP_CHANNEL_SECRET'))
line_bot_api = LineBotApi(os.getenv('SSP_CHANNEL_ACCESS_TOKEN'))
stuffed_shogi_master = _read_json_master()
answer_queue = list()


@app.route('/', methods=['GET'])
def health():
    return 'Health Check OK'


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.debug("Request body -> " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error(
            "Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """メッセージハンドリング部分
    """
    req_text = event.message.text
    res_messages = list()
    if req_text == 'つかいかた' or req_text == '使い方':
        res_messages.append(TextSendMessage(text=_how_to_use_message()))
    elif req_text == 'リセット':
        _reset_master()
        app.logger.warn('stuffed-shogi urls have resetted.')
        res_messages.append(TextSendMessage(text='問題がリセットされました。'))
    elif req_text == 'ストック':
        res_messages.append(TextSendMessage(text=_stock_message()))
    elif req_text == 'かいとう' or req_text == '解答':
        if len(answer_queue) <= 0:
            res_messages.append(TextSendMessage(text='未解答の問題はありません。'))
        else:
            print('now answer queue->' + str(answer_queue))
            for answer in answer_queue:
                res_messages.append(TextSendMessage(text=answer))
            answer_queue.clear()
    else:
        try:
            # 画像イメージ処理
            res_messages.append(_stuffed_shogi_image_message(req_text))
        except ValueError:
            return  # Do Nothing

    # Response返却
    line_bot_api.reply_message(
        reply_token=event.reply_token,
        messages=res_messages)


def _reset_master():
    """Globalで持っているマスタキャッシュを読み直し、解答対象リストをリセットする。
    """
    global stuffed_shogi_master
    stuffed_shogi_master = _read_json_master()
    answer_queue.clear()


def _stuffed_shogi_image_message(req_text):
    """キャッシュしている辞書からreq_text手の画像メッセージを取得

    Args:
        req_text (str): リクエストメッセージ

    Returns:
        Message: 取得できた場合 -> ImageMessage,\
                 req_textが整数以外 -> 整数入力を促すTextMessage,\
                 対象手数の問題がなくなった -> 別の手数を促すTextMessage
    """
    def _check_range(num):
        return num % 2 != 0 and MIN <= num <= MAX

    if not _check_range(int(req_text)):
        return TextSendMessage(
            text='{min}から{max}までの整数を入力すると、詰将棋の図が出てくるよ。'.format(
                min=MIN, max=MAX))

    selected_master = _popMasterRandomly(req_text)
    if selected_master is not None:
        image_url = selected_master.get('question_image')
        answer_queue.append(selected_master.get('answer'))
        return ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url)
    else:
        return TextSendMessage(
            text='{key}手の詰将棋ストックがありません。ほかの手数を入力してください。'.format(
                key=req_text))


def _popMasterRandomly(key):
    """key手のマスタデータをランダムに1つ取得する。
    Args:
        key (str): 手数の部分
    Returns:
        dict: ランダムに取り出されたマスタ
              ただし、用意されていない手数や当該手数のストックがなくなった場合はNone。
    """
    target_master = stuffed_shogi_master.get(key)
    if target_master is None or len(target_master) <= 0:
        return None
    poped_result = target_master.pop(randint(0, len(target_master) - 1))
    return poped_result


def _stock_message():
    stock_list = [
        '{key}手：残り{num}問'.format(
            key=key, num=len(
                stuffed_shogi_master.get(key))) for key in stuffed_shogi_master.keys()]
    return os.linesep.join(stock_list)


def _how_to_use_message():
    return """以下のコマンドを利用できます。
「7~17」：指定手数の詰将棋をランダム表示
「かいとう」：一度選択した詰将棋の解答を表示
「リセット」：状態をもとに戻す
「ストック」：残りの問題数を表示"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
