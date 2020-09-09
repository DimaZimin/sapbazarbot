



@dp.callback_query_handler(category_callback.filter(category=CATEGORIES))
async def add_category(call: CallbackQuery):
    """

    Callback query handler catches name of a category. Categories are stored in keyboard.py CATEGORIES variable.
    """
    await call.answer(cache_time=60)
    if call.data == 'choose_category:Next' and db_manager.get_user_categories(call.from_user.id):
        logging.info(f'CHAT ID: {call.from_user.id} CHOOSING LOCATION')
        await Form.state.set()
        await call.message.edit_reply_markup()
        await call.message.answer('Please, choose your location', reply_markup=localization_keys())
    elif call.data == 'choose_category:Next' and not db_manager.get_user_categories(call.from_user.id):
        logging.info(f'EMPTY CATEGORY\tCHAT ID: {call.from_user.id}')
        await call.message.edit_reply_markup()
        await call.message.answer(f'You have not chosen any category yet. First, choose a category '
                                  f'and then press Next button',
                                  reply_markup=category_keys())
    else:
        callback_data = (call.message.text, call.message.chat.id)
        logging.info(f'CATEGORY UPDATE: {callback_data[1]}')
        user_id = call.from_user.id
        category = category_callback.parse(call.data)['category']
        db_manager.add_user_category(user_id=user_id, category=category)
        logging.info(f'CATEGORY UPDATED: {category} FOR USER ID: {user_id}')
        await call.message.edit_reply_markup()
        await call.message.answer(f'{category} category has been added. Choose another category or press Next',
                                  reply_markup=category_keys())
