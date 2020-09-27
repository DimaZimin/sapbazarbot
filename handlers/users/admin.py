from aiogram.dispatcher import FSMContext
import logging
from keyboards.inline.keyboard import admin_start_keys, admin_remove_categories, \
    remove_category_callback
from loader import dp, bot, db
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from middlewares.middleware import Admin
from filters.admin_filter import IsCategory

@dp.callback_query_handler(text='ADMIN')
async def admin_start(call: CallbackQuery):
    await call.answer(cache_time=60)
    chat_id = call.message.chat.id
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
                           reply_markup=await admin_remove_categories())


@dp.callback_query_handler(IsCategory())
async def admin_remove_category(call: CallbackQuery):
    await call.answer(cache_time=10)
    user_id = call.message.chat.id
    category = call.data
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


@dp.callback_query_handler(text='')
async def admin_add_location(call: CallbackQuery):
    pass

@dp.callback_query_handler(text='')
async def admin_del_location(call: CallbackQuery):
    pass

@dp.callback_query_handler(text='')
async def admin_stats(call: CallbackQuery):
    pass