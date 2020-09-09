from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, ContentTypes
from loader import dp, bot
from aiogram import types
from middlewares.middleware import CreateJob
from keyboards.inline.keyboard import job_post_callback, CATEGORIES, job_categories, job_locations, LOCATIONS, \
    confirmation_keys, invoice_callback, start_keys

PAYMENTS_PROVIDER_TOKEN = '381764678:TEST:18773'

prices = [
    types.LabeledPrice(label='Job posting fees', amount=50_000),
    types.LabeledPrice(label='VAT 20%', amount=10_000),
]


@dp.callback_query_handler(job_post_callback.filter(posting='start'))
async def create_job_post(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    await CreateJob.job_name.set()
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, 'Type a job name')


@dp.message_handler(state=CreateJob.job_name)
async def process_job_name(message: Message, state: FSMContext):
    job_name = message.text
    async with state.proxy() as data:
        data["job_name"] = job_name
    await CreateJob.job_description.set()
    await message.answer('Type job description')


@dp.message_handler(state=CreateJob.job_description)
async def process_job_description(message: Message, state: FSMContext):
    chat_id = message.chat.id
    job_description = message.text
    async with state.proxy() as data:
        data["job_description"] = job_description
    await CreateJob.job_category.set()
    await bot.send_message(chat_id=chat_id, text='Choose job category', reply_markup=job_categories())


@dp.callback_query_handler(job_post_callback.filter(posting=CATEGORIES), state=CreateJob.job_category)
async def process_job_category(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    chat_id = call.message.chat.id
    job_category = job_post_callback.parse(call.data)['posting']
    async with state.proxy() as data:
        data["job_category"] = job_category
    await CreateJob.job_location.set()
    await call.message.edit_reply_markup()
    await bot.send_message(chat_id=chat_id, text='Choose job location', reply_markup=job_locations())


@dp.callback_query_handler(job_post_callback.filter(posting=LOCATIONS), state=CreateJob.job_location)
async def process_job_location(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    chat_id = call.message.chat.id
    job_location = job_post_callback.parse(call.data)['posting']
    async with state.proxy() as data:
        data["job_location"] = job_location
    await call.message.edit_reply_markup()
    await CreateJob.send_invoice.set()
    await bot.send_message(chat_id=chat_id, text=f"Please review your job posting.\n\n"
                                                 f"Name: {data['job_name']}\n\n"
                                                 f"Description: {data['job_description']}\n\n"
                                                 f"Category: {data['job_category']}\n\n"
                                                 f"Location: {data['job_location']}",
                           reply_markup=confirmation_keys())


@dp.callback_query_handler(invoice_callback.filter(confirm='yes'), state=CreateJob.send_invoice)
async def send_invoice(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    chat_id = call.message.chat.id
    data = await state.get_data()
    await state.finish()
    await bot.send_invoice(chat_id,
                           title='Job posting',
                           description=f"Name: {data['job_name']}\n\n"
                                       f"Description: {data['job_description']}\n\n"
                                       f"Category: {data['job_category']}\n\n"
                                       f"Location: {data['job_location']}",
                           provider_token=PAYMENTS_PROVIDER_TOKEN,
                           currency='rub',
                           prices=prices,
                           start_parameter="create_job_invoice",
                           need_name=True,
                           need_email=True,
                           need_shipping_address=False,
                           is_flexible=False,
                           payload='HAPPY FRIDAYS COUPON')


@dp.callback_query_handler(invoice_callback.filter(confirm='no'), state=CreateJob.send_invoice)
async def cancel_posting(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    await state.finish()
    await call.message.edit_reply_markup()
    await bot.send_message(call.from_user.id, text='Yo', reply_markup=start_keys())


@dp.pre_checkout_query_handler(lambda query: True)
async def checkout(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True,
                                        error_message="Aliens tried to steal your card's CVV,"
                                                      " but we successfully protected your credentials,"
                                                      " try to pay again in a few minutes, we need a small rest.")


@dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT)
async def got_payment(message: types.Message):
    await bot.send_message(message.chat.id,
                           'Success! Thank you for using our services payment! '
                           'We will proceed your order for `{} {}`'
                           ' as fast as possible! Stay in touch.'.format(
                               message.successful_payment.total_amount / 100, message.successful_payment.currency),

                           parse_mode='Markdown', reply_markup=start_keys())
