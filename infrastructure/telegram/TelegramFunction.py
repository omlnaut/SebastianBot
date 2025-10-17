import logging

from function_app import app
import azure.functions as func

from infrastructure.telegram import TelegramService
from infrastructure.telegram.AzureHelper import (
    create_telegram_output_event,
    telegram_output_binding,
)
from infrastructure.telegram.TelegramSecret import (
    TelegramChat,
    TelegramConfig,
    TelegramToken,
)
from shared.secrets import SecretKeys, get_secret


@app.route(route="test_send_telegram_message")
@telegram_output_binding()
def test_send_telegram_message(
    req: func.HttpRequest, telegramOutput: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("Python event trigger function processed a request.")
    telegramOutput.set(create_telegram_output_event(message="hello there testi"))

    return func.HttpResponse("yay")


@app.event_grid_trigger(arg_name="azeventgrid")
async def send_telegram_message(azeventgrid: func.EventGridEvent):
    logging.info("Start to send telegram message")

    msg = "from new: " + azeventgrid.get_json()["message"]
    config = get_secret(SecretKeys.TelegramSebastianToken, TelegramConfig)

    # hardcode for now
    token = config.tokens[TelegramToken.Sebastian].token
    chat_id = config.chats[TelegramChat.MainChat].id

    await TelegramService.send_telegram_message(token, chat_id, msg)

    logging.info(f"Telegram Message sent: {msg}")
