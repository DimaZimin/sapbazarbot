@dp.message_handler(filters.Text(contains=['Unsubscribe']))
async def unsubscribe(message: types.Message):
    """
    Unsubscribe button function
    """
    user_id = message.from_user.id
    db_manager.remove_subscription(user_id)
    db_manager.update_subscription(user_id, status=False)
    logging.info(f'USER ID: {user_id} UNSUSCRIBED')
    await message.answer("You have successfully unsubscribed from job alert", reply_markup=ReplyKeyboardRemove())
    await message.answer("Thank you for choosing our service", reply_markup=start_keys())