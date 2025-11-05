import logging

import azure.functions as func

from cloud.helper import SecretKeys, get_secret, parse_payload
from function_app import app
from sebastian.infrastructure.telegram import service

from .config import TelegramChat, TelegramConfig, TelegramToken
from .helper import SendTelegramMessageEvent, telegram_output_binding


@app.route(route="test_send_telegram_message")
@telegram_output_binding()
def test_send_telegram_message(
    req: func.HttpRequest, telegramOutput: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("Python event trigger function processed a request.")
    telegramOutput.set(
        SendTelegramMessageEvent(message="hello there testi").to_output()
    )

    return func.HttpResponse("yay")


@app.event_grid_trigger(arg_name="azeventgrid")
async def send_telegram_message(azeventgrid: func.EventGridEvent):
    logging.info("Start to send telegram message")

    input_event = parse_payload(azeventgrid, SendTelegramMessageEvent)

    token, chat_id = _load_token_and_chat_id()

    await service.send_telegram_message(token, chat_id, input_event.message)

    logging.info(f"Telegram Message sent: {input_event.message}")


def _load_token_and_chat_id():
    config = get_secret(SecretKeys.TelegramSebastianToken, TelegramConfig)
    token = config.tokens[TelegramToken.Sebastian].token
    chat_id = config.chats[TelegramChat.MainChat].id
    return token, chat_id
