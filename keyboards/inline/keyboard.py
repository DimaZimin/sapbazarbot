"""
This file contains keyboard and callback settings
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

category_callback = CallbackData('choose_category', 'category')
start_subscription = CallbackData('subscription', 'action')
job_post_callback = CallbackData('job_posting', 'posting')
invoice_callback = CallbackData('send_invoice', 'confirm')
location_callback = CallbackData('choose_location', 'location')

# You can add new category here
CATEGORIES = ['SAP ABAP', 'SAP FI', 'SAP BASIS', 'SAP TM',
              'SAP BW', 'SAP SD', 'SAP BPC', 'SAP HCM',
              'SAP QM', 'SAP EWM', 'SAP S/4HANA', 'SAP CO', 'SAP GRC', 'Next']

# Locations can be added here
LOCATIONS = ['Moscow', 'Saint Petersburg', 'Russia', 'Germany', 'Berlin', 'Wroclaw', 'Remote']


def start_keys():
    """
    Inline keyboard that pops up after activating /start command
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅Subscribe", callback_data=start_subscription.new(action='next'))],
            [InlineKeyboardButton(text="💼Post a Job", callback_data=job_post_callback.new(posting='start'))],
            [InlineKeyboardButton(text="✉️Contact", url='https://sapbazar.com/more/contactus')]])


def category_keys() -> InlineKeyboardMarkup:
    """
    Inline keyboard that includes all available categories. This keyboard pops up after pressing "Subscribe" button.
    CATEGORIES can be expanded by adding a category name to CATEGORY list namespace.
    Make sure that added category is exactly the same as it is on the website, including the font case,
    as it is case sensitive.
    !!!IMPORTANT!!! DO NOT REMOVE 'Next' at the end of the list. Keep it there for convenience!!!
    """
    markup = InlineKeyboardMarkup()
    for category in CATEGORIES:
        markup.add(InlineKeyboardButton(category, callback_data=category_callback.new(category=category)))
    return markup


def job_categories() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    for category in CATEGORIES[:-1]:
        markup.add(InlineKeyboardButton(category, callback_data=job_post_callback.new(posting=category)))
    return markup


def job_locations() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    for location in LOCATIONS:
        markup.add(InlineKeyboardButton(location, callback_data=job_post_callback.new(posting=location)))
    return markup


def confirmation_keys() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [InlineKeyboardButton('Confirm', callback_data=invoice_callback.new(confirm='yes'))],
            [InlineKeyboardButton('Cancel', callback_data=invoice_callback.new(confirm='no'))]])


def localization_keys() -> InlineKeyboardMarkup:
    """
    Inline keyboard associated with locations and cities included in LOCATIONS list namespace.
    You can add new locations to LOCATIONS namespace. Make sure that added location is exactly the same as it is on the
    website, including the font case, as it is case sensitive.
    """
    markup = InlineKeyboardMarkup()
    for loc in LOCATIONS:
        markup.add(InlineKeyboardButton(loc, callback_data=location_callback.new(location=loc)))
    return markup


unsubscribe_key = ReplyKeyboardMarkup(row_width=3).row(KeyboardButton(text='🚫 Unsubscribe'))
