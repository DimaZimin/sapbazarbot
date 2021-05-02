import logging

from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, ContentTypes
from aiogram import types

from data.config import PAYMENTS_PROVIDER_TOKEN
from loader import dp, bot, db, mysql_db
from states.states import CreateJob
from keyboards.inline.keyboard import job_post_callback, job_categories_keys, job_locations_keys, \
    confirmation_keys, invoice_callback, start_keys, payment_keys
from filters.filters import JobCategory, JobLocation
from utils.misc import rate_limit


async def prices():
    fee_amount = await db.fetch_value('posting_fees', 'settings')
    return [
        types.LabeledPrice(label='Job posting fees', amount=int(fee_amount[0]['posting_fees'])),
        types.LabeledPrice(label='VAT 20%', amount=int(fee_amount[0]['posting_fees'] * 0.2)),
    ]


@rate_limit(5)
@dp.callback_query_handler(job_post_callback.filter(posting='start'))
async def start_creating_job_post(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    name = f"{call.from_user.first_name} {call.from_user.last_name}"
    logging.info(f'USER ID {user_id} {name} BEGINS JOB CREATIONS')
    await db.add_user(user_id, name)
    await bot.send_chat_action(chat_id=user_id, action='typing')
    """TODO: ADD USER TO DATABASE"""
    await CreateJob.company_name.set()
    await bot.send_message(user_id, 'Please, type your company name')


@rate_limit(5)
@dp.message_handler(state=CreateJob.company_name)
async def process_company_name(message: Message, state: FSMContext):
    user_id = message.chat.id
    company_name = message.text
    await bot.send_chat_action(user_id, action='typing')
    logging.info(f'USER ID {user_id} COMPANY: {company_name} ')
    async with state.proxy() as data:
        data["company_name"] = company_name
    await CreateJob.job_name.set()
    await bot.send_message(user_id, 'Please, type a job title')


@rate_limit(5)
@dp.message_handler(state=CreateJob.job_name)
async def process_job_name(message: Message, state: FSMContext):
    job_name = message.text
    user_id = message.chat.id
    logging.info(f'USER ID {user_id} JOB TITLE: {job_name} ')
    await bot.send_chat_action(user_id, action='typing')
    async with state.proxy() as data:
        data["job_name"] = job_name
    await CreateJob.job_description.set()
    await message.answer('Please, write a job description')


@rate_limit(5)
@dp.message_handler(state=CreateJob.job_description)
async def process_job_description(message: Message, state: FSMContext):
    user_id = message.chat.id
    job_description = message.text
    logging.info(f'USER ID {user_id} JOB DESCRIPTION: {job_description} ')
    await bot.send_chat_action(user_id, action='typing')
    async with state.proxy() as data:
        data["job_description"] = job_description
    await CreateJob.job_category.set()
    await bot.send_message(chat_id=user_id, text='Select a job category', reply_markup=await job_categories_keys())


@rate_limit(5)
@dp.callback_query_handler(text='add_cat', state=CreateJob.job_category)
async def add_category(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    logging.info(f'USER ID {user_id} ADDS CATEGORY')
    await CreateJob.job_category_add.set()
    await bot.send_chat_action(user_id, action='typing')
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id, text='Type a category name', reply_markup=None)


@rate_limit(5)
@dp.callback_query_handler(text='add_loc', state=CreateJob.job_location)
async def add_location(call: CallbackQuery):
    await call.answer(cache_time=60)
    await CreateJob.job_location_add.set()
    user_id = call.message.chat.id
    logging.info(f'USER ID {user_id} ADDS CATEGORY')
    await bot.send_chat_action(user_id, action='typing')
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id, text='What is your location? Type a city or country', reply_markup=None)


