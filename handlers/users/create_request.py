import asyncio
import datetime
import logging

import slugify
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, Message, ContentTypes
from aiogram.utils.parts import split_text

from data.config import PAYMENTS_PROVIDER_TOKEN
from filters.filters import PaidConsultationCategories, PaidConsultationRequest
from handlers.users.tools import try_send_message, project_id_generator
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
from loader import dp, db, bot, questions_api, mail_man
from utils.db_api.sqlmanager import MySQLDatabase
from utils.misc import rate_limit
from handlers.users.ask_question import get_image_url, image_from_url_to_base64
from .tools import transform_fee_amount


@rate_limit(5)
@dp.callback_query_handler(text='create_request')
async def create_request(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    logging.info(f'CREATE PAID REQUEST: {user_id} REQUESTS MENU')
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, text='Select request', reply_markup=await create_request_keys())


@rate_limit(5)
@dp.callback_query_handler(text='paid_consultation')
async def start_paid_consultation_request(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    logging.info(f'CREATE PAID REQUEST: {user_id} - CREATE PAID REQUEST')
    await PaidConsultationState.budget_state.set()
    await call.message.edit_reply_markup()
    await bot.send_message(user_id,
                           text='Please evaluate your budget in USD$. '
                                'Type a number without spaces or other characters.',
                           reply_markup=None)


@rate_limit(5)
@dp.callback_query_handler(text='back_to_menu')
async def back_to_main_menu(call: CallbackQuery):
    await call.answer(cache_time=60)
    await call.message.edit_reply_markup()
    logging.info(f'CREATE PAID REQUEST: {call.from_user.id} - BACK TO MAIN MENU')
    await bot.send_message(call.from_user.id, 'Main menu', reply_markup=await start_keys(call.from_user.id))


@dp.message_handler(lambda message: message.text.isdigit(), state=PaidConsultationState.budget_state)
async def set_budget_state(message: Message, state: FSMContext):
    user_id = message.chat.id
    budget = int(message.text)
    logging.info(f'CREATE PAID REQUEST: {user_id} SETS BUDGET')
    async with state.proxy() as data:
        data['budget'] = budget
    await PaidConsultationState.category_state.set()
    await bot.send_message(user_id,
                           text=f'Your budget is {budget} $. Now, please choose a category from the below list.',
                           reply_markup=await sap_categories_keys('CO'))


@dp.message_handler(lambda message: not message.text.isdigit(), state=PaidConsultationState.budget_state)
async def check_budget_is_number(message: Message):
    user_id = message.from_user.id
    logging.info(f'CREATE PAID REQUEST: {user_id} ERROR - BUDGET IS NOT A NUMBER')
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
    await bot.send_message(user_id,
                           text="Please describe your problem in the most precise and short way, so that it would be "
                                "clear for consultants.")
    logging.info(f'CREATE PAID REQUEST: {user_id} SELECTS CATEGORY')


@rate_limit(5)
@dp.message_handler(state=PaidConsultationState.content_state)
async def process_content_state(message: Message, state: FSMContext):
    user_id = message.chat.id
    question_content = message.text
    async with state.proxy() as data:
        data['content'] = question_content
    await PaidConsultationState.picture_state.set()
    await bot.send_message(user_id,
                           text="Now, you can attach a screenshot if needed. "
                                "If no need, type any text to proceed.",
                           reply_markup=None)
    logging.info(f'CREATE PAID REQUEST: USER ID {user_id} PROVIDED QUESTION CONTENT')


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
    await bot.send_message(user_id, 'Please, provide your contact details such as an '
                                    'e-mail address and/or mobile number in a free form. We will share your contact '
                                    'information with consultants, so they can reach you even though if they are '
                                    'not using Telegram. For example:\n'
                                    'E-mail: example@domain.com, mobile: +1 471 1231232, John Doe.')
    logging.info(f'CREATE PAID REQUEST: {user_id} PROVIDED PICTURE')


@rate_limit(5)
@dp.message_handler(state=PaidConsultationState.contact_state)
async def process_contact_details_state(message: Message, state: FSMContext):
    user_id = message.chat.id
    contact_details = message.text
    async with state.proxy() as data:
        data['contact_details'] = contact_details
    await PaidConsultationState.review.set()
    text_partitioned = split_text(
        f"<b>Problem:</b> {data['content']}\n"
    )
    description = f"<b>Your budget:</b> {data['budget']}$\n" \
                  f"<b>Category:</b> {data['category']}\n" \
                  f"<b>Attached image: </b> {data['image_url']}\n" \
                  f"<b>Contact details:</b> {data['contact_details']}\n"
    for part in text_partitioned:
        await bot.send_message(user_id,
                               text=part,
                               parse_mode='HTML')
        await bot.send_message(user_id,
                               text=description,
                               parse_mode='HTML')
    await bot.send_message(
        user_id,
        'Please, review your request',
        reply_markup=await confirm_paid_consultation_request()
    )
    logging.info(f'CREATE PAID REQUEST: {user_id} PROCESS CONTACT DETAILS')


@rate_limit(5)
@dp.callback_query_handler(text='consultation_request_cancel', state=PaidConsultationState.review)
async def cancel_paid_consultation(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    name = call.from_user.full_name
    await state.finish()
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, text=f'{name}, consultation request aborted',
                           reply_markup=await start_keys(user_id))
    logging.info(f'CREATE PAID REQUEST: {user_id} CANCELS PAID REQUEST')


@rate_limit(5)
@dp.callback_query_handler(text="reject_paid_consultation")
async def reject_paid_consultation_by_consultant(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, text='Paid consultation rejected', reply_markup=await start_keys(user_id))
    logging.info(f'CREATE PAID REQUEST: {user_id} CONSULTANT REJECT PAID REQUEST')


@rate_limit(5)
@dp.callback_query_handler(state=PaidConsultationState.review, text='consultation_request_confirmed')
async def approve_consultation_request(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=200)
    await call.message.edit_reply_markup()
    user_id = call.from_user.id
    data = await state.get_data()
    await state.finish()
    username = call.from_user.username
    contact = f'@{username if username else ""}\n{data["contact_details"]}'
    new_request = await db.create_consultation_record(
        user_id,
        data['budget'],
        data['content'],
        data['image_url'],
        data['category'],
        contact
    )
    record_id = new_request.get('id')
    await bot.send_message(
        user_id,
        text=f"Your request #{record_id} is recorded. "
             "We will notify you when any consultant will be ready to assist.",
        reply_markup=await start_keys(user_id))
    consultants = [
        user['user_id'] for user in await db.select_mentors_for_category(data['category']) if user['user_id'] != user_id
    ]
    if not consultants:
        consultants = [
            user['user_id'] for user in await db.select_all_mentors() if user['user_id'] != user_id
        ]
    await send_request_to_consultants(consultants, data, record_id)
    description = f"{data['content']}\n\n<img src=\"{data['image_url']}\" alt=\"screenshot\">" \
        if data['image_url'] else data['content']
    url = await create_project_in_db(record_id, data['budget'], data['category'], description)
    if url:
        await send_mass_mail_to_category_users(category=data['category'], request_id=record_id, url=url)
    logging.info(f'CREATE PAID REQUEST: {user_id} REQUEST APPROVED')


async def send_mass_mail_to_category_users(category, request_id, url):
    logging.info(f'SENDING MASS MAIL URL {url}')
    try:
        with MySQLDatabase() as mysqldb:
            users = mysqldb.select_category_users(category)
            logging.info(f'USERS RETRIEVED: {users}')
    except Exception as e:
        logging.error(e)
        return None
    if users:
        mail_man.send_mass_mail(
            receivers=users, category=category, request_id=request_id, url=url
        )


async def create_project_in_db(request_id, budget, category, description):
    project_id = project_id_generator()
    title = f'SAP assistance request {request_id} in {category}'
    try:
        with MySQLDatabase() as sqldb:
            sqldb.insert(
                'projects',
                projectid=project_id,
                userid='6655',
                title=title,
                slug=slugify.slugify(title),
                budget=budget,
                category=category,
                description=description,
                closed=0,
                complete=0,
                date_added=datetime.datetime.today().date()
            )
        return mail_man.create_url_for_project(project_id=project_id, slug=slugify.slugify(title))
    except Exception as e:
        logging.error(f'INSERT ERROR: {e}')


async def send_request_to_consultants(consultants, data, record_id):
    count = 0
    try:
        for consultant in consultants:
            logging.info(f"SENDING REQUEST TO: {consultant}")
            full_text = f"<b>Problem:</b>\n{data['content']}\n" \
                        f"<b>Screenshot url:</b> {data['image_url']}\n\n" \
                        f"If you know how to solve this problem and" \
                        f" are ready to assist, please press the 'Assist' button below. " \
                        f"If the client's request still relevant, you will receive his contact."
            text_to_send = split_text(full_text)
            description = f"Dear consultant.\n" \
                          f"One user requested a paid consultation on " \
                          f"the problem that might be in your area of expertise.\n" \
                          f"<b>Area:</b> {data['category']}.\n" \
                          f"<b>Client's budget:</b> {data['budget']} USD\n\n"

            if await try_send_message(int(consultant), text=description):
                for text in text_to_send:
                    await bot.send_message(int(consultant), text=text)
                    await bot.send_message(int(consultant),
                                           text="If you are ready to assist, press the 'Assist' button below",
                                           reply_markup=await accept_consultation_request(record_id))
                    count += 1
                    await asyncio.sleep(.05)
    finally:
        logging.info(f"{count} messages sent")


@dp.callback_query_handler(PaidConsultationRequest())
async def confirm_assistance(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    await call.message.edit_reply_markup()
    user_id = call.from_user.id
    request_id = int(call.data.replace('confirm_paid_request_', ''))
    request = await db.get_consultation_record(request_id)
    await AssistanceState.contact_details_state.set()
    async with state.proxy() as data:
        data['request_id'] = request_id
        data['budget'] = request.get('budget')
    await bot.send_message(user_id, text=f"You have accepted request #{request_id} "
                                         f"for paid consultation. Client's budget is {request.get('budget')} $. "
                                         f"Provide your contact details, so the person who requested assistance "
                                         f"will be able to contact you directly.")
    logging.info(f'CREATE PAID REQUEST: {user_id} CONFIRM ASSISTANCE')


@dp.message_handler(state=AssistanceState.contact_details_state)
async def assistant_contact_details(message: Message, state: FSMContext):
    user_id = message.from_user.id
    contact_details = message.text
    name = message.from_user.full_name
    data = await state.get_data()
    await state.finish()
    assistance_id = await db.assign_assistance(user_id, name, contact_details, data['request_id'])
    await bot.send_message(user_id, text='Great, I notify the requester that you are willing to consult on the problem.'
                                         ' If he confirms that request is still relevant, we will send you the contact '
                                         'information.')
    experience = await db.get_consultant_experience(user_id)
    await notify_requester_about_paid_consultation(data['request_id'], experience, assistance_id['id'])
    logging.info(f'CREATE PAID REQUEST: {user_id} assistant_contact_details')


async def notify_requester_about_paid_consultation(request_id, experience, assistance_id):

    request = await db.get_consultation_record(request_id)
    total_budget = await transform_fee_amount(request['budget'])
    logging.info(f"notify_requester_about_paid_consultation: {request}, budget: {total_budget}")
    fee_amount = total_budget / 100
    user_id = request.get('user_id')

    await bot.send_message(user_id,
                           text=f'Hello! O ne assistant is ready to consult you on your request #{request_id}. '
                                f'If it is still relevant to you, please proceed with payment. '
                                f'Once you have paid the fee, we will share '
                                "the assistant's contact details with you, so you can contact him directly.\n\n"
                                f"<b>Consultant's experience:</b>\n{experience}\n"
                                f"<b>Our fee:</b> {fee_amount} USD",
                           reply_markup=await charge_paid_consultation_keys(request_id, assistance_id))
    logging.info(f'CREATE PAID REQUEST: {user_id} notify_requester_about_paid_consultation')


@rate_limit(5)
@dp.callback_query_handler(Text(startswith='paid_consultation_reject_'))
async def reject_assistance_proposal(call: CallbackQuery):
    await call.answer(cache_time=60)
    request_and_assistance_id = call.data.replace('paid_consultation_reject_', '').split('_')
    request_record = int(request_and_assistance_id[0])
    assistant_id = int(request_and_assistance_id[1])
    await try_send_message(assistant_id, text=f'Dear consultant, unfortunately client rejected your assistance '
                                              f'for request #{request_record}')
    await db.remove_assistance_record(request_record, assistant_id)
    await bot.send_message(
        call.from_user.id,
        text=f'Ok, {call.from_user.first_name}. Assistance rejected.',
        reply_markup=await start_keys(call.from_user.id)
    )
    await call.message.edit_reply_markup()
    logging.info(f'CREATE PAID REQUEST: reject_assistance_proposal')


@rate_limit(5)
@dp.callback_query_handler(Text(startswith='paid_consultation_confirm_'))
async def approve_paid_consultation(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=200)
    await call.message.edit_reply_markup()
    user_id = call.from_user.id
    ids = call.data.replace('paid_consultation_confirm_', '').split('_')
    request_id = int(ids[0])
    assistance_id = int(ids[1])
    request = await db.get_consultation_record(request_id)
    await PayConsultationFees.payment_state.set()
    fee_amount = await transform_fee_amount(request['budget'])
    assistant = await db.get_assistant(assistance_id)
    await bot.get_chat(assistant['user_id'])
    prices = [
        types.LabeledPrice(label='Paid consultation', amount=fee_amount)
    ]
    message_id = await bot.send_invoice(
        user_id,
        title=f'Fee invoice #{request_id}',
        description='Commission for using SapBazar Bot services.',
        provider_token=PAYMENTS_PROVIDER_TOKEN,
        currency='usd',
        prices=prices,
        start_parameter="create_job_invoice",
        photo_url='https://qa.sapbazar.com/api/post/aKj1PLKy.png',
        photo_width=512,
        photo_height=420,
        need_name=True,
        need_email=True,
        need_shipping_address=False,
        is_flexible=False,
        payload=f'{request_id}_{assistance_id}',
        reply_markup=consultation_payment_keys()
    )
    async with state.proxy() as data:
        data['message_id'] = message_id['message_id']
        data['request_id'] = request_id
    logging.info(f'CREATE PAID REQUEST: approve_paid_consultation')


@dp.pre_checkout_query_handler(lambda query: True, state=PayConsultationFees.payment_state)
async def checkout(query: types.PreCheckoutQuery, state: FSMContext):
    await state.finish()
    logging.info(f'USER ID {query.from_user.id} checkout')
    await bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True,
                                        error_message="Something went wrong. "
                                                      "Payment was not successful. "
                                                      "Please try again later.")


@rate_limit(5)
@dp.callback_query_handler(text='cancel_consultation_payment', state=PayConsultationFees.payment_state)
async def cancel_payment_consultation(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    name = call.from_user.full_name
    data = await state.get_data()
    await bot.delete_message(user_id, data['message_id'])
    await db.delete_consultation_record(data['request_id'])
    await state.finish()
    await bot.send_message(user_id, text=f'Hello, {name}', reply_markup=await start_keys(user_id))
    logging.info(f'CREATE PAID REQUEST: {user_id} cancel_payment_consultation')


@dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT)
async def got_payment(message: types.Message):
    user_id = message.from_user.id
    data = message.successful_payment.invoice_payload.split("_")
    request_id = int(data[0])
    assistance_id = int(data[1])
    assistant_record = await db.get_assistant(assistance_id)
    assistant_chat = await bot.get_chat(chat_id=assistant_record['user_id'])
    assistant_contact = assistant_record['contact']
    request_data = await db.get_consultation_record(request_id)
    requester_contact = request_data['contact']
    logging.info(f'PAID QUESTION MODE: USER ID {user_id} PAID FOR QUESTION')
    assistant_link = assistant_chat.user_url
    await bot.send_message(user_id,
                           "Success!\nYour contact details just sent to the consultant.\n"
                           f"Assistant contact details:\n{assistant_contact}\n"
                           f"Telegram username: @{assistant_chat.username}\n"
                           f"Telegram URL: {assistant_link}",
                           reply_markup=await start_keys(user_id))
    await send_client_contacts_to_consultant(
        consultant_id=assistant_record['user_id'],
        client_id=user_id,
        client_contact=requester_contact,
        request_id=request_id
    )
    logging.info(f'CREATE PAID REQUEST: {user_id} got_payment')


async def send_client_contacts_to_consultant(consultant_id,
                                             client_id,
                                             client_contact,
                                             request_id):
    request_record = await db.get_consultation_record(request_id)
    category = request_record['category']
    content = request_record['content']
    budget = request_record['budget']
    consultant = await bot.get_chat(consultant_id)
    consultant_name = consultant.first_name
    client = await bot.get_chat(client_id)
    client_telegram_url = await client.get_url()
    full_text = f"Hello, {consultant_name}. Client confirmed, that request #{request_id} " \
                f"is still relevant and your help is needed. " \
                f"Here we are sending you the request information.\n" \
                f"<b>Category:</b> {category}\n" \
                f"<b>Problem description:</b>\n{content}\n" \
                f"<b>Budget:</b> {budget}$\n" \
                f"<b>Client:</b> {client.full_name}\n" \
                f"<b>Username:</b> @{client.username}\n" \
                f"<b>Client telegram:</b> {client_telegram_url}\n" \
                f"<b>Client contacts:</b> {client_contact}\n" \
                f"Now, you can contact him directly."
    partitioned_text = split_text(full_text)
    for text in partitioned_text:
        await bot.send_message(
            consultant_id,
            text=text
        )
    logging.info(f'CREATE PAID REQUEST: {consultant_id} send_client_contacts_to_consultant')
