"""
This file contains keyboard and callback settings
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from data.config import admins
from loader import db

category_callback = CallbackData('choose_category', 'category')
start_subscription = CallbackData('subscription', 'action')
job_post_callback = CallbackData('job_posting', 'posting')
invoice_callback = CallbackData('send_invoice', 'confirm')
location_callback = CallbackData('choose_location', 'location')
remove_category_callback = CallbackData('remove_category', 'category')

# CATEGORIES = ['SAP ABAP', 'SAP FI', 'SAP BASIS', 'SAP TM',
#               'SAP BW', 'SAP SD', 'SAP BPC', 'SAP HCM',
#               'SAP QM', 'SAP EWM', 'SAP S/4HANA', 'SAP CO', 'SAP GRC', 'Next']


def start_keys(admin_id):
    """
    Inline keyboard that pops up after activating /start command
    """
    markup = InlineKeyboardMarkup(row_width=2)
    markup.insert(InlineKeyboardButton(text="✅ Subscribe", callback_data=start_subscription.new(action='subscribe')))
    markup.insert(InlineKeyboardButton(text="💼 Post a Job", callback_data=job_post_callback.new(posting='start')))
    markup.insert(InlineKeyboardButton(text="✉️ Contact", url='https://sapbazar.com/more/contactus'))
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


async def job_categories() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    categories = [category['category_name'] for category in await db.fetch_value('category_name', 'Categories')]
    for category in categories:
        button = InlineKeyboardButton(category, callback_data=job_post_callback.new(posting=category))
        markup.insert(button)
    markup.insert(InlineKeyboardButton('Add new category',
                                       callback_data='add_cat'))
    return markup


async def job_locations() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    locations = [location['location_name'] for location in await db.fetch_value('location_name', 'Locations')]
    for location in locations:
        button = InlineKeyboardButton(location, callback_data=location)
        markup.insert(button)
    markup.insert(InlineKeyboardButton('Add new location',
                                       callback_data='add_loc'))
    return markup


def confirmation_keys() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [InlineKeyboardButton('Confirm', callback_data=invoice_callback.new(confirm='yes'))],
            [InlineKeyboardButton('Cancel', callback_data=invoice_callback.new(confirm='no'))]])


async def localization_keys() -> InlineKeyboardMarkup:
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
    return InlineKeyboardMarkup().insert(InlineKeyboardButton(text='Unsubscribe', callback_data='unsubscribe'))


def admin_start_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    markup.insert(InlineKeyboardButton(text="New category", callback_data='admin_new_category'))
    markup.insert(InlineKeyboardButton(text="Remove category", callback_data='admin_remove_category'))
    markup.insert(InlineKeyboardButton(text="New location", callback_data='admin_new_location'))
    markup.insert(InlineKeyboardButton(text="Remove location", callback_data='admin_remove_location'))
    markup.insert(InlineKeyboardButton(text="Statistics", callback_data='admin_statistics'))
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

def unsubscribe_blog_keys() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.insert(InlineKeyboardButton(text='Unsubscribe', callback_data='blog_unsubscribe'))
    return markup
