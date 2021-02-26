import base64
import io
import logging

import requests
from PIL import Image
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, Message
from aiogram.utils.exceptions import BotBlocked
from data.config import BOT_TOKEN
from filters.filters import QuestionCategories
from keyboards.inline.keyboard import question_category_keys, question_review_keys, start_keys, \
    answer_question_keys, feedback_answer_keys
from loader import dp, bot, db, questions_api

from states.states import StartQuestion, AnswerQuestionState
from utils.misc import rate_limit


@rate_limit(5)
@dp.callback_query_handler(text='ask_question')
async def start_question(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    logging.info(f'QUESTION MODE: USER ID {user_id} STARTED QUESTION CREATION')
    await StartQuestion.title_state.set()
    await bot.send_message(user_id, 'Please, type your question title')


@rate_limit(5)
@dp.message_handler(state=StartQuestion.title_state)
async def process_question_title(message: Message, state: FSMContext):
    user_id = message.chat.id
    question_title = message.text
    logging.info(f'QUESTION MODE: USER ID {user_id} PROVIDED QUESTION TITLE')
    async with state.proxy() as data:
        data["title"] = question_title
    await StartQuestion.content_state.set()
    await bot.send_chat_action(user_id, action='typing')
    await bot.send_message(user_id, 'Please, type question content')


@rate_limit(5)
@dp.message_handler(state=StartQuestion.content_state)
async def process_question_content(message: Message, state: FSMContext):
    user_id = message.chat.id
    question_content = message.text
    logging.info(f'QUESTION MODE: USER ID {user_id} PROVIDED QUESTION CONTENT')
    async with state.proxy() as data:
        data["content"] = question_content
    await StartQuestion.picture_state.set()
    await bot.send_chat_action(user_id, action='typing')
    await bot.send_message(user_id, "Now, you can attach a screenshot if needed. "
                                    "If no need, type any text to proceed.",
                           reply_markup=None)


async def get_image_url(image_id):
    bot_token = BOT_TOKEN
    link_to_image_info = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={image_id}"
    response = requests.request("GET", link_to_image_info)
    file_path = response.json()['result']['file_path']
    file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    return file_url


async def image_from_url_to_base64(image_link):
    image = Image.open(requests.get(image_link, stream=True).raw)
    buf = io.BytesIO()
    image.save(buf, format='JPEG')
    bytes_image = buf.getvalue()
    string = base64.b64encode(bytes_image)
    string = str(string)[1:]
    return string


@rate_limit(5)
@dp.message_handler(state=StartQuestion.picture_state, content_types=[types.ContentType.PHOTO, types.ContentType.TEXT])
async def process_picture(message: Message, state: FSMContext):
    user_id = message.chat.id
    try:
        image_id = message.photo[-1].file_id
    except IndexError:
        image_id = None
    if image_id:
        await bot.send_message(user_id, message.photo[-1].file_id)
        image_url = await get_image_url(image_id)
        image_base_64 = await image_from_url_to_base64(image_url)
        saved_image_link = await questions_api.get_image_internal_link(image_base_64)
        async with state.proxy() as data:
            data["image_url"] = saved_image_link
    else:
        async with state.proxy() as data:
            data["image_url"] = None
    await StartQuestion.category_state.set()
    await bot.send_chat_action(user_id, action='typing')
    await bot.send_message(user_id, 'Please, choose a category', reply_markup=await question_category_keys())


async def check_if_string_has_sap(string):
    if string.startswith('SAP'):
        return string
    else:
        if string == 'success factors':
            string = 'SAP SuccessFactors'
        elif string == 'S/4 HANA':
            string = 'SAP S/4HANA'
        return string


@rate_limit(5)
@dp.callback_query_handler(QuestionCategories(), state=StartQuestion.category_state)
async def process_question_category(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    question_category = call.data.split('QuestionCategory_')[1]
    logging.info(f'QUESTION MODE: USER ID {user_id} SELECTED QUESTION CATEGORY {question_category}')
    async with state.proxy() as data:
        data["category"] = question_category
    await StartQuestion.email_state.set()
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, 'Please provide your mail')


@rate_limit(5)
@dp.message_handler(state=StartQuestion.email_state)
async def process_question_content(message: Message, state: FSMContext):
    user_id = message.chat.id
    email = message.text
    logging.info(f'QUESTION MODE: USER ID {user_id} IS PROVIDING EMAIL')
    async with state.proxy() as data:
        data["email"] = email
    await StartQuestion.review.set()
    await bot.send_chat_action(user_id, action='typing')
    await bot.send_message(user_id, text=f"Please review your question post:\n\n"
                                         f"<b>Question title</b>:\n"
                                         f"{data['title']}\n\n"
                                         f"<b>Question content</b>:\n"
                                         f"{data['content']}\n\n"
                                         f"<b>Category:</b>\n"
                                         f"{data['category']}\n\n"
                                         f"<b>E-mail</b>:\n"
                                         f"{data['email']}\n"
                                         f"Attached screen:\n"
                                         f"{data['image_url']}\n\n",
                           reply_markup=question_review_keys())


@dp.callback_query_handler(text=['questions_create', 'questions_cancel'], state=StartQuestion.review)
async def create_question(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    action = call.data
    data = await state.get_data()
    if action == 'questions_create':
        logging.info(f'QUESTION MODE: USER ID {user_id} APPROVES QUESTION')
        response = await questions_api.create_question(data['email'],
                                                       data['title'],
                                                       data['content'],
                                                       await questions_api.get_category_id(data['category']),
                                                       await questions_api.get_category_tag(data['category']),
                                                       photo=data['image_url'])
        question_id = str(response['responseBody']['postid'])
        external_user_id = str(response['responseBody']['userid'])
        await db.create_question(user_id=user_id,
                                 post_id=question_id,
                                 user_email=data['email'],
                                 external_user_id=external_user_id)
        await state.finish()
        await call.message.edit_reply_markup()
        await bot.send_message(user_id, "Question has been created.", reply_markup=start_keys(user_id))
        users = await db.get_category_subscribers(await check_if_string_has_sap(data['category']))
        users = [user['user_id'] for user in users if user['user_id'] != user_id]
        for user in users:
            try:
                await bot.send_message(user, f"Hello. Some user needs an advice on SAP. "
                                             f"You might be the one who can help.\n\n"
                                             f"<b>Title:</b>\n{data['title']}\n\n<b>Question:</b>\n{data['content']}\n"
                                             f"{data['image_url'] if data['image_url'] else ''}",
                                       parse_mode='HTML',
                                       reply_markup=answer_question_keys(question_id))
            except BotBlocked:
                pass
    else:
        logging.info(f'QUESTION MODE: USER ID {user_id} CANCELS QUESTION CREATION')
        await state.finish()
        await call.message.edit_reply_markup()
        await bot.send_message(user_id, "Main menu", reply_markup=start_keys(user_id))


@rate_limit(5)
@dp.callback_query_handler(Text(startswith='AnswerQuestion_'))
async def answer_question(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    question_id = call.data.split('AnswerQuestion_')[1]
    logging.info(f'QUESTION MODE: USER ID {user_id} ANSWERS ON QUESTION ID {question_id}')
    await AnswerQuestionState.answer_content.set()
    async with state.proxy() as data:
        data["question_id"] = question_id
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, text='Please, write your answer')


@dp.message_handler(state=AnswerQuestionState.answer_content)
async def process_answer_question(message: Message, state: FSMContext):
    user_id = message.chat.id
    answer_content = message.text
    logging.info(f'QUESTION MODE: USER ID {user_id} RESPONDS TO QUESTION')
    async with state.proxy() as data:
        data["answer_content"] = answer_content
    await AnswerQuestionState.answer_email.set()
    await bot.send_message(user_id, text='Please, provide your e-mail')


@dp.message_handler(state=AnswerQuestionState.answer_email)
async def process_answer_email(message: Message, state: FSMContext):
    user_id = message.chat.id
    logging.info(f'QUESTION MODE: USER ID {user_id} PROCESS ANSWER')
    email = message.text
    data = await state.get_data()
    content = data['answer_content']
    question_id = data['question_id']
    question_starter_user_id = await db.get_value('questions', 'user_id', 'post_id', question_id)
    question_starter_user_id = question_starter_user_id[0]['user_id']
    answer_id = await questions_api.write_answer(user=email,
                                                 content=content,
                                                 post_id=question_id)
    await db.create_answer(user_id=user_id, user_mail=email, question_id=question_id, post_id=answer_id)
    await state.finish()
    question_title = await questions_api.get_question_title(question_id)
    try:
        await bot.send_message(question_starter_user_id, text=f"Hi, we have got an answer for your question: "
                                                              f"{question_title}\n"
                                                              f"<b>Answer:</b>\n{content}",
                               parse_mode='HTML', reply_markup=feedback_answer_keys(answer_id))
    except BotBlocked:
        pass
    await bot.send_message(user_id, 'Your answer has been posted! Thank you.', reply_markup=start_keys(user_id))


@dp.callback_query_handler(Text(startswith='feedback_'))
async def give_feedback_helpful(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    feedback = call.data
    answer_id = feedback.split('_')[-1]
    feedback_type = feedback.split('_')[1]
    user_mail = await db.get_user_mail_by_answer_id(answer_id=answer_id)
    user_mail = user_mail[0]['user_mail']
    logging.info(f'QUESTION MODE: USER ID {user_id} GIVES FEEDBACK TO ANSWER {answer_id}')
    if feedback_type == 'helpful':
        await questions_api.vote_answer(user_id=user_mail, post_id=answer_id, vote='1')
        await bot.send_message(user_id, text='You up voted the answer. Thank you.', reply_markup=start_keys(user_id))
        await call.message.edit_reply_markup()
    elif feedback_type == 'unhelpful':
        await questions_api.vote_answer(user_id=user_mail, post_id=answer_id, vote='0')
        await bot.send_message(user_id, text='You down voted the answer. Thank you.', reply_markup=start_keys(user_id))
        await call.message.edit_reply_markup()
    elif feedback_type == 'thebest':
        question_id = await db.get_question_id_by_answer_id(answer_id=answer_id)
        question_id = question_id[0]['question_id']
        await bot.send_message(user_id, text='You set the answer is the best. Thank you.',
                               reply_markup=start_keys(user_id))
        await call.message.edit_reply_markup()
        await questions_api.set_best_answer(question_id=question_id, answer_id=answer_id, user_id=user_mail)
