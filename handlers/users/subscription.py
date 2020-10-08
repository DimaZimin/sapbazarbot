import asyncio
import logging

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, Message
from filters.filters import SubscriptionCategories, SubscriptionLocations
from keyboards.inline.keyboard import start_subscription, subscription_category_keys, \
    localization_keys, unsubscribe_key, blog_sub

from middlewares.middleware import Form
from keyboards.inline.keyboard import start_keys
from loader import dp, db, bot, json_db
from utils.parsers import parsers
from utils.misc import rate_limit


@rate_limit(5)
@dp.callback_query_handler(start_subscription.filter(action='subscribe'))
async def process_subscription(call: CallbackQuery):
    """
    Callback query handler that catches 'next' action which corresponds to 'Subscribe' button.
    """
    await call.answer(cache_time=60)
    user_id = int(call.from_user.id)
    name = f"{call.from_user.first_name} {call.from_user.last_name}"
    await db.add_user(user_id, name)
    logging.info(f'USER ID: {user_id} CHOOSING CATEGORIES')
    await call.message.answer('Please choose your SAP categories',
                              reply_markup=await subscription_category_keys())
    await call.message.edit_reply_markup()


@rate_limit(5)
@dp.callback_query_handler(SubscriptionCategories())
async def choose_category(call: CallbackQuery):
    """

    Callback query handler catches name of a category. Categories are stored in keyboard.py CATEGORIES variable.
    """
    await call.answer(cache_time=60)
    user_id = int(call.from_user.id)
    user_categories = await db.get_value('subscriptions', column='category', where_col='user_id', value=user_id)
    if call.data == 'next' and user_categories:
        logging.info(f'CHAT ID: {user_id} CHOOSING LOCATION')
        await Form.state.set()
        await call.message.edit_reply_markup()
        await call.message.answer('Please, choose your location', reply_markup=await localization_keys())
    elif call.data == 'next' and not user_categories:
        logging.info(f'EMPTY CATEGORY\tCHAT ID: {call.from_user.id}')
        await call.message.edit_reply_markup()
        await call.message.answer(f'You have not chosen any category yet. First, choose a category '
                                  f'and then press Next button',
                                  reply_markup=await subscription_category_keys())
    else:
        callback_data = (call.message.text, call.message.chat.id)
        logging.info(f'CATEGORY UPDATE: {callback_data[1]}')
        user_id = int(call.from_user.id)
        category = call.data
        await db.add_user_category(user_id=user_id, category=category)
        logging.info(f'CATEGORY UPDATED: {category} FOR USER ID: {user_id}')
        await call.message.edit_reply_markup()
        await call.message.answer(f'{category} category has been added. Choose another category or press Next',
                                  reply_markup=await subscription_category_keys())


@rate_limit(5)
@dp.callback_query_handler(SubscriptionLocations(), state=Form.state)
async def set_location(call: CallbackQuery, state: FSMContext):
    """
    Callback query catches name of location. Locations are stored in keyboard.py LOCATIONS variable.
    """
    await call.answer(cache_time=60)
    callback_data = (call.message.text, call.message.chat.id)
    logging.info(f'call = {callback_data[0]}\tchat id: {callback_data[1]}')
    user_id = int(call.from_user.id)
    location = call.data
    await db.update_user(user_id=user_id, location=location)
    logging.info(f'LOCATION UPDATED: {location} FOR USER ID: {user_id}')
    await state.finish()
    await call.message.edit_reply_markup()
    await call.message.answer(f'{location} location has been chosen. '
                              f'Do you want to subscribe on SAP blog',
                              reply_markup=blog_sub())


