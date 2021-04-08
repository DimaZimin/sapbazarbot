import asyncio
import logging
from collections import defaultdict

from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, Message
from aiogram.utils.exceptions import BotBlocked, UserDeactivated, ChatNotFound, RetryAfter, TelegramAPIError

from keyboards.inline.keyboard import start_keys, select_question_keys, get_questions_keys, answer_question_keys, \
    feedback_answer_keys, answer_question_direct_keys
from loader import dp, bot, db, questions_api, json_answers
from states.states import MyQuestionsState, AllQuestionsState
from utils.misc import rate_limit
from aiogram.dispatcher import FSMContext


@rate_limit(7)
@dp.callback_query_handler(text='my_questions')
async def start_my_questions(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    logging.info(f'MY QUESTIONS MODE: USER ID {user_id} LISTS QUESTIONS')
    user_mail = await db.get_user_question_mail(user_id)
    if user_mail:
        if user_mail == 1:
            user_questions = await questions_api.get_user_questions(user_mail[0]['user_mail'])
        else:
            user_questions = await questions_api.get_user_questions(user_mail[-1]['user_mail'])
        if user_questions:
            user_question_titles = [
               ". ".join((str(index), title)) for index, title in enumerate([
                    question['title'] for question in user_questions], start=1)
            ]
            string_titles = "\n".join(user_question_titles)
            await call.message.edit_reply_markup()
            await bot.send_message(user_id, text=f'Your questions:\n{string_titles}',
                                   reply_markup=select_question_keys())
            async with state.proxy() as data:
                data["questions"] = [(index, post_id['postid']) for index, post_id in enumerate(user_questions, start=1)]
            await MyQuestionsState.question_list_state.set()
    elif not user_mail:
        await call.message.edit_reply_markup()
        await bot.send_message(user_id, 'You have no questions', reply_markup=start_keys(user_id))


@rate_limit(5)
@dp.callback_query_handler(text='select_detail_question', state=MyQuestionsState.question_list_state)
async def select_question(call: CallbackQuery):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    await call.message.edit_reply_markup()
    await MyQuestionsState.select_question_state.set()
    await bot.send_message(user_id, 'Please, provide question number')


@dp.message_handler(lambda message: not message.text.isdigit(), state=MyQuestionsState.select_question_state)
async def render_question_detail_error(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await bot.send_message(user_id, text="Sorry mate, that's not, what I expect. Please type a question number")


@dp.message_handler(lambda message: message.text.isdigit(), state=MyQuestionsState.select_question_state)
async def render_question_detail(message: Message, state: FSMContext):
    user_id = message.from_user.id
    selected_question = int(message.text)
    data = await state.get_data()
    question_indexes = list(map(lambda x: x[0], data['questions']))
    if selected_question in question_indexes:
        post_id = list(filter(lambda x: x[0] == selected_question, data['questions']))[0][1]
        response = await questions_api.get_detailed_question(post_id)
        answers = response['responseBody'].get('answers')
        if answers:
            answers_content = 'Answers:\n' + "\n".join(
                [
                    ". ".join((str(index), value)) for index, value in enumerate([item['content'] for item in answers],
                                                                                 start=1)
                ]
            )
        else:
            answers_content = 'No answers'
        await state.finish()
        await bot.send_message(user_id, text=answers_content, reply_markup=start_keys(user_id))
    else:
        await state.finish()
        await bot.send_message(user_id, text='Wrong index!', reply_markup=start_keys(user_id))


@dp.callback_query_handler(text='dont_select_detail_question', state=MyQuestionsState.question_list_state)
async def dont_select_question(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    await state.finish()
    await bot.send_message(user_id, text='Welcome!', reply_markup=start_keys(user_id))


@dp.callback_query_handler(text='all_questions')
async def all_questions_starter(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    await AllQuestionsState.select_question_state.set()
    async with state.proxy() as data:
        data['questions'] = questions_api.get_all_questions()
        data['answers'] = await questions_api.get_answers()
    question_answers = [q['questid'] for q in data['answers']]
    data_to_send = "\n".join(
        [f"{index}. {question['title']}.\nAnswers: {question_answers.count(question['postid'])}\n\n"
         for index, question in enumerate(data['questions'], start=1)]
    )
    await bot.send_message(user_id, text="Please specify question number\n\n" + data_to_send)


@dp.message_handler(lambda message: message.text.isdigit() and message.text != '0',
                    state=AllQuestionsState.select_question_state)
async def all_questions_detail(message: Message, state: FSMContext):
    user_id = message.from_user.id
    selected_question = int(message.text) - 1
    data = await state.get_data()
    question = data['questions'][selected_question]
    question_id = question['postid']
    question_content = question['content']
    detailed_query = await questions_api.get_detailed_question(question['postid'])
    try:
        answers = "\n=======\n".join([answer['content'] for answer in detailed_query['answers']])
    except KeyError:
        answers = "No answers yet"
    await AllQuestionsState.answer_questions_state.set()
    await bot.send_message(user_id,
                           text=f"<b>Question content</b>:\n{question_content}\n\n<b>Answers:</b>\n=======\n{answers}",
                           parse_mode="HTML", reply_markup=answer_question_keys(question_id))


@rate_limit(5)
@dp.callback_query_handler(text="finish_state_answers", state=AllQuestionsState.answer_questions_state)
async def answer_question_cancel(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    await state.finish()
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, "Hello back!", reply_markup=start_keys(user_id))


@rate_limit(5)
@dp.callback_query_handler(Text(startswith='AnswerQuestion_'), state=AllQuestionsState.answer_questions_state)
async def answer_question(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    user_id = call.from_user.id
    question_id = call.data.split('AnswerQuestion_')[1]
    await AllQuestionsState.answer_content_state.set()
    async with state.proxy() as data:
        data["question_id"] = question_id
    await call.message.edit_reply_markup()
    await bot.send_message(user_id, text='Please, write your answer')


@dp.message_handler(state=AllQuestionsState.answer_content_state)
async def process_answer_question(message: Message, state: FSMContext):
    user_id = message.chat.id
    answer_content = message.text
    logging.info(f'QUESTION MODE: USER ID {user_id} PROCESS ANSWER')
    email = user_id
    data = await state.get_data()
    data["answer_content"] = answer_content
    content = data['answer_content']
    question_id = data['question_id']
    await questions_api.write_answer(user=email, content=content, post_id=question_id)
    await state.finish()
    await bot.send_message(user_id, 'Your answer has been posted! Thank you.', reply_markup=start_keys(user_id))


@dp.message_handler(lambda message: not message.text.isdigit() or message.text == '0', state=AllQuestionsState.select_question_state)
async def all_questions_detail_exception(message: Message):
    user_id = message.from_user.id
    await bot.send_message(user_id, text="Sorry mate, that's not, what I expect. Please type a question number")


async def check_new_answers_task(wait):
    while True:
        await asyncio.sleep(wait)
        new_answers = await questions_api.is_new_answers(json_answers)
        logging.info("NEW ANSWERS TASK PERFORMS")
        if new_answers and isinstance(new_answers, list):
            logging.info(f"NEW ANSWERS {new_answers}")
            for answer in new_answers:
                question_id = answer['questid']
                logging.info(f"QUESTION ID {question_id}")
                user_id = await db.select_user_by_post_id(question_id)
                logging.info(f"USER ID {user_id}")
                if user_id:
                    logging.info(f"USER IDENTIFIED")
                    detailed_question = await questions_api.get_detailed_question(question_id)
                    logging.info(f"DETAILED QUESTION {detailed_question}")
                    try:
                        answer_content = detailed_question.get('answers')[-1]['content']
                        logging.info(f"ANSWER CONTENT {answer_content}")
                    except TypeError or KeyError:
                        answer_content = None
                    if answer_content:
                        logging.info(f"ANSWER IS SENDING TO USER")
                        question_title = detailed_question.get('question')[0]['title']
                        try:
                            await bot.send_message(user_id,
                                                   text=f"Hi! You have got a new answer "
                                                        f"for your question {question_title}:\n\n"
                                                        f"{answer_content}")
                        except BotBlocked or UserDeactivated:
                            logging.info(f"ANSWER NOT SENT. BOT BLOCKED OR USER DEACTIVATED.")
                            pass
        else:
            logging.info("NO NEW ANSWERS")


async def send_questions_message(user_id: int, text: str, question, disable_notification: bool = False) -> bool:
    """
    Safe messages sender
    :param question:
    :param user_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification, reply_markup=answer_question_direct_keys(question))
    except BotBlocked:
        logging.error(f"Target [ID:{user_id}]: blocked by user")
    except ChatNotFound:
        logging.error(f"Target [ID:{user_id}]: invalid user ID")
    except RetryAfter as e:
        logging.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_questions_message(user_id, text)  # Recursive call
    except UserDeactivated:
        logging.error(f"Target [ID:{user_id}]: user is deactivated")
    except TelegramAPIError:
        logging.exception(f"Target [ID:{user_id}]: failed")
    else:
        logging.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def get_unanswered_questions():
    all_questions = questions_api.get_all_questions()
    answered_questions = set([post.get('questid') for post in await questions_api.get_answers()])
    unanswered = [(i.get('category'), i.get('postid'), i.get('content')) for i in list(all_questions) if
                  i.get('postid') not in list(answered_questions)]

    return unanswered


async def unanswered_questions_task_users(wait_time):
    while True:
        logging.info("UNANSWERED QUESTION - USERS TASK")
        unanswered = await get_unanswered_questions()
        unanswered_by_cat = defaultdict(list)
        unanswered_by_id = dict()
        for category, question, content in unanswered:
            unanswered_by_cat[category].append(question)
            unanswered_by_id[question] = content
        for cat, questions in unanswered_by_cat.items():
            users = [u.get('user_id') for u in await db.select_category_users(cat)]
            if users:
                count = 0
                try:
                    for user in users:
                        for q in questions:
                            text = f"<b>Hello, someone needs your help. Please, answer the question below, " \
                                   f"if you can.</b>\n\n{unanswered_by_id[q]}"
                            if await send_questions_message(int(user), text=text, question=q):
                                count += 1
                            await asyncio.sleep(.1)
                finally:
                    logging.info(f"{count} messages sent")
        await asyncio.sleep(wait_time)


async def unanswered_questions_task_group(wait_time):
    while True:
        unanswered = await get_unanswered_questions()

        unanswered_by_cat = defaultdict(list)
        unanswered_by_id = dict()

        for category, question, content in unanswered:
            unanswered_by_cat[category].append(question)
            unanswered_by_id[question] = content

        text_to_channel = []
        for cat, quest in unanswered_by_cat.items():
            text_to_channel.append(f"\n<b>{cat}:</b>\n\n")
            url_string = "".join([f"https://qa.sapbazar.com/{quest_id}/\n" for quest_id in quest])
            text_to_channel.append(url_string)
        text_to_channel = "Dear Gurus, please help our colleagues resolve SAP challenges\n\n" + "".join(text_to_channel)
        await bot.send_message(chat_id='@ivankaim', text=text_to_channel)
        await asyncio.sleep(wait_time)
