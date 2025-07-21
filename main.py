import logging
import os
from dotenv import load_dotenv

from telegram import Update, Message, MessageEntity
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from mobile_de import AutoMobile, URLParseFailed

load_dotenv(verbose=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет, этот бот поможет тебе рассчитать стоимость покупки автомобиля с европейского mobile.de"
        "\n\nОтправляй ссылку на машину!",
    )


async def url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Обрабатываем вашу ссылку ⏳")
    message = update.message
    try:
        first = urls(message)[0]
        automobile = AutoMobile(first)
        await update.message.reply_text(f"Название машины: {automobile.title()}")
    except URLParseFailed:
        await update.message.reply_text("Ссылка ведет на какую-то другую страницу. Отправьте корректную ссылку")


def urls(message: Message) -> list[str]:
    return list([message.text[ent.offset:ent.offset + ent.length] for ent in
                 filter(lambda ent: ent.type == MessageEntity.URL, message.entities)])


def main() -> None:
    application = Application.builder().token(os.getenv("TG_BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(~filters.COMMAND & filters.TEXT & filters.Entity("url"), url_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
