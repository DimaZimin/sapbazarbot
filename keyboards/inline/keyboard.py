"""
This file contains keyboard and callback settings
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData
from data.config import admins
from loader import db, questions_api

category_callback = CallbackData('choose_category', 'category')
start_subscription = CallbackData('subscription', 'action')
job_post_callback = CallbackData('job_posting', 'posting')
invoice_callback = CallbackData('send_invoice', 'confirm')
location_callback = CallbackData('choose_location', 'location')
# remove_category_callback = CallbackData('remove_category', 'category')


def start_keys(admin_id):
    """
    Inline keyboard that pops up after activating /start command
    """
    markup = InlineKeyboardMarkup(row_width=2)
    markup.insert(InlineKeyboardButton(text="✅ Subscribe", callback_data=start_subscription.new(action='subscribe')))
    markup.insert(InlineKeyboardButton(text='❓ Ask SAP GURU', callback_data='ask_question'))
    markup.insert(InlineKeyboardButton(text='🙋 My questions', callback_data='my_questions'))
    markup.insert(InlineKeyboardButton(text='See all questions', callback_data='all_questions'))
    markup.insert(InlineKeyboardButton(text="✉️ Contact", url='telegram.me/gurusap'))
    markup.insert(InlineKeyboardButton(text="💼 Post a Job", callback_data=job_post_callback.new(posting='start')))

    if str(admin_id) in admins:
        markup.insert(InlineKeyboardButton(text="ADMIN", callback_data='ADMIN'))
    return markup


def start_keys_unsubscribe(admin_id):
    """
    Inline keyboard that pops up after activating /start command
    """
    markup = InlineKeyboardMarkup(row_width=2)
    markup.insert(InlineKeyboardButton(text="❌ Unsubscribe", callback_data="unsubscribe"))
    markup.insert(InlineKeyboardButton(text="💼 Post a Job", callback_data=job_post_callback.new(posting='start')))
    markup.insert(InlineKeyboardButton(text="✉️ Contact", url='telegram.me/gurusap'))
    markup.insert(InlineKeyboardButton(text='❓ Ask SAP GURU', callback_data='ask_question'))
    markup.insert(InlineKeyboardButton(text='🙋 My questions', callback_data='my_questions'))
    markup.insert(InlineKeyboardButton(text='See all questions', callback_data='all_questions'))
    if str(admin_id) in admins:
        markup.insert(InlineKeyboardButton(text="ADMIN", callback_data='ADMIN'))
    return markup


async def subscription_category_keys() -> InlineKeyboardMarkup:
    """
    Inline keyboard that includes all available categories. This keyboard pops up after pressing "Subscribe" button.
    CATEGORIES can be expanded by adding a category name to CATEGORY list namespace.
    Make sure that added category is exactly the same as it is on the website, including the font case,
    as it is case sensitive.
    !!!IMPORTANT!!! DO NOT REMOVE 'Next' at the end of the list. Keep it there for convenience!!!
    """
    markup = InlineKeyboardMarkup(row_width=2)
    categories = [category['category_name'] for category in
                  await db.fetch_value('category_name', 'Categories')]
    for category in categories:
        button = InlineKeyboardButton(category, callback_data=category)
        markup.insert(button)
    markup.insert(InlineKeyboardButton('Next', callback_data='next'))
    return markup


async def job_categories_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    categories = [category['category_name'] for category in await db.fetch_value('category_name', 'Categories')]
    for category in categories:
        button = InlineKeyboardButton(category, callback_data=f"JP{category}")
        markup.insert(button)
    # markup.insert(InlineKeyboardButton('Add new category',
    #                                    callback_data='add_cat'))
    return markup


async def job_locations_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    locations = [location['location_name'] for location in await db.fetch_value('location_name', 'Locations')]
    for location in locations:
        button = InlineKeyboardButton(location, callback_data=f"JP{location}")
        markup.insert(button)
    # markup.insert(InlineKeyboardButton('Add new location',
    #                                    callback_data='add_loc'))
    return markup


def confirmation_keys() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [InlineKeyboardButton('Confirm', callback_data=invoice_callback.new(confirm='yes'))],
            [InlineKeyboardButton('Cancel', callback_data=invoice_callback.new(confirm='no'))]])


def payment_keys() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [InlineKeyboardButton('Pay', pay=True)],
            [InlineKeyboardButton('Cancel', callback_data='cancel_payment')]
        ]
    )


async def subscription_locations_keys() -> InlineKeyboardMarkup:
    """
    Inline keyboard associated with locations and cities included in LOCATIONS list namespace.
    You can add new locations to LOCATIONS namespace. Make sure that added location is exactly the same as it is on the
    website, including the font case, as it is case sensitive.
    """
    markup = InlineKeyboardMarkup(row_width=2)
    locations = [location['location_name'] for location in await db.fetch_value('location_name', 'Locations')]
    for location in locations:
        button = InlineKeyboardButton(location, callback_data=location)
        markup.insert(button)
    return markup


def blog_sub():
    blog_subscribe = InlineKeyboardMarkup(row_width=2)
    blog_subscribe.insert(InlineKeyboardButton(text="Yes", callback_data='yes'))
    blog_subscribe.insert(InlineKeyboardButton(text="No", callback_data='no'))
    return blog_subscribe


def unsubscribe_key():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='❌Unsubscribe')]], resize_keyboard=True, row_width=1)


def admin_start_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    markup.insert(InlineKeyboardButton(text="New category", callback_data='admin_new_category'))
    markup.insert(InlineKeyboardButton(text="Remove category", callback_data='admin_remove_category'))
    markup.insert(InlineKeyboardButton(text="New location", callback_data='admin_new_location'))
    markup.insert(InlineKeyboardButton(text="Remove location", callback_data='admin_remove_location'))
    markup.insert(InlineKeyboardButton(text="Statistics and settings", callback_data='admin_statistics'))
    markup.insert(InlineKeyboardButton(text="Payable posting", callback_data='payable'))
    markup.insert(InlineKeyboardButton(text="Send mass message", callback_data='mass_message'))
    markup.insert(InlineKeyboardButton(text="Send channel message", callback_data='group_message'))
    markup.insert(InlineKeyboardButton(text='Set posting fee', callback_data='set_price'))
    markup.insert(InlineKeyboardButton(text="Back to main", callback_data='admin_main'))
    return markup


async def remove_categories_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    categories = [category['category_name'] for category in await db.fetch_value('category_name', 'Categories')]
    for category in categories:
        markup.insert(InlineKeyboardButton(text=category,
                                           callback_data=f"A{category}"))
    markup.insert(InlineKeyboardButton(text='Back', callback_data='admin_go_back'))
    return markup


async def remove_location_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    locations = [location['location_name'] for location in await db.fetch_value('location_name', 'Locations')]
    for location in locations:
        markup.insert(InlineKeyboardButton(text=location,
                                           callback_data=f"A{location}"))
    markup.insert(InlineKeyboardButton(text='Back', callback_data='admin_go_back'))
    return markup


async def question_category_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    categories = questions_api.get_categories()
    for category in categories:
        markup.insert(InlineKeyboardButton(text=category, callback_data=f"QuestionCategory_{category}"))
    return markup


def question_review_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.insert(InlineKeyboardButton(text='Create post', callback_data="questions_create"))
    markup.insert(InlineKeyboardButton(text='Cancel', callback_data="questions_cancel"))
    return markup


def answer_question_keys(question_id) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.insert(InlineKeyboardButton(text='Respond', callback_data=f'AnswerQuestion_{question_id}'))
    markup.insert(InlineKeyboardButton(text='Cancel', callback_data='finish_state_answers'))
    return markup


def answer_question_direct_keys(question_id) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.insert(InlineKeyboardButton(text='Answer question', callback_data=f'AnswerQuestion_{question_id}'))
    return markup


def feedback_answer_keys(answer_id) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.insert(InlineKeyboardButton(text='Best Answer 🙏', callback_data=f'feedback_thebest_{answer_id}'))
    markup.insert(InlineKeyboardButton(text='Helpful 👍', callback_data=f'feedback_helpful_{answer_id}'))
    markup.insert(InlineKeyboardButton(text='Unhelpful 👎', callback_data=f'feedback_unhelpful_{answer_id}'))
    markup.insert(InlineKeyboardButton(text='Write a comment', callback_data=f'feedback_comment_{answer_id}'))
    return markup


def reply_for_comment_keys(answer_id, user) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.insert(InlineKeyboardButton(text='Reply', callback_data=f'comment_{answer_id}_user_{user}'))
    return markup


def select_question_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.insert(InlineKeyboardButton(text='Select question', callback_data=f'select_detail_question'))
    markup.insert(InlineKeyboardButton(text='Main menu', callback_data=f'dont_select_detail_question'))
    return markup


def get_questions_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.insert(InlineKeyboardButton(text='Answered questions', callback_data='answered_questions'))
    markup.insert(InlineKeyboardButton(text='Unanswered questions', callback_data='unanswered_questions'))
    return markup

