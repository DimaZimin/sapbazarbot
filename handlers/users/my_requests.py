import asyncio
import logging

from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery

from handlers.users.tools import try_send_message
from keyboards.inline.keyboard import (
    user_requests_keys, assigned_requests_keys, notification_resolve_request_keys,
)

from keyboards.inline.keyboard import start_keys
from loader import dp, db, bot
from utils.misc import rate_limit


@rate_limit(5)
@dp.callback_query_handler(text='my_requests')
async def my_requests_starter(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    user_requests = await db.get_requests_for_client(user_id)
    assigned_requests = await db.get_assigned_requests(user_id)

    if user_requests:
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
            await bot.send_message(user_id,
                                   text=f"<b>Request {request_id}</b>\n\n"
                                        f"<b>Category:</b> {request['category']}\n\n"
                                        f"<b>Budget:</b> {request['budget']}\n\n"
                                        f"No consultant has been assigned yet",
                                   reply_markup=await user_requests_keys(request_id)
                                   )
            await bot.send_chat_action(user_id, 'typing')
            await asyncio.sleep(.5)
        else:
            assistant_contact = assistant_record['contact']
            assistant_name = assistant_record['name']
            assistant_chat = await bot.get_chat(assistant_record['user_id'])
            await bot.send_message(user_id,
                                   text=f"<b>Request #{request_id}</b>\n\n"
                                        f"<b>Category:</b> {request['category']}\n"
                                        f"<b>Budget:</b> {request['budget']}\n"
                                        f"<b>Consultant:</b> {assistant_name}\n"
                                        f"<b>Telegram link:</b> {assistant_chat.user_url}\n"
                                        f"<b>Contact:</b> {assistant_contact}",
                                   reply_markup=await user_requests_keys(request_id),
                                   parse_mode='HTML'
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
        await send_notification_about_completion_of_the_request(request_id, requester_id, user_id)
    else:
        await bot.send_message(
            user_id,
            text="Good job! To open main menu press /start",
        )


async def send_notification_about_completion_of_the_request(request, user_id, consultant_id):
    user = await bot.get_chat(user_id)
    consultant = await bot.get_chat(consultant_id)
    text = f"Hello, {user.first_name}. We're writing you because consultant {consultant.full_name} marked request id:{request}" \
           f" as resolved. In order to close this request successfully, please press 'Resolved' button below. If you" \
           f"have any problems or remarks, please contact our support service."
    if await try_send_message(user_id, text, reply_markup=await notification_resolve_request_keys(request)):
        logging.info(f"RESOLVED REQUEST #{request} NOTIFICATION SENT TO {user_id} SUCCESSFULLY")
    else:
        logging.info(f"UNABLE TO SEND RESOLVED REQUEST #{request} NOTIFICATION TO {user_id}")


@dp.callback_query_handler(Text(startswith='client_request_resolved_'))
async def resolve_request_by_requester(call: CallbackQuery):
    await call.answer(cache_time=60)
    user = call.from_user.id
    request_id = int(call.data.replace("client_request_resolved_", ""))
    await db.mark_request_as_resolved_by_client(request_id)
    await db.close_request(request_id)
    await bot.send_message(
        user, 'Thank you for using our service.', reply_markup=await start_keys(user)
    )

    consultant_record = await db.get_assistant(request_id)
    if consultant_record:
        consultation_request_id = consultant_record['request']
        consultant_id = consultant_record['user_id']
        consultant = await bot.get_chat(
            consultant_id
        )
        await bot.send_message(
            consultant_id,
            text=f"Good job, {consultant.first_name}! Request #{consultation_request_id} "
                 f"marked as resolved. Thank you for your assistance.",
            reply_markup=await start_keys(consultant_id)
        )