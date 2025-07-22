import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from dateutil.relativedelta import relativedelta
from math import ceil

from telegram import Update, Message, MessageEntity
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from mobile_de import AutoMobile, URLParseFailed
from euro_rate import EuroRate

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
        fee = calculate_the_fee(automobile)
        euro_rate = EuroRate()
        fee_in_rub = ceil(euro_rate.euro_to_rub(fee["chosen"]) * 100) / 100
        await context.bot.send_message(chat_id=message.chat_id,
                                       text=f"Таможенная пошлина для этой машины составит {fee_in_rub} ₽")
    except URLParseFailed:
        await update.message.reply_text("Ссылка ведет на какую-то другую страницу. Отправьте корректную ссылку")


def urls(message: Message) -> list[str]:
    return list([message.text[ent.offset:ent.offset + ent.length] for ent in
                 filter(lambda ent: ent.type == MessageEntity.URL, message.entities)])


def age(auto: AutoMobile) -> relativedelta:
    reg_date = auto.first_registration_date()
    return relativedelta(datetime.strptime(reg_date, "%m/%Y"), datetime.today())


# TODO: refactoring
def calculate_the_fee(auto: AutoMobile) -> dict[str, float]:
    cars_age = age(auto)
    cars_price = float_price(auto.brutto_price())
    cars_engine_capacity = auto.engine_capacity_cm3()
    if cars_age.years < 3:
        percentage_fee = calc_fee_car_less_3_years(cars_price, cars_engine_capacity)
    elif cars_age.years < 5:
        percentage_fee = calc_fee_car_less_5_years(cars_engine_capacity)
    else:
        percentage_fee = calc_fee_car_other(cars_engine_capacity)
    return percentage_fee


def calc_fee_car_less_3_years(price: float, capacity: int) -> dict[str, float]:
    if price <= 8500:
        rate = 0.54
        at_least = 3.5  # euro for 1 cm^3
    elif price <= 16700:
        rate = 0.48
        at_least = 5.5
    elif price <= 84500:
        rate = 0.48
        at_least = 7.5
    elif price <= 169000:
        rate = 0.48
        at_least = 15
    else:
        rate = 0.48
        at_least = 20
    percentage_fee = {
        "by_percentage": price * rate,
        "by_engine_capacity": capacity * at_least,
        "chosen": max(price * rate, capacity * at_least)
    }
    return percentage_fee

def calc_fee_car_less_5_years(capacity: int) -> dict[str, float]:
    if capacity <= 1000:
        at_least = 1.5
    elif capacity <= 1500:
        at_least = 1.7
    elif capacity <= 1800:
        at_least = 2.5
    elif capacity <= 2300:
        at_least = 2.7
    elif capacity <= 3000:
        at_least = 3.
    else:
        at_least = 3.6
    percentage_fee = {
        "by_percentage": 0,
        "by_engine_capacity": capacity * at_least,
        "chosen": capacity * at_least,
    }
    return percentage_fee

def calc_fee_car_other(capacity: int) -> dict[str, float]:
    if capacity <= 1000:
        at_least = 3.
    elif capacity <= 1500:
        at_least = 3.2
    elif capacity <= 1800:
        at_least = 3.5
    elif capacity <= 2300:
        at_least = 4.8
    elif capacity <= 3000:
        at_least = 5.
    else:
        at_least = 5.7
    percentage_fee = {
        "by_percentage": 0,
        "by_engine_capacity": capacity * at_least,
        "chosen": capacity * at_least,
    }
    return percentage_fee

def float_price(price: str) -> float:
    return float(price.split(' ')[0].replace('.', '').replace(',', '.'))


def main() -> None:
    application = Application.builder().token(os.getenv("TG_BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(~filters.COMMAND & filters.TEXT & filters.Entity("url"), url_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
