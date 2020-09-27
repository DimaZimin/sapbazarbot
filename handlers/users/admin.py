import asyncio

from aiogram.dispatcher import FSMContext
import logging
from keyboards.inline.keyboard import admin_start_keys, remove_categories_keys, remove_location_keys, start_keys
from loader import dp, bot, db
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from middlewares.middleware import Admin
from filters.filters import IsCategory, IsLocation


@dp.callback_query_handler(text='ADMIN')
async def admin_start(call: CallbackQuery):
    await call.answer(cache_time=60)
    chat_id = call.message.chat.id
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=chat_id, text='Chose func', reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_new_category')
async def admin_add_category(call: CallbackQuery):
    await call.answer(cache_time=60)
    chat_id = call.message.chat.id
    await Admin.new_category.set()
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=chat_id,
                           text='Type category name')

@dp.message_handler(state=Admin.new_category)
async def render_category(message: Message, state: FSMContext):
    user_id = message.chat.id
    category = message.text
    await db.add_category(category)
    await state.finish()
    await bot.send_message(chat_id=user_id,
                           text=f'{category} category has been added!',
                           reply_markup=admin_start_keys())

@dp.callback_query_handler(text='admin_remove_category')
async def delete_category(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text='Chose category which will be removed',
                           reply_markup=await remove_categories_keys())


@dp.callback_query_handler(IsCategory())
async def admin_remove_category(call: CallbackQuery):
    await call.answer(cache_time=10)
    user_id = call.message.chat.id
    category = call.data[1:]
    await db.remove_category(category)
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text=f"{category} has been removed",
                           reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_go_back')
async def admin_back_to_main(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id, text='Main menu',
                           reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_new_location')
async def admin_add_location(call: CallbackQuery):
    await call.answer(cache_time=60)
    chat_id = call.message.chat.id
    await Admin.new_location.set()
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=chat_id,
                           text='Type location name')


@dp.message_handler(state=Admin.new_location)
async def render_location(message: Message, state: FSMContext):
    user_id = message.chat.id
    location = message.text
    await db.add_location(location)
    await state.finish()
    await bot.send_message(chat_id=user_id,
                           text=f'{location} category has been added!',
                           reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_remove_location')
async def delete_location(call: CallbackQuery):
    await call.answer(cache_time=30)
    user_id = call.message.chat.id
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text='Choose a category to remove',
                           reply_markup=await remove_location_keys())


@dp.callback_query_handler(IsLocation())
async def admin_del_location(call: CallbackQuery):
    await call.answer(cache_time=30)
    user_id = call.message.chat.id
    location = call.data[1:]
    await db.remove_location(location)
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text=f"{location} has been removed",
                           reply_markup=admin_start_keys())


@dp.callback_query_handler(text='admin_statistics')
async def admin_stats(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    total_users = await db.total_users()
    subscribed_users = await db.subscribed_users()
    locations_list = [location['location_name'] for location in await db.fetch_value('location_name', 'Locations')]
    locations = "\n".join(locations_list)
    categories_list = [category['category_name'] for category in await db.fetch_value('category_name', 'Categories')]
    categories = "\n".join(categories_list)
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text=f"<b>Total users:</b> {total_users[0]['count']}\n\n"
                                f"<b>Subscribed users:</b> {subscribed_users[0]['count']}\n\n"
                                f"<b>Locations:</b>\n{locations}\n\n"
                                f"<b>Categories:</b>\n{categories}\n\n",
                           reply_markup=None, parse_mode='HTML')
    await asyncio.sleep(3)
    await bot.send_message(chat_id=user_id, text='Admin panel', reply_markup=admin_start_keys())

@dp.callback_query_handler(text='admin_main')
async def admin_stats(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id,
                           text='Main panel', reply_markup=start_keys(user_id))