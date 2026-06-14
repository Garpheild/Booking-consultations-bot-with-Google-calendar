from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def reply_builder(buttons: list):
    builder = ReplyKeyboardBuilder()
    
    for item in buttons:
        builder.button(text=item)

    return builder.as_markup()


def inline_builder(buttons: dict):
    builder = InlineKeyboardBuilder()
    
    for k, v in buttons.items():
        builder.button(text=k, callback_data=v)

    builder.adjust(*([1]*len(buttons)))
    return builder.as_markup()

