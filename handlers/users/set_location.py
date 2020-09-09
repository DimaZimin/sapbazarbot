@dp.callback_query_handler(location_callback.filter(location=LOCATIONS), state=Form.state)
async def set_location(call: CallbackQuery, state: FSMContext):
    """
    Callback query catches name of location. Locations are stored in keyboard.py LOCATIONS variable.
    """
    await call.answer(cache_time=60)
    callback_data = (call.message.text, call.message.chat.id)
    logging.info(f'call = {callback_data[0]}\tchat id: {callback_data[1]}')
    user_id = call.from_user.id
    location = location_callback.parse(call.data)['location']
    db_manager.update_location(user_id=user_id, location=location)
    logging.info(f'LOCATION UPDATED: {location} FOR USER ID: {user_id}')
    await state.finish()
    await call.message.edit_reply_markup()
    await call.message.answer(f'{location} location has been chosen. '
                              f'You have successfully subscribed for job alert!',
                              reply_markup=unsubscribe_key)