@rate_limit(5)
@dp.callback_query_handler(text=['yes', 'no'])
async def subscribe_on_blog(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    if call.data == 'yes':
        await db.update_user(user_id, blog_subscription='True')
        logging.info(f"USER {user_id} SUBSCRIBED ON BLOG")
    else:
        await db.update_user(user_id, blog_subscription='False')
        logging.info(f"USER {user_id} REFUSED TO SUBSCRIBE ON BLOG")
    await db.update_user(user_id, job_subscription='True')
    await call.message.edit_reply_markup()
    logging.info(f"USER {user_id} SUBSCRIBED FOR JOB ALERT")
    await call.message.answer(f'You have successfully subscribed for job alert!',
                              reply_markup=unsubscribe_key())


@rate_limit(5)
@dp.message_handler(Text(contains='Unsubscribe'))
async def unsubscribe(message: Message):
    """
    Unsubscribe button function
    """
    user_id = message.from_user.id
    await db.delete_user_subscription(user_id)
    await db.update_user(user_id, job_subscription='False')
    logging.info(f'USER ID: {user_id} UNSUBSCRIBED FROM JOB ALERT')
    await message.answer("You have successfully unsubscribed from job alert", reply_markup=ReplyKeyboardRemove())
    await message.answer("Thank you for choosing our service", reply_markup=start_keys(user_id))


@rate_limit(5)
@dp.message_handler(Command(['unsubscribe']))
async def unsubscribe_blog(message: Message):
    user_id = message.chat.id
    await db.update_user(user_id=user_id, blog_subscription='False')
    logging.info(f'USER ID: {user_id} UNSUBSCRIBED FROM BLOG')
    await bot.send_message(user_id, text='You have been unsubscribed from blog.')


async def contact_to_send(contact):
    return f"@{contact[0]['username']}" if contact else 'https://sapbazar.com/more/contactus'


async def job_task(wait_time):
    """
    Main task function that runs every 'wait_time'. Entry parameter must be an integer and corresponds to seconds.
    :param wait_time: integer - seconds
    """
    while True:
        await asyncio.sleep(wait_time)
        logging.info(f'SCHEDULED TASK IS EXECUTING...')
        json_manager = parsers.JsonManager(json_db)
        new_ads = json_manager.get_values('job_new')
        logging.info(f'NEW ADS: {new_ads}')
        if new_ads:
            logging.info('ITERATION OVER ADS...')
            for ad_url in new_ads:
                html = parsers.HTMLParser(ad_url)
                category = html.category()
                location = html.location()
                title = html.job_title()
                contact = await db.get_username(f"{' '.join(html.job_title().split()[:-3])}")
                logging.info(f'LINK: {ad_url} CATEGORY: {category} LOCATION: {location}')
                users = await db.select_user(location=location, category=category)
                logging.info(f'USERS: {users}')
                logging.info(f"MESSAGE SENT TO CHANNEL")
                await bot.send_message(chat_id='@ivankaim', text=f"<a href='{ad_url}'>New job opening: "
                                                                 f"{title}</a>"
                                                                 f"\nContact: {await contact_to_send(contact)}",
                                       parse_mode='HTML')
                for user in users:
                    logging.info(f'MESSAGE SENT TO: {user["user_id"]}')
                    await bot.send_message(user['user_id'], text=f"<a href='{ad_url}'>New job opening: "
                                                                 f"{title}</a>"
                                                                 f"\nContact: {await contact_to_send(contact)}",
                                                                 parse_mode='HTML')
        json_manager.update_job_urls()


async def blog_task(wait_time):
    while True:
        await asyncio.sleep(wait_time)
        json_manager = parsers.JsonManager(json_db)
        new_posts = json_manager.new_blog_post()
        logging.info(f"PERFORMING BLOG SCRAPING...\nNEW POSTS: {new_posts}")
        if new_posts:
            logging.info("ITERATION OVER BLOG ARTICLES")
            for post in new_posts:
                category = post[1]
                post_url = post[0]
                logging.info(f"CATEGORY: {category}\nURL: {post_url}\n")
                subscribers = await db.get_blog_subscription_users(f"{category}")
                logging.info(f"SUBSCRIBERS: {subscribers}")
                logging.info(f"SENDING BLOG MESSAGE TO CHANNEL")
                await bot.send_message(chat_id='@sapbazar', text=f'<a href="{post_url}"> Hey! We got'
                                                                 f' a new post here! Check this out.</a>',
                                       parse_mode='HTML')
                for subscriber in subscribers:
                    logging.info(f"SENDING URL TO: {subscriber}")
                    await bot.send_message(subscriber['user_id'], text=f'<a href="{post_url}"> Hey! We got'
                                                                       f' a new post here! Check this out.</a>',
                                           parse_mode='HTML')
        json_manager.update_blog_urls()
