import asyncio
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils.exceptions import ChatNotFound
from aiogram.types import CallbackQuery, Message, ContentTypes

from data.config import PAYMENTS_PROVIDER_TOKEN
from filters.filters import PaidConsultationCategories, PaidConsultationRequest, ChargeConsultationRequest
from handlers.users.admin import send_message
from keyboards.inline.keyboard import (
    create_request_keys,
    sap_categories_keys,
    charge_paid_consultation_keys,
    consultation_payment_keys,
    confirm_paid_consultation_request,
    accept_consultation_request, user_requests_keys, assigned_requests_keys
)

from states.states import PaidConsultationState, AssistanceState, PayConsultationFees
from keyboards.inline.keyboard import start_keys
from loader import dp, db, bot, questions_api
from utils.misc import rate_limit
from handlers.users.ask_question import get_image_url, image_from_url_to_base64


@rate_limit(5)
@dp.callback_query_handler(text='my_requests')
async def my_requests_starter(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    user_requests = await db.get_requests_for_client(user_id)
    assigned_requests = await db.get_assigned_requests(user_id)

    if user_requests:
        if len(user_requests) > 3:
            user_requests = user_requests[-3:]
        await send_list_of_requests_to_user(user_id, user_requests)
    else:
        await bot.send_message(
            user_id,
            text='You have no paid requests.Press /start to open main menu',
            reply_markup=None
        )
    if assigned_requests:
        await send_list_of_assigned_request_to_consultant(
            user_id, assigned_requests
        )
    else:
        await bot.send_message(
            user_id, text='You have no assigned requests. Press /start to open main menu',
            reply_markup=None
        )


async def send_list_of_requests_to_user(user_id, user_requests):
    await bot.send_message(
        user_id,
        text=f"You have {len(user_requests)} open requests. If any of these requests have been resolved, "
             f"press 'Resolved' button. If you want to close the request, press 'Close request'",
        reply_markup=None
    )
    for request in user_requests:
        request_id = request['id']
        assistant_record = await db.get_assistant(request_id=request_id)
        if not assistant_record:
            assistant_contact = 'No assigned consultant'
            assistant_name = 'No assigned consultant'
        else:
            assistant_contact = assistant_record['contact']
            assistant_name = assistant_record['name']
        await bot.send_message(user_id,
                               text=f"Request {request_id}\n\n"
                                    f"Category: {request['category']}\n\n"
                                    f"Budget: {request['budget']}\n\n"
                                    f"Consultant: {assistant_name}\n\n"
                                    f"Contact: {assistant_contact}",
                               reply_markup=await user_requests_keys(request_id)
                               )
        await bot.send_chat_action(user_id, 'typing')
        await asyncio.sleep(.5)


async def send_list_of_assigned_request_to_consultant(user_id, assigned_requests):
    await bot.send_message(
        user_id,
        text=f"You have {len(assigned_requests)} assigned requests.\n"
             f"If any of these requests have been resolved, please "
             f"press 'Resolved' button under corresponding request."
    )
    for assigned_request in assigned_requests:
        request = await db.get_consultation_record(assigned_request['request'])
        request_id = assigned_request['request']
        await bot.send_message(
            user_id, text=f"Consultation request: {request_id}\n"
                          f"Requester contact:\n{request['contact']}\n",
            reply_markup=await assigned_requests_keys(request_id)
        )
        await asyncio.sleep(0.5)


@dp.callback_query_handler(Text(startswith='request_close_'))
async def close_request(call: CallbackQuery):
    await call.answer(cache_time=60)
    await call.message.edit_reply_markup()
    user_id = call.from_user.id
    request_id = int(call.data.replace('request_close_', ''))
    await db.close_request(request_id)
    await bot.send_message(user_id, f'Request {request_id} has been closed.')


@dp.callback_query_handler(Text(startswith='cons_request_resolved_'))
async def mark_request_as_resolved_by_consultant(call: CallbackQuery):
    await call.answer(cache_time=60)
    await call.message.edit_reply_markup()
    user_id = call.from_user.id
    request_id = int(call.data.replace('cons_request_resolved_', ''))
    record = await db.mark_request_as_resolved_by_consultant(request_id)
    requester_id = record['user_id']
    if not record['resolved_client']:
        await bot.send_message(
            user_id,
            text="Good job! However, requester haven't marked the request as solved yet."
                 "We're sending him notification right now. Once the request will be approved "
                 "you will receive your compensation.",
            reply_markup=await start_keys(user_id))
    else:
        await bot.send_message(
            user_id,
            text="Good job! You will receive compensation shortly"
        )
    # TODO: send notification to client, ask consultant provide bank details