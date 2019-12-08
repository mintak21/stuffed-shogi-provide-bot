import configparser
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

from enums import Number


def read_config(file='config/config.ini', section='DEFAULT'):
    """config.iniを読んで、Number:listの辞書にする
    Args:
        file (str, optional): 指定ファイル. Defaults to 'config/config.ini'.
        section (str, optional): 指定セクション. Defaults to 'DEFAULT'.
    Returns:
        dict: 手数とURLリストの辞書
    """
    parser = configparser.ConfigParser()
    parser.read(file, encoding='utf-8')
    items = parser[section]
    return {Number.value_of(item[0]): item[1].split(',')
            for item in items.items()}


# グローバル変数群
MIN = 7
MAX = 19
app = Flask(__name__)
handler = WebhookHandler(os.getenv('SSP_CHANNEL_SECRET'))
line_bot_api = LineBotApi(os.getenv('SSP_CHANNEL_ACCESS_TOKEN'))
stuffed_shogi_url_cache = read_config()


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
    if req_text == 'リセット':
        _reset_urls_cache()
        app.logger.warn('stuffed-shogi urls have resetted.')
        res_messages.append(TextSendMessage(text='問題がリセットされました。'))
    elif req_text == 'ストック':
        pass
    elif req_text == 'かいとう' or req_text == '解答':
        pass
    else:
        # 画像イメージ処理
        res_messages.append(_stuffed_shogi_image_message(req_text))

    # Response返却
    line_bot_api.reply_message(
        reply_token=event.reply_token,
        messages=res_messages)


def _reset_urls_cache():
    global stuffed_shogi_url_cache
    stuffed_shogi_url_cache = read_config()


def _stuffed_shogi_image_message(req_text):
    """キャッシュしている辞書からreq_text手の画像メッセージを取得

    Args:
        req_text (str): リクエストメッセージ

    Returns:
        Message: 取得できた場合 -> ImageMessage,\
                 req_textが整数以外 -> 整数入力を促すTextMessage,\
                 対象手数の問題がなくなった -> 別の手数を促すTextMessage
    """
    try:
        key = Number.value_of(int(req_text))
        image_url = _popRandomly(key)
        if image_url is not None:
            return ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url)
        else:
            return TextSendMessage(
                text='{key}手の詰将棋ストックがありません。ほかの手数を入力してください。'.format(
                    key=key))
    except ValueError:
        return TextSendMessage(
            text='{min}から{max}までの整数を入力すると、詰将棋の図が出てくるよ。'.format(
                min=MIN, max=MAX))


def _popRandomly(key):
    """key手の詰将棋URLをランダムに1つ取得する。
    Args:
        key (Number): 手数の部分
    Returns:
        str: ランダムに取り出された画像URL
             ただし、用意されていない手数や当該手数のストックがなくなった場合はNone。
    """
    target_urls = stuffed_shogi_url_cache.get(key)
    if target_urls is None or len(target_urls) <= 0:
        return None
    return target_urls.pop(randint(0, len(target_urls) - 1))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
