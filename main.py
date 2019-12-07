import configparser
import os
from enum import Enum
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


@classmethod
def read_config(file='config/config.ini', section='DEFAULT'):
    """config.iniを読んで、Number:listの辞書にする
    Args:
        file (str, optional): 指定ファイル. Defaults to 'config/config.ini'.
        section (str, optional): 指定セクション. Defaults to 'DEFAULT'.
    Returns:
        dict: 手数とURLリストの辞書
    """
    parser = configparser.ConfigParser()
    items = parser.read(file, encoding='utf-8')[section]
    return {Number.value_of(item[0]): item[1].split(',')
            for item in items.items()}


# グローバル変数群
app = Flask(__name__)
handler = WebhookHandler(os.getenv('SSP_CHANNEL_SECRET'))
line_bot_api = LineBotApi(os.getenv('SSP_CHANNEL_ACCESS_TOKEN'))
stuffed_shogi_urls = read_config()


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body -> " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error(
            "Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


def _popRandomly(key):
    """key手の詰将棋URLをランダムに1つ取得する。
    Args:
        key (Number): 手数の部分
    Returns:
        str: ランダムに取り出された画像URL
             ただし、用意されていない手数や当該手数のストックがなくなった場合はNone。
    """
    target_urls = stuffed_shogi_urls.get(key)
    if key not in target_urls or len(target_urls) <= 0:
        return None
    return target_urls.pop(randint(len(target_urls)))


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    try:
        key = Number.value_of(int(event.message.text))
        image_url = _popRandomly(key)
        if image_url is not None:
            # ストックあり
            line_bot_api.reply_message(
                reply_token=event.reply_token,
                messages=ImageSendMessage(
                    original_content_url=_popRandomly(key)))
        else:
            # ストックなし or 当該手数準備なし
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text='{key}手の詰将棋ストックがありません。ほかの手数を入力してください。'.format(key=key)))
    except ValueError:
        # 数値以外
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text='{min}から{max}までの整数を入力すると、詰将棋の図が出てくるよ。'))


class Number(Enum):
    """詰将棋の手数
    """
    SEVEN = 'seven'
    NINE = 'nine'
    ELEVEN = 'eleven'
    THIRTEEN = 'thirteen'
    FIFTEEN = 'fifteen'
    NINETEEN = 'nineteen'

    def __init__(self, str_number):
        self.__number = str_number

    @property
    def number(self):
        return self.__number

    @classmethod
    def value_of(cls, str_number):
        """引数に対応するNUMBER返却する。
        Parameters
        --------------------------
        number : str
            数字(文字)
        Returns
        --------------------------
        CardNumber
            数字に対応するNumber　ない場合はエラー
        """
        for e in Number:
            if e.number == str_number:
                return e
        raise ValueError()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
