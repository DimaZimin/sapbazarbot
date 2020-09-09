from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, ContentTypes
from loader import dp, bot
from aiogram import types
from keyboards.inline.keyboard import CATEGORIES, LOCATIONS, start_keys, start_subscription



@dp.callback_query_handler(start_subscription.filter(action='next'))
async def process_subscription(call: CallbackQuery):
    """
    Callback query handler that catches 'next' action which is associated with pressing 'Subscribe' button.
    This corresponds to start_keys() function in keyboard.py.
    """
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    db_manager.add_subscriber(user_id)
    db_manager.update_subscription(user_id, True)
    logging.info(f'USER ID: {user_id} CHOOSING CATEGORIES')
    await call.message.answer('Please choose your SAP categories',
                              reply_markup=category_keys())
    await call.message.edit_reply_markup()


@dp.callback_query_handler(category_callback.filter(category=CATEGORIES))
async def add_category(call: CallbackQuery):
    """

    Callback query handler catches name of a category. Categories are stored in keyboard.py CATEGORIES variable.
    """
    await call.answer(cache_time=60)
    if call.data == 'choose_category:Next' and db_manager.get_user_categories(call.from_user.id):
        logging.info(f'CHAT ID: {call.from_user.id} CHOOSING LOCATION')
        await Form.state.set()
        await call.message.edit_reply_markup()
        await call.message.answer('Please, choose your location', reply_markup=localization_keys())
    elif call.data == 'choose_category:Next' and not db_manager.get_user_categories(call.from_user.id):
        logging.info(f'EMPTY CATEGORY\tCHAT ID: {call.from_user.id}')
        await call.message.edit_reply_markup()
        await call.message.answer(f'You have not chosen any category yet. First, choose a category '
                                  f'and then press Next button',
                                  reply_markup=category_keys())
    else:
        callback_data = (call.message.text, call.message.chat.id)
        logging.info(f'CATEGORY UPDATE: {callback_data[1]}')
        user_id = call.from_user.id
        category = category_callback.parse(call.data)['category']
        db_manager.add_user_category(user_id=user_id, category=category)
        logging.info(f'CATEGORY UPDATED: {category} FOR USER ID: {user_id}')
        await call.message.edit_reply_markup()
        await call.message.answer(f'{category} category has been added. Choose another category or press Next',
                                  reply_markup=category_keys())


@dp.callback_query_handler(location_callback.filter(location=LOCATIONS), state=Form.state)
async def set_location(call: CallbackQuery, state: FSMContext):
    """
    Callback query catches name of location. Locations are stored in keyboard.py LOCATIONS variable.
    """
    await call.answer(cache_time=60)
    callback_data = (call.message.text, call.message.chat.id)
    logging.info(f'call = {callback_data[0]}\tchat id: {callback_data[1]}')
    user_id = call.from_user.id
    location = location_callback.parse(call.data)['location']
    db_manager.update_location(user_id=user_id, location=location)
    logging.info(f'LOCATION UPDATED: {location} FOR USER ID: {user_id}')
    await state.finish()
    await call.message.edit_reply_markup()
    await call.message.answer(f'{location} location has been chosen. '
                              f'You have successfully subscribed for job alert!',
                              reply_markup=unsubscribe_key)


@dp.message_handler(filters.Text(contains=['Unsubscribe']))
async def unsubscribe(message: types.Message):
    """
    Unsubscribe button function
    """
    user_id = message.from_user.id
    db_manager.remove_subscription(user_id)
    db_manager.update_subscription(user_id, status=False)
    logging.info(f'USER ID: {user_id} UNSUSCRIBED')
    await message.answer("You have successfully unsubscribed from job alert", reply_markup=ReplyKeyboardRemove())
    await message.answer("Thank you for choosing our service", reply_markup=start_keys())


def check_user_requirements(user_id, url) -> str:
    """
    Validate if a url associated with a job on the website satisfies user requirements regarding category and location
    of a job.
    :param user_id: user chat_id
    :param url: url as a string
    :return: URL as a string if satisfies user's subscription records
    """
    user_categories = db_manager.get_user_categories(user_id)
    user_location = db_manager.get_user_location(user_id)
    html = parser.HTMLParser(url)
    if html.location() == user_location and html.category() in user_categories:
        return url


async def scheduled_task(wait_time):
    """
    Main task function that runs every 'wait_time'. Entry parameter must be an integer and corresponds to seconds.
    :param wait_time: integer - seconds
    """
    while True:
        await asyncio.sleep(wait_time)
        logging.info(f'SCHEDULED TASK PERFORMING...')
        json_file = parser.JSONContextManager(json_db)
        xml = parser.XMLParser()
        old_ads = json_file.json_old_ads()
        logging.info(f'CURRENT ADS IDS ({len(xml.get_ids())}) : {xml.get_ids()}\n')
        logging.info(f'OLD ADS : {len(old_ads)}{old_ads}\n')
        logging.info(f'DIFF (NEW ADS): {len(xml.get_ids()) - len(old_ads)}')
        logging.info(f'JSON FILE UPDATING...')
        json_file.update_json()
        subscribers = [sub[0] for sub in db_manager.get_active_subscriptions()]
        new_ads = json_file.json_new_ads()
        logging.info(f'NEW ADS: {new_ads}')
        if new_ads:
            for subscriber in subscribers:
                for url in new_ads:
                    link = check_user_requirements(subscriber, url)
                    if link:
                        html = parser.HTMLParser(link)
                        logging.info(f'URL {link} SENT TO USER ID: {subscriber}')
                        await bot.send_message(subscriber, text=f"<a href='{link}'>New job openning: "
                                                                f"{html.job_title()}</a>",
                                               parse_mode='HTML')
