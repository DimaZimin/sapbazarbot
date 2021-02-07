import logging

from aiogram.types import CallbackQuery, Message

from keyboards.inline.keyboard import start_keys, select_question_keys
from loader import dp, bot, db, questions_api
from states.states import MyQuestionsState
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














