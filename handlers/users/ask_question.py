import logging

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, Message, ContentTypes
from aiogram import types

from filters.filters import QuestionCategories
from keyboards.inline.keyboard import question_category_keys, question_review_keys, start_keys, \
    answer_question_keys
from loader import dp, bot, db, mysql_db, questions_api

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
    logging.info(f'QUESTION MODE: USER ID {user_id} PROVIDES QUESTION TITLE')
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
    logging.info(f'QUESTION MODE: USER ID {user_id} IS PROVIDING QUESTION CONTENT')
    async with state.proxy() as data:
        data["content"] = question_content
    await StartQuestion.category_state.set()
    await bot.send_chat_action(user_id, action='typing')
    await bot.send_message(user_id, 'Please, choose SAP category', reply_markup=await question_category_keys())


@rate_limit(5)
@dp.callback_query_handler(QuestionCategories(), state=StartQuestion.category_state)
async def process_question_category(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    question_category = call.data.split('QuestionCategory_')[1]
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
                                         f"{data['email']}\n\n",
                           reply_markup=question_review_keys())


@dp.callback_query_handler(text=['questions_create', 'questions_cancel'], state=StartQuestion.review)
async def create_question(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    action = call.data
    data = await state.get_data()
    if action == 'questions_create':
        response = await questions_api.create_question(data['email'],
                                                       data['title'],
                                                       data['content'],
                                                       await questions_api.get_category_id(data['category']),
                                                       await questions_api.get_category_tag(data['category']))
        question_id = str(response['responseBody']['postid'])
        external_user_id = str(response['responseBody']['userid'])
        await db.create_question(user_id=user_id,
                                 post_id=question_id,
                                 user_email=data['email'],
                                 external_user_id=external_user_id)
        await state.finish()
        await call.message.edit_reply_markup()
        await bot.send_message(user_id, "Question has been created.", reply_markup=start_keys(user_id))
        users = await db.get_category_subscribers(data['category'])
        for user in users:
            await bot.send_message(user['user_id'], f"Hello. Some user needs an advice on SAP. "
                                                    f"You might be the one who can help.\n\n"
                                                    f"<b>Title:</b>\n{data['title']}\n\n<b>Question:</b>\n{data['content']}",
                                   parse_mode='HTML',
                                   reply_markup=answer_question_keys(question_id))
    else:
        await state.finish()
        await call.message.edit_reply_markup()
        await bot.send_message(user_id, "Main menu", reply_markup=start_keys(user_id))


@rate_limit(5)
@dp.callback_query_handler(Text(startswith='AnswerQuestion_'))
async def answer_question(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    question_id = call.data.split('AnswerQuestion_')[1]
    await AnswerQuestionState.answer_content.set()
    async with state.proxy() as data:
        data["question_id"] = question_id
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, text='Please, write your answer')


@dp.message_handler(state=AnswerQuestionState.answer_content)
async def process_answer_question(message: Message, state: FSMContext):
    user_id = message.chat.id
    answer_content = message.text
    async with state.proxy() as data:
        data["answer_content"] = answer_content
    await AnswerQuestionState.answer_email.set()
    await bot.send_message(user_id, text='Please, provide your e-mail')


@dp.message_handler(state=AnswerQuestionState.answer_email)
async def process_answer_email(message: Message, state: FSMContext):
    user_id = message.chat.id
    email = message.text
    data = await state.get_data()
    content = data['answer_content']
    question_id = data['question_id']
    question_starter_user_id = await db.get_value('questions', 'user_id', 'post_id', question_id)
    question_starter_user_id = question_starter_user_id[0]['user_id']
    await questions_api.write_answer(user=email,
                                     content=content,
                                     post_id=question_id)
    await state.finish()
    question_title = await questions_api.get_question_title(question_id)
    await bot.send_message(question_starter_user_id, text=f"Hi, we have got an answer for your question: "
                                                          f"{question_title}\n"
                                                          f"<b>Answer:</b>\n{content}", parse_mode='HTML')
    await bot.send_message(user_id, 'Your answer has been posted! Thank you.', reply_markup=start_keys(user_id))


