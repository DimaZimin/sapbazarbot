import asyncio
import logging

from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.exceptions import BotBlocked, UserDeactivated, RetryAfter, ChatNotFound, TelegramAPIError

from loader import dp, bot, db
from keyboards.inline.keyboard import admin_start_keys, remove_categories_keys, remove_location_keys, start_keys
from states.states import Admin, MassMessage, GroupMessage
from filters.filters import IsCategory, IsLocation


@dp.callback_query_handler(text='ADMIN')
async def admin_start(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await call.message.edit_reply_markup()
    logging.info(f"ADMIN {user_id} ENTERED THE MAIN ADMIN PANEL")
    await bot.send_message(chat_id=user_id, text=f'Hello, Admin!', reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_new_category')
async def admin_add_category(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await Admin.new_category.set()
    await call.message.edit_reply_markup()
    logging.info(f"ADMIN {user_id} IS ADDING A CATEGORY...")
    await bot.send_message(chat_id=user_id,
                           text='Type category name')


@dp.message_handler(state=Admin.new_category)
async def render_category(message: Message, state: FSMContext):
    user_id = message.chat.id
    category = message.text
    await db.add_category(category)
    await state.finish()
    logging.info(f"ADMIN {user_id} ADDED A CATEGORY...")
    await bot.send_message(chat_id=user_id,
                           text=f'{category} category has been added!',
                           reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_remove_category')
async def delete_category(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    logging.info(f"ADMIN {user_id} IS REMOVING A CATEGORY...")
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text='Choose a category to remove',
                           reply_markup=await remove_categories_keys())


@dp.callback_query_handler(IsCategory())
async def admin_remove_category(call: CallbackQuery):
    await call.answer(cache_time=10)
    user_id = call.message.chat.id
    category = call.data[1:]
    await db.remove_category(category)
    logging.info(f"ADMIN {user_id} REMOVED A CATEGORY...")
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text=f"{category} has been removed",
                           reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_go_back')
async def admin_back_to_main(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id, text='Hello, Admin!',
                           reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_new_location')
async def admin_add_location(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    logging.info(f"ADMIN {user_id} IS ADDING A LOCATION...")
    await Admin.new_location.set()
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text='Type location name')


@dp.message_handler(state=Admin.new_location)
async def render_location(message: Message, state: FSMContext):
    user_id = message.chat.id
    location = message.text
    await db.add_location(location)
    logging.info(f"ADMIN {user_id} ADDED {location} LOCATION...")
    await state.finish()
    await bot.send_message(chat_id=user_id,
                           text=f'{location} category has been added!',
                           reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_remove_location')
async def delete_location(call: CallbackQuery):
    await call.answer(cache_time=30)
    user_id = call.message.chat.id
    await call.message.edit_reply_markup()
    logging.info(f"ADMIN {user_id} IS REMOVING A LOCATION...")
    await bot.send_message(chat_id=user_id,
                           text='Choose a category to remove',
                           reply_markup=await remove_location_keys())


@dp.callback_query_handler(IsLocation())
async def admin_del_location(call: CallbackQuery):
    await call.answer(cache_time=30)
    user_id = call.message.chat.id
    location = call.data[1:]
    await db.remove_location(location)
    logging.info(f"ADMIN {user_id} REMOVED A LOCATION...")
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text=f"{location} has been removed",
                           reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_statistics')
async def admin_stats(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    logging.info(f"ADMIN {user_id} ACTIVATES STATISTICS...")
    total_users = await db.total_users()
    subscribed_users = await db.subscribed_users()
    locations_list = [location['location_name'] for location in await db.fetch_value('location_name', 'Locations')]
    locations = "\n".join(locations_list)
    categories_list = [category['category_name'] for category in await db.fetch_value('category_name', 'Categories')]
    categories = "\n".join(categories_list)
    db_status = await db.fetch_value('payable', 'settings')
    status = 'Payable' if db_status[0]['payable'] else 'Free of charge'
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text=f"<b>Total users:</b> {total_users[0]['count']}\n\n"
                                f"<b>Subscribed users:</b> {subscribed_users[0]['count']}\n\n"
                                f"<b>Locations:</b>\n{locations}\n\n"
                                f"<b>Categories:</b>\n{categories}\n\n"
                                f"<b>Job posting:</b>\n{status}\n\n",
                           reply_markup=None, parse_mode='HTML')
    await asyncio.sleep(3)
    await bot.send_message(chat_id=user_id, text='Admin panel', reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_main')
async def admin_main_menu(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    logging.info(f"ADMIN {user_id} BACK TO MAIN MENU")
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text='Main panel', reply_markup=start_keys(user_id))


@dp.callback_query_handler(text='payable')
async def make_payable(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    db_status = await db.fetch_value('payable', 'settings')
    await bot.send_chat_action(user_id, action='typing')
    if db_status[0]['payable']:
        await db.payable_post('False')
        status = 'free of charge'
    else:
        await db.payable_post('True')
        status = 'payable'
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id, text=f'Your job posting set to {status}', reply_markup=start_keys(user_id))


@dp.callback_query_handler(text='mass_message')
async def mass_message(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    logging.info(f"ADMIN {user_id} STARTS MASS MESSAGE")
    await bot.send_chat_action(user_id, action='typing')
    await MassMessage.message_processing.set()
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, text='Type a message', reply_markup=None)


async def send_message(user_id: int, text: str, disable_notification: bool = False) -> bool:
    """
    Safe messages sender
    :param user_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification)
    except BotBlocked:
        logging.error(f"Target [ID:{user_id}]: blocked by user")
    except ChatNotFound:
        logging.error(f"Target [ID:{user_id}]: invalid user ID")
    except RetryAfter as e:
        logging.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text)  # Recursive call
    except UserDeactivated:
        logging.error(f"Target [ID:{user_id}]: user is deactivated")
    except TelegramAPIError:
        logging.exception(f"Target [ID:{user_id}]: failed")
    else:
        logging.info(f"Target [ID:{user_id}]: success")
        return True
    return False


@dp.message_handler(state=MassMessage)
async def send_mass_message_to_users(message: Message, state: FSMContext):
    user_id = int(message.chat.id)
    subscribers = [user['user_id'] for user in await db.fetch_value('user_id', 'users')]
    logging.info(f"ADMIN {user_id} SENDS MESSAGE: {message.text}")
    count = 0
    try:
        for user in subscribers:
            if await send_message(int(user), text=message.text):
                count += 1
            await asyncio.sleep(.05)
    finally:
        logging.info(f"{count} messages sent")
    await state.finish()
    await bot.send_message(user_id, text='Main admin panel', reply_markup=admin_start_keys())


@dp.callback_query_handler(text='group_message')
async def group_message(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await bot.send_chat_action(user_id, action='typing')
    logging.info(f"ADMIN {user_id} MASS MESSAGE: ENTERING THE TEXT")
    await GroupMessage.message_processing.set()
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, text='Type a message', reply_markup=None)


@dp.message_handler(state=GroupMessage)
async def send_mass_message(message: Message, state: FSMContext):
    user_id = message.chat.id
    group_chat_id = '@sapbazar'
    await state.finish()
    await bot.send_message(group_chat_id, text=message.text)
    await bot.send_message(user_id, text=f"Privet {message.from_user.first_name}", reply_markup=admin_start_keys())


@dp.callback_query_handler(text='set_price')
async def set_price(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await Admin.catch_price.set()
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id, text=f'Укажи стоимость услуг в копейках (мин 5000). '
                                                 f'Используй только числа. Пример: '
                                                 f'введи 50000 и стоимость услуги будет равна 500 рублей.')


@dp.message_handler(lambda message: message.text.isdigit() and int(message.text) >= 5000, state=Admin.catch_price)
async def update_price(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await db.set_posting_fees(int(message.text))
    await state.finish()
    await bot.send_message(chat_id=user_id, text=f"Posting fee has been set to {int(message.text)/100} RUR",
                           reply_markup=admin_start_keys())


@dp.message_handler(lambda message: not message.text.isdigit() or int(message.text) < 5000, state=Admin.catch_price)
async def process_price_invalid(message: Message):
    logging.info(f"ADMIN USER: {message.from_user.id} - SETS INVALID FEES, MUST BE INTEGER")
    await message.reply('Стоимость должна быть указана в цифрах и составлять больше 5000 !')
