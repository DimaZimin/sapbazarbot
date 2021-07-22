import asyncio
import logging
import string
import random

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, RetryAfter, UserDeactivated, TelegramAPIError

from loader import bot


async def try_send_message(
        user_id: int,
        text: str,
        disable_notification: bool = False,
        reply_markup: InlineKeyboardMarkup = None
) -> bool:
    """
    Safe messages sender
    :param user_id:
    :param text:
    :param disable_notification:
    :param reply_markup:
    :return:
    """
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification, reply_markup=reply_markup)
    except BotBlocked:
        logging.error(f"Target [ID:{user_id}]: blocked by user")
    except ChatNotFound:
        logging.error(f"Target [ID:{user_id}]: invalid user ID")
    except RetryAfter as e:
        logging.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await try_send_message(user_id, text)  # Recursive call
    except UserDeactivated:
        logging.error(f"Target [ID:{user_id}]: user is deactivated")
    except TelegramAPIError:
        logging.exception(f"Target [ID:{user_id}]: failed")
    else:
        logging.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def transform_fee_amount(amount) -> int:
    if int(amount) < 100:
        return 100
    if int(amount) > 1000:
        return 1000


def project_id_generator():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(16))
