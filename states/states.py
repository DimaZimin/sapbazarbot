from aiogram.dispatcher.filters.state import StatesGroup, State


class JobCreation(StatesGroup):

    job_name = State()
    job_category = State()
    job_location = State()
    job_description = State()


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
    contact = State()
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


class StartQuestion(StatesGroup):

    title_state = State()
    content_state = State()
    picture_state = State()
    category_state = State()
    email_state = State()
    review = State()
    send_invoice = State()
    checkout = State()
    payment_paid = State()


class AnswerQuestionState(StatesGroup):

    answer_content = State()
    answer_email = State()


class MyQuestionsState(StatesGroup):

    question_list_state = State()
    select_question_state = State()
    get_answers_state = State()


class AllQuestionsState(StatesGroup):

    select_category_state = State()
    select_question_state = State()
    answer_questions_state = State()
    answer_content_state = State()
    answer_email_state = State()


class CommentState(StatesGroup):

    write_comment_state = State()


class ReplyCommentState(StatesGroup):

    reply_to_state = State()
