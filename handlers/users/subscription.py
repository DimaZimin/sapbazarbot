import asyncio
import logging

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.utils.exceptions import BotBlocked, RetryAfter, UserDeactivated, ChatNotFound, TelegramAPIError
from aiogram.types import CallbackQuery, Message
from filters.filters import SubscriptionCategories, SubscriptionLocations
from handlers.users.tools import try_send_message
from keyboards.inline.keyboard import start_subscription, sap_categories_keys, \
    subscription_locations_keys, blog_sub

from states.states import Form
from keyboards.inline.keyboard import start_keys
from loader import dp, db, bot, json_db, questions_api
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
    await Form.about_state.set()
    logging.info(f'USER ID: {user_id} -> consultant_experience_description()')
    await call.message.answer('Please, describe your experience in SAP in a few sentences.')
    await call.message.edit_reply_markup()


@rate_limit(5)
@dp.message_handler(state=Form.about_state)
async def consultant_experience_description(message: Message, state: FSMContext):
    description = message.text
    async with state.proxy() as data:
        data['description'] = description
    await db.create_or_update_consultant(
        user_id=message.from_user.id,
        name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        exp=description
    )
    await Form.categories_state.set()
    await message.answer('Thank you. Now, please select SAP category', reply_markup=await sap_categories_keys())


@rate_limit(5)
@dp.callback_query_handler(SubscriptionCategories(), state=Form.categories_state)
async def choose_category(call: CallbackQuery, state: FSMContext):
    """

    Callback query handler catches name of a category. Categories are stored in keyboard.py CATEGORIES variable.
    """
    await call.answer(cache_time=60)
    user_id = int(call.from_user.id)
    user_categories = await db.get_value('subscriptions', column='category', where_col='user_id', value=user_id)

    if call.data == 'next' and user_categories:
        logging.info(f'CHAT ID: {user_id} CHOOSING LOCATION')
        await Form.blog_subscription_state.set()
        await call.message.edit_reply_markup()
        await db.update_user(user_id=user_id, location="Remote", is_mentor=True)
        await call.message.answer(f'Do you want to subscribe to the SAP blog?', reply_markup=blog_sub())

    elif call.data == 'next' and not user_categories:
        logging.info(f'EMPTY CATEGORY\tCHAT ID: {call.from_user.id}')
        await call.message.edit_reply_markup()
        await call.message.answer(f'You have not chosen any category yet. First, choose a category '
                                  f'and then press Next button',
                                  reply_markup=await sap_categories_keys())
    else:
        callback_data = (call.message.text, call.message.chat.id)
        logging.info(f'CATEGORY UPDATE: {callback_data[1]}')
        user_id = int(call.from_user.id)
        category = call.data
        await db.add_user_category(user_id=user_id, category=category)
        logging.info(f'CATEGORY UPDATED: {category} FOR USER ID: {user_id}')
        await call.message.edit_reply_markup()
        await call.message.answer(f'{category} category has been selected. Select another '
                                  f'category or press the "Next" button',
                                  reply_markup=await sap_categories_keys())


@rate_limit(5)
@dp.callback_query_handler(text=['yes', 'no'], state=Form.blog_subscription_state)
async def subscribe_on_blog(call: CallbackQuery, state: FSMContext):
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
    await state.finish()
    await call.message.answer(f'You have successfully subscribed for job alert!',
                              reply_markup=await start_keys(user_id))


@rate_limit(5)
@dp.callback_query_handler(text='unsubscribe')
async def unsubscribe_from_job_alert(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    await db.delete_user_subscription(user_id)
    await db.update_user(user_id, job_subscription='False', is_mentor=False)
    logging.info(f'USER ID: {user_id} UNSUBSCRIBED FROM JOB ALERT')
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, "You have successfully unsubscribed from job alert.\n"
                                    "Thank you for choosing our service", reply_markup=await start_keys(user_id))


@rate_limit(5)
@dp.message_handler(Command(['unsubscribe']))
async def unsubscribe_blog(message: Message):
    user_id = message.chat.id
    await db.update_user(user_id=user_id, blog_subscription='False')
    logging.info(f'USER ID: {user_id} UNSUBSCRIBED FROM BLOG')
    await bot.send_message(user_id, text='You have been unsubscribed from blog.')