@rate_limit(5)
@dp.message_handler(state=CreateJob.job_location_add)
async def render_location(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    job_location = message.text
    await bot.send_chat_action(user_id, action='typing')
    async with state.proxy() as data:
        data['job_location'] = job_location
    logging.info(f'USER ID {job_location} RENDERING LOCATION')
    await CreateJob.send_invoice.set()
    await bot.send_message(chat_id=user_id, text=f"Please review your job posting:\n\n"
                                                 f"<b>Your company name</b>:\n"
                                                 f"{data['company_name']}\n\n"
                                                 f"<b>Job title</b>:\n"
                                                 f"{data['job_name']}\n\n"
                                                 f"<b>Description:</b>\n"
                                                 f"{data['job_description']}\n\n"
                                                 f"<b>Category</b>:\n"
                                                 f"{data['job_category']}\n\n"
                                                 f"<b>Location</b>:\n"
                                                 f"{data['job_location']}",
                           reply_markup=confirmation_keys(), parse_mode=types.ParseMode.HTML)


@rate_limit(5)
@dp.message_handler(state=CreateJob.job_category_add)
async def render_category(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    job_category = message.text
    await bot.send_chat_action(user_id, action='typing')
    async with state.proxy() as data:
        data["job_category"] = job_category
    logging.info(f'USER ID {job_category} CATEGORY RENDERING')
    await CreateJob.job_location.set()
    await bot.send_message(chat_id=user_id, text='Choose job location', reply_markup=await job_locations_keys())


@rate_limit(5)
@dp.callback_query_handler(JobCategory(), state=CreateJob.job_category)
async def process_job_category(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    job_category = call.data[2:]
    await bot.send_chat_action(user_id, action='typing')
    async with state.proxy() as data:
        data["job_category"] = job_category
    logging.info(f'USER ID {job_category} CATEGORY ADDED')
    await CreateJob.contact.set()
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=user_id, text='Please provide your contact details. '
                                                 'Type your name, email and mobile phone number.')


@rate_limit(5)
@dp.callback_query_handler(JobLocation(), state=CreateJob.job_location)
async def process_job_location(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    job_location = call.data[2:]
    await bot.send_chat_action(user_id, action='typing')
    async with state.proxy() as data:
        data["job_location"] = job_location
    logging.info(f'USER ID {job_location} LOCATION ADDED')
    await CreateJob.contact.set()
    await bot.send_message(chat_id=user_id, text='Please provide your contact details. '
                                                 'Type your name, email and mobile phone number.')


@rate_limit(5)
@dp.message_handler(state=CreateJob.contact)
async def process_contact_data(message: Message, state: FSMContext):
    user_id = message.chat.id
    contact = message.text
    logging.info(f'USER ID {user_id} SETS CONTACT: {contact} ')
    await bot.send_chat_action(user_id, action='typing')
    async with state.proxy() as data:
        data["contact"] = contact
        data["job_location"] = 'Remote'
    await CreateJob.send_invoice.set()
    await bot.send_message(chat_id=user_id, text=f"Please, review your job posting\n\n"
                                                 f"<b>Your company name</b>:\n"
                                                 f"{data['company_name']}\n\n"
                                                 f"<b>Job title</b>:\n"
                                                 f"{data['job_name']}\n\n"
                                                 f"<b>Description:</b>\n"
                                                 f"{data['job_description']}\n\n"
                                                 f"<b>Category</b>:\n"
                                                 f"{data['job_category']}\n\n"
                                                 f"<b>Location</b>:\n"
                                                 f"{data['job_location']}\n\n"
                                                 f"<b>Contact</b>:\n"
                                                 f"{data['contact']}",
                           reply_markup=confirmation_keys(), parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(invoice_callback.filter(confirm='yes'), state=CreateJob.send_invoice)
async def send_invoice(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await bot.send_chat_action(user_id, action='typing')
    data = await state.get_data()
    await CreateJob.checkout.set()
    await call.message.edit_reply_markup()
    db_status = await db.fetch_value('payable', 'settings')
    company = data['company_name']
    description = data['job_description']
    job_title = f"{company} - {data['job_name']}"
    category = data['job_category']
    location = data['job_location']
    contact = data['contact']
    username = call.from_user.username
    if not username:
        username = data['contact']
    logging.info(f'USER ID {user_id} SENDING INVOICE')
    if db_status[0]['payable']:
        await bot.send_invoice(user_id,
                               title='Your job advertisement',
                               description=f"Job title: {job_title}\n\n"
                                           f"Company: {company}\n\n"
                                           f"Description: {description}\n\n"
                                           f"Category: {category}\n\n"
                                           f"Location: {location}",
                               provider_token=PAYMENTS_PROVIDER_TOKEN,
                               currency='rub',
                               prices=await prices(),
                               start_parameter="create_job_invoice",
                               need_name=True,
                               need_email=True,
                               need_shipping_address=False,
                               is_flexible=False,
                               payload='HAPPY FRIDAYS COUPON',
                               reply_markup=payment_keys()
                               )
    else:
        mysql_description = f"Company: {company}<br> Location: {location}<br>{description}<br>Contact: {contact}"
        mysql_db.insert_job(company, job_title, mysql_description, category, location)
        await db.submit_order(user_id, company, job_title, description, category, location, False, username, contact)
        await state.finish()
        logging.info(f'USER ID {user_id} JOB POSTED')
        await bot.send_message(chat_id=user_id, text='Success! Your job posting has been created!',
                               reply_markup=start_keys(user_id))


@dp.callback_query_handler(invoice_callback.filter(confirm='no'), state=CreateJob.send_invoice)
async def cancel_posting(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await bot.send_chat_action(user_id, action='typing')
    await state.finish()
    await call.message.delete_reply_markup()
    logging.info(f'USER ID {user_id} CANCEL JOB POSTING')
    await bot.send_message(user_id, text='Welcome back!', reply_markup=start_keys(user_id))


@dp.callback_query_handler(text='cancel_payment', state=CreateJob.checkout)
async def cancel_payment(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.message.chat.id
    await bot.send_chat_action(user_id, action='typing')
    await state.finish()
    logging.info(f'USER ID {user_id} CANCELLED PAYMENT')
    await bot.send_message(user_id, text='Job posting has been cancelled.', reply_markup=None)
    await bot.send_message(user_id, text='Welcome back!', reply_markup=start_keys(user_id))


@dp.pre_checkout_query_handler(lambda query: True, state=CreateJob.checkout)
async def checkout(query: types.PreCheckoutQuery, state: FSMContext):
    await CreateJob.payment_paid.set()
    async with state.proxy() as data:
        data["email"] = query.order_info['email']
    logging.info(f'USER ID {query.from_user.id} checkout')
    await bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True,
                                        error_message="Aliens tried to steal your card's CVV,"
                                                      " but we successfully protected your credentials,"
                                                      " try to pay again in a few minutes, we need a small rest.")


@dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT, state=CreateJob.payment_paid)
async def got_payment(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    data = await state.get_data()
    company = data['company_name']
    description = data['job_description']
    job_title = f"{company} - {data['job_name']}"
    category = data['job_category']
    location = data['job_location']
    email = data['email']
    username = message.from_user.username
    await db.submit_order(user_id, company, job_title, description,
                          category, location, True, username, email)
    await state.finish()
    mysql_description = f"Company:{company}<br>Location: {location}<br>{description}<br>Contact: {email}"
    mysql_db.insert_job(company, job_title, mysql_description, category, location)
    logging.info(f'USER ID {user_id} GOT PAYMENT')
    await bot.send_chat_action(user_id, action='typing')
    await bot.send_message(user_id,
                           'Success! Thank you for using our services! '
                           'We will proceed your order for `{} {}`'
                           ' as fast as possible! Stay in touch.'.format(
                               message.successful_payment.total_amount / 100, message.successful_payment.currency),
                           parse_mode='Markdown', reply_markup=start_keys(user_id))
