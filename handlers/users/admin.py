from aiogram.dispatcher.filters import CommandStart
from aiogram import types
import logging
from keyboards.inline.keyboard import start_keys
from loader import dp
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

@dp.callback_query_handler(text='ADMIN')
async def admin_start(call: CallbackQuery):
    pass


@dp.callback_query_handler(text='')
async def admin_add_category(call: CallbackQuery):
    pass


@dp.callback_query_handler(text='')
async def admin_del_category(call: CallbackQuery):
    pass

@dp.callback_query_handler(text='')
async def admin_add_location(call: CallbackQuery):
    pass

@dp.callback_query_handler(text='')
async def admin_del_location(call: CallbackQuery):
    pass

@dp.callback_query_handler(text='')
async def admin_stats(call: CallbackQuery):
    pass