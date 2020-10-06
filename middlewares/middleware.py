from aiogram.dispatcher.filters.state import State, StatesGroup


class Form(StatesGroup):
    state = State()


class CreateJob(StatesGroup):
    job_name = State()
    company_name = State()
    job_description = State()
    job_category = State()
    job_category_add = State()
    job_location = State()
    job_location_add = State()
    send_invoice = State()
    checkout = State()
    payment_paid = State()


class Admin(StatesGroup):

    new_category = State()
    new_location = State()
    catch_price = State()


class MassMessage(StatesGroup):

    message_processing = State()


class GroupMessage(StatesGroup):

    message_processing = State()


