import asyncio
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
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
    accept_consultation_request
)

from states.states import PaidConsultationState, AssistanceState, PayConsultationFees
from keyboards.inline.keyboard import start_keys
from loader import dp, db, bot, questions_api
from utils.misc import rate_limit
from handlers.users.ask_question import get_image_url, image_from_url_to_base64


@rate_limit(5)
@dp.callback_query_handler(text='create_request')
async def create_request(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    logging.info(f'USER ID: {user_id} - CREATE REQUEST STEP')
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, text='Select request', reply_markup=await create_request_keys())


@rate_limit(5)
@dp.callback_query_handler(text='paid_consultation')
async def start_paid_consultation_request(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    user_requests = await db.get_requests_for_client(user_id)
    if len(user_requests) < 3:
        logging.info(f'PAID CONSULTATION MODE - USER ID: {user_id} - START')
        await PaidConsultationState.budget_state.set()
        await call.message.edit_reply_markup()
        await bot.send_message(user_id,
                               text='Please evaluate your budget in USD$. '
                                    'Type a number without spaces or other characters.',
                               reply_markup=None)
    else:
        await call.message.edit_reply_markup()
        await bot.send_message(user_id,
                               text="You already have opened 3 requests. Please close at least one in order to create"
                                    " a new request. To close request select 'My requests', and press 'Close request'"
                                    " under selected request.",
                               reply_markup=await create_request_keys()
                               )


@rate_limit(5)
@dp.callback_query_handler(text='back_to_menu')
async def back_to_main_menu(call: CallbackQuery):
    await call.answer(cache_time=60)
    await call.message.edit_reply_markup()
    await bot.send_message(call.from_user.id, 'Main menu', reply_markup=await start_keys(call.from_user.id))


@dp.message_handler(lambda message: message.text.isdigit(), state=PaidConsultationState.budget_state)
async def set_budget_state(message: Message, state: FSMContext):
    user_id = message.chat.id
    budget = int(message.text)
    logging.info(f'USER ID {user_id} RESPONDS TO QUESTION')
    async with state.proxy() as data:
        data['budget'] = budget
    await PaidConsultationState.category_state.set()
    await bot.send_message(user_id, text=f'Your budget is {budget}. Now, please choose a category from the below list.',
                           reply_markup=await sap_categories_keys('CO'))


@dp.message_handler(lambda message: not message.text.isdigit(), state=PaidConsultationState.budget_state)
async def check_budget_is_number(message: Message):
    user_id = message.from_user.id
    await bot.send_message(user_id, text="Please, type a number")


@dp.callback_query_handler(PaidConsultationCategories(), state=PaidConsultationState.category_state)
async def process_category_state(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    category = call.data[2:]
    user_id = call.from_user.id
    await call.message.edit_reply_markup()
    async with state.proxy() as data:
        data['category'] = category
    await PaidConsultationState.content_state.set()
    await bot.send_message(user_id, text="Please type question content")


@rate_limit(5)
@dp.message_handler(state=PaidConsultationState.content_state)
async def process_content_state(message: Message, state: FSMContext):
    user_id = message.chat.id
    question_content = message.text
    logging.info(f'PAID CONSULTATION MODE: USER ID {user_id} PROVIDED QUESTION CONTENT')
    async with state.proxy() as data:
        data['content'] = question_content
    await PaidConsultationState.picture_state.set()
    await bot.send_message(user_id,
                           text="Now, you can attach a screenshot if needed. "
                                "If no need, type any text to proceed.",
                           reply_markup=None)


@rate_limit(5)
@dp.message_handler(state=PaidConsultationState.picture_state,
                    content_types=[types.ContentType.PHOTO, types.ContentType.TEXT])
async def process_picture_state(message: Message, state: FSMContext):
    user_id = message.chat.id
    try:
        image_id = message.photo[-1].file_id
    except IndexError:
        image_id = None
    if image_id:
        image_url = await get_image_url(image_id)
        image_base_64 = await image_from_url_to_base64(image_url)
        saved_image_link = await questions_api.get_image_internal_link(image_base_64)
        async with state.proxy() as data:
            data["image_url"] = saved_image_link
    else:
        async with state.proxy() as data:
            data["image_url"] = None
    await PaidConsultationState.contact_state.set()

    await bot.send_chat_action(user_id, action='typing')
    await bot.send_message(user_id, 'Please, provide your contact details such as '
                                    'e-mail address and/or mobile number')


@rate_limit(5)
@dp.message_handler(state=PaidConsultationState.contact_state)
async def process_contact_details_state(message: Message, state: FSMContext):
    user_id = message.chat.id
    contact_details = message.text
    async with state.proxy() as data:
        data['contact_details'] = contact_details
    await PaidConsultationState.review.set()
    await bot.send_message(user_id, text='Review your request', reply_markup=None)
    await bot.send_message(user_id,
                           text=f"<b>Your budget:</b> {data['budget']}$\n"
                                f"<b>Category:</b> {data['category']}\n"
                                f"<b>Problem:</b> {data['content']}\n"
                                f"<b>Attached image: </b> {data['image_url']}\n"
                                f"<b>Contact details:</b> {data['contact_details']}\n",
                           parse_mode='HTML', reply_markup=await confirm_paid_consultation_request())


@rate_limit(5)
@dp.callback_query_handler(state=PaidConsultationState.review, text='consultation_request_confirmed')
async def approve_consultation_request(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=200)
    user_id = call.from_user.id
    data = await state.get_data()
    await state.finish()
    username = call.from_user.username
    contact = f'Username: @{username}\n{data["contact_details"]}'
    new_request = await db.create_consultation_record(
        user_id,
        data['budget'],
        data['content'],
        data['image_url'],
        data['category'],
        contact
    )
    record_id = new_request.get('id')
    await bot.send_message(user_id,
                           text="Your request is recorded. "
                                "We will notify you when any consultant will be ready to assist.",
                           reply_markup=await start_keys(user_id))
    consultants = [
        user['user_id'] for user in await db.select_mentors_for_category(data['category']) if user['user_id'] != user_id
    ]
    if not consultants:
        consultants = [
            user['user_id'] for user in await db.select_all_mentors() if user['user_id'] != user_id
        ]

    count = 0
    try:
        for consultant in consultants:
            logging.info(f"SENDING REQUEST TO: {consultant}")
            try:
                user_chat = await bot.get_chat(chat_id=consultant)
                mentor_name = user_chat.first_name
            except ChatNotFound:
                mentor_name = 'Dear'
            text_to_send = f"Hello, {mentor_name}.\n" \
                           f"One user requested a paid consultation on " \
                           f"the problem that might be in your area of expertise.\n" \
                           f"<b>Area:</b> {data['category']}.\n" \
                           f"<b>Client's budget:</b> {data['budget']} USD\n\n" \
                           f"<b>Problem:</b>\n{data['content']}\n" \
                           f"<b>Screenshot url:</b> {data['image_url']}\n\n" \
                           f"If you know how to solve this problem and" \
                           f" are ready to assist, please press the 'Assist' button below. " \
                           f"If the client's request still relevant, you will receive his contact."

            if await send_message(
                    int(consultant),
                    text=text_to_send,
                    reply_markup=await accept_consultation_request(record_id)
            ):
                count += 1
            await asyncio.sleep(.05)
    finally:
        logging.info(f"{count} messages sent")


@dp.callback_query_handler(PaidConsultationRequest())
async def confirm_assistance(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    request_id = int(call.data.replace('confirm_paid_request_', ''))
    request = await db.get_consultation_record(request_id)
    await AssistanceState.contact_details_state.set()
    async with state.proxy() as data:
        data['request_id'] = request_id
        data['budget'] = request.get('budget')
    await bot.send_message(user_id, text=f"You have accepted the request id {request_id} "
                                         f"for paid solutions on budget {request.get('budget')}. "
                                         f"Provide your contact details, so the person who requested assistance "
                                         f"can contact you directly.")


@dp.message_handler(state=AssistanceState.contact_details_state)
async def assistant_contact_details(message: Message, state: FSMContext):
    user_id = message.from_user.id
    contact_details = message.text
    name = message.from_user.full_name
    data = await state.get_data()
    await state.finish()
    await db.assign_assistance(user_id, name, contact_details, data['request_id'])
    await bot.send_message(user_id, text='Great, I notify the requester that you are willing to consult on the problem.'
                                         'Once the requester transfer the funds to our account, you receive his/her '
                                         'contact details. After successful consultation we will transfer'
                                         'the funds to your account.')
    await notify_requester_about_paid_consultation(data['request_id'])


async def notify_requester_about_paid_consultation(request_id):
    request = await db.get_consultation_record(request_id)
    user_id = request.get('user_id')
    await bot.send_message(user_id, text='Hello! One assistant is ready to consult you on your request. If it is still '
                                         'relevant to you, please proceed with payment. Once you paid, we will share '
                                         "the assistant's contact details with you, so you can contact him directly.",
                           reply_markup=await charge_paid_consultation_keys(request_id))


@rate_limit(5)
@dp.callback_query_handler(ChargeConsultationRequest())
async def approve_paid_consultation(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=200)
    user_id = call.from_user.id
    request_id = int(call.data.replace('paid_consultation_confirm_', ''))
    request = await db.get_consultation_record(request_id)
    await PayConsultationFees.payment_state.set()
    fee_amount = int(request['budget']) * 10
    assistant = await db.get_assistant(request_id)
    await bot.get_chat(assistant['user_id'])
    async with state.proxy() as data:
        data['assistant_contact'] = assistant['contact']
        data['assistant_id'] = assistant['user_id']
        data['request_id'] = request_id
        data['requester_contact'] = request['contact']
    prices = [
        types.LabeledPrice(label='Paid consultation', amount=fee_amount)
    ]
    await bot.send_invoice(
        user_id,
        title='Invoice for paid consultation',
        description=f"Request id:\n"
                    f"{request_id}\n\n"
                    f"Your budget: {request['budget']}\n"
                    f"Category:\n"
                    f"{request['category']}\n\n"
                    f"Your contact details:\n"
                    f"{request['contact']}\n",
        provider_token=PAYMENTS_PROVIDER_TOKEN,
        currency='usd',
        prices=prices,
        start_parameter="create_job_invoice",
        need_name=True,
        need_email=True,
        need_shipping_address=False,
        is_flexible=False,
        payload='PAID_CONSULTATION',
        reply_markup=consultation_payment_keys()
    )


@dp.pre_checkout_query_handler(lambda query: True, state=PayConsultationFees.payment_state)
async def checkout(query: types.PreCheckoutQuery):
    await PayConsultationFees.checkout.set()
    logging.info(f'USER ID {query.from_user.id} checkout')
    await bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True,
                                        error_message="Something went wrong. "
                                                      "Payment was not successful. "
                                                      "Please try again.")


@rate_limit(5)
@dp.callback_query_handler(text='paid_consultation_cancel')
async def cancel_paid_consultation(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    name = call.from_user.full_name
    await state.finish()
    await bot.send_message(user_id, text=f'Hello, {name}', reply_markup=await start_keys(user_id))


@rate_limit(5)
@dp.callback_query_handler(text='cancel_consultation_payment', state=PayConsultationFees.payment_state)
async def cancel_payment_consultation(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    name = call.from_user.full_name
    await state.finish()
    await bot.send_message(user_id, text=f'Hello, {name}', reply_markup=await start_keys(user_id))


@dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT, state=PayConsultationFees.checkout)
async def got_payment(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    assistant_id = data['assistant_id']
    assistant_chat = await bot.get_chat(chat_id=assistant_id)
    assistant_contact = data['assistant_contact']
    requester_contact = data['requester_contact']
    logging.info(f'PAID QUESTION MODE: USER ID {user_id} PAID FOR QUESTION')
    await state.finish()
    await bot.send_message(user_id,
                           "Success. Your contact details have been sent to the consultant."
                           f"Assistant contact details:\n{assistant_contact}\n"
                           f"Telegram username: @{assistant_chat.username}",
                           reply_markup=await start_keys(user_id))
    await bot.send_message(assistant_id, text=f'Hi! We have received the budget from the requester. '
                                              f'Now you can contact him directly. Once the request is closed, '
                                              f'we will transfer you consultation fee.\n'
                                              f'Contact to client:\n\n{requester_contact}')