async def contact_to_send(contact):
    return f"Contact: @{contact[0]['username']}" if contact else ''


async def job_task(wait_time):
    """
    Main task function that runs every 'wait_time' value. Entry parameter must be an integer and corresponds to seconds.
    :param wait_time: integer - seconds
    """
    while True:
        await asyncio.sleep(wait_time)
        logging.info(f'SCHEDULED TASK IS EXECUTING...')
        json_manager = parsers.JsonManager(json_db)
        new_ads = json_manager.new_ads()
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
                await bot.send_message(chat_id='@sapbazar', text=f"<a href='{ad_url}'>New job opening: "
                                                                 f"{title}</a>"
                                                                 f"\n{await contact_to_send(contact)}",
                                       parse_mode='HTML')
                for user in users:
                    logging.info(f'MESSAGE SENT TO: {user["user_id"]}')
                    try:
                        await bot.send_message(user['user_id'], text=f"<a href='{ad_url}'>New job opening: "
                                                                     f"{title}</a>"
                                                                     f"\nContact: {await contact_to_send(contact)}",
                                                                     parse_mode='HTML')
                    except BotBlocked:
                        pass
        json_manager.update_job_urls()


async def blog_task(wait_time):
    while True:
        await asyncio.sleep(wait_time)
        json_manager = parsers.JsonManager(json_db)
        new_posts = json_manager.new_blog_post('blog_urls')
        logging.info(f"PERFORMING BLOG SCRAPING...\nNEW POSTS: {new_posts}")
        if new_posts:
            logging.info("ITERATION OVER BLOG ARTICLES")
            for post in new_posts:
                category = post[1]
                post_url = post[0]
                logging.info(f"CATEGORY: {category}\nURL: {post_url}\n")
                subscribers = await db.get_blog_subscription_users(f"{category}")
                logging.info(f"SUBSCRIBERS: {subscribers}")
                count = 0
                try:
                    for subscriber in subscribers:
                        logging.info(f"SENDING URL TO: {subscriber}")
                        text_to_send = f'<a href="{post_url}"> Hey! We got a new post here! Check this out.</a>'
                        user_id = subscriber['user_id']
                        if await try_send_message(int(user_id), text=text_to_send, reply_markup=await start_keys(user_id)):
                            count += 1
                        await asyncio.sleep(.05)
                finally:
                    logging.info(f"{count} messages sent")
            json_manager.update_blog_urls('blog_urls')


async def blog_task_for_channel(wait_time):
    while True:
        await asyncio.sleep(wait_time)
        json_manager = parsers.JsonManager(json_db)
        new_posts = json_manager.new_blog_post('blog_channel')

        if len(new_posts) >= 5:
            text_to_send = "\n\n".join([
                f'<a href="{post[0]}">{post[2]}</a> in {post[1]}' for post in new_posts[:5]
            ])
            try:
                await bot.send_message(chat_id='@sapbazar', text=f'New posts:\n\n{text_to_send}',
                                       parse_mode='HTML')
            except RetryAfter:
                pass
            json_manager.update_blog_urls('blog_channel')


async def points_task(wait_time):
    while True:
        await asyncio.sleep(wait_time)
        users_points = await questions_api.get_top_ten()

        if users_points:
            user_rating = []

            for chat in users_points:

                chat_id = chat['user']
                points = chat['points']

                try:
                    user_chat = await bot.get_chat(chat_id=chat_id)
                    full_name = f"{user_chat.first_name if user_chat.first_name else ''} " \
                                f"{user_chat.last_name if user_chat.last_name else ''} " \
                                f"{user_chat.username if user_chat.username else ''}"

                    user_rating.append(f"{full_name} - {points} points")
                except ChatNotFound:
                    user_rating.append(f"{chat_id} - {points} points")

            joined_points = '\n'.join(user_rating)
            text_to_send = f"Hello! The rating of the most active SAP consultants:\n\n{joined_points}\n\n"

            all_users = await db.fetch_value('user_id', 'users')
            count = 0

            try:
                for user in all_users:
                    user_id = user['user_id']
                    if await try_send_message(int(user_id), text=text_to_send, reply_markup=await start_keys(user_id)):
                        count += 1
                    await asyncio.sleep(.05)
            finally:
                logging.info(f"{count} messages sent")
