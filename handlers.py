from aiogram.filters import CommandStart
from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import app.keyboard as kb
import app.google_calendar as gc

from config import ADMIN_ID, summ

router = Router()


class Form(StatesGroup):
    summary = State()
    full_name = State()
    group = State()


class Sign(StatesGroup):
    r_type = State()
    sign_choice = State()
    


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f'Привет, {message.from_user.first_name}.\n\nВы можете записаться, посмотреть записи или отменить запись на курсовую работу, ВКР, учебную деятельность.\n', reply_markup=kb.reply_builder(['Курсовая работа', 'ВКР', 'Учебная деятельность', 'Отчетность']))
    else:
        await message.answer(f'Привет, {message.from_user.first_name}.\n\nВы можете записаться, посмотреть записи или отменить запись на курсовую работу, ВКР, учебную деятельность.\n', reply_markup=kb.reply_builder(['Курсовая работа', 'ВКР', 'Учебная деятельность']))
    await state.set_state(Sign.r_type)


@router.message(F.text == 'Отчетность')
async def report(message: Message, state: FSMContext):

    if message.from_user.id != ADMIN_ID:
        await state.set_state(Sign.r_type)
        return
    

    summaries = [i for i in gc.get_summaries_past_30_days() if 'Группа:' in i.get('description', '')]

    if len(summaries) == 0:
        await message.answer('За последние 30 дней не было консультаций.')
        await state.set_state(Sign.r_type)
        return

    text = [f'За последние 30 дней было проведено {len(summaries)} консультаций:\n']

    months = {'01': 'январь',  '02': 'февраль',  '03': 'март',  '04': 'апрель',  '05': 'май',  '06': 'июнь',  '07': 'июль',  '08': 'август',  '09': 'сентябрь',  '10': 'октябрь',  '11': 'ноябрь', '12': 'декабрь',}
    nl = '\n'
    for index, i in enumerate(summaries):
        text.append(f"{index+1}. {i.get('summary')},  Группа: {i.get('description', 'Нет').replace('Группа:', '').split(nl)[0].strip()},  Дата: {i['start']['dateTime'][8:10]} {months.get(i['start']['dateTime'][5:7])} | {i['start']['dateTime'][11:16]}-{i['end']['dateTime'][11:16]}")
    
    await message.answer('\n'.join(text))
    await state.set_state(Sign.r_type)


@router.message(Sign.r_type, F.text.in_(['Курсовая работа', 'ВКР', 'Учебная деятельность']))
async def sign_choice_def(message: Message, state: FSMContext):
    await state.update_data(r_type = summ.get(message.text))
    await message.answer(f'Запишитесь, отмените запись или посмотрите активные записи на {message.text}', reply_markup=kb.reply_builder(['Записаться', 'Отменить запись', 'Активные записи', 'Назад']))
    await state.set_state(Sign.sign_choice)


@router.message(Sign.sign_choice, F.text == 'Назад')
async def sign_back(message: Message, state: FSMContext):
    await message.answer(f'Вы можете записаться, посмотреть записи или отменить запись на курсовую работу, ВКР, учебную деятельность.\n', reply_markup=kb.reply_builder(['Курсовая работа', 'ВКР', 'Учебная деятельность']))
    await state.set_state(Sign.r_type)


@router.message(Sign.sign_choice, F.text == 'Записаться')
async def sign_start(message: Message, state: FSMContext):
    data = await state.get_data()
    summaries = [i for i in gc.get_summaries() if i.get('summary', '').lower() == data.get('r_type', '').lower()]

    if not summaries:
        await message.answer('Нет свободных консультаций')
        return
    
    months = {'01': 'январь',  '02': 'февраль',  '03': 'март',  '04': 'апрель',  '05': 'май',  '06': 'июнь',  '07': 'июль',  '08': 'август',  '09': 'сентябрь',  '10': 'октябрь',  '11': 'ноябрь', '12': 'декабрь',}

    s_buttons = dict(zip([f"{i['start']['dateTime'][8:10]} {months.get(i['start']['dateTime'][5:7])} | {i['start']['dateTime'][11:16]}-{i['end']['dateTime'][11:16]}" for i in summaries], [f"s_{str(i['id'])},{i['start']['dateTime'][8:10]} {months.get(i['start']['dateTime'][5:7])} | {i['start']['dateTime'][11:16]}-{i['end']['dateTime'][11:16]}" for i in summaries]))
    await message.answer('Выберите свободную консультацию:', reply_markup=kb.inline_builder(s_buttons))


@router.message(Sign.sign_choice, F.text == 'Отменить запись') 
async def cancel(message: Message, state: FSMContext):
    data = await state.get_data()

    summaries = [i for i in gc.get_summaries(time_delta=True) if str(message.from_user.id) in i.get('description', '') and data.get('r_type').lower() == i.get('summary')[-3:].lower().strip().lower()]

    months ={'01': 'январь',  '02': 'февраль',  '03': 'март',  '04': 'апрель',  '05': 'май',  '06': 'июнь',  '07': 'июль',  '08': 'август',  '09': 'сентябрь',  '10': 'октябрь',  '11': 'ноябрь', '12': 'декабрь',}

    s_buttons = dict(zip([f"{i['start']['dateTime'][8:10]} {months.get(i['start']['dateTime'][5:7])} | {i['start']['dateTime'][11:16]}-{i['end']['dateTime'][11:16]}" for i in summaries], [f"c_{str(i['id'])}" for i in summaries]))
    if not s_buttons:
        await message.answer('Нет консультаций для отмены')
        return
    
    await message.answer('Выберите запись:', reply_markup=kb.inline_builder(s_buttons))


@router.message(Sign.sign_choice, F.text == 'Активные записи')
async def active_entries(message: Message, state: FSMContext):
    data = await state.get_data()

    summaries = [i for i in gc.get_summaries() if str(message.from_user.id) in i.get('description', '') and data.get('r_type').lower() == i.get('summary')[-3:].lower().strip()]

    months ={'01': 'январь',  '02': 'февраль',  '03': 'март',  '04': 'апрель',  '05': 'май',  '06': 'июнь',  '07': 'июль',  '08': 'август',  '09': 'сентябрь',  '10': 'октябрь',  '11': 'ноябрь', '12': 'декабрь',}

    
    s_list = [f"{i['start']['dateTime'][8:10]} {months.get(i['start']['dateTime'][5:7])} | {i['start']['dateTime'][11:16]}-{i['end']['dateTime'][11:16]}" for i in summaries ]
    if not s_list:
        await message.answer('Нет активных записей')
        return
    
    await message.answer('Активные записи:\n\n∙ ' + "\n∙ ".join(s_list))


@router.message(Form.full_name, F.text)
async def sign_group(message: Message, state: FSMContext):
    await state.update_data(full_name = message.text)
    await state.set_state(Form.group)
    await message.answer('Введите вашу группу')


@router.message(Form.group, F.text)
async def sign_confirm(message: Message, state: FSMContext):
    await state.update_data(group = message.text)
    data = await state.get_data()
    await state.set_state(Form.summary)
    buttons = {'Подтвердить ✔': 'confirm', 'Отменить ❌': 'cancel'}
    await message.answer(f'''Подтвердите запись:
                         
∙ Имя: {data["full_name"]}
∙ Группа: {data["group"]}
∙ Время: {data["summary_time"]}
''', reply_markup=kb.inline_builder(buttons))



@router.callback_query(F.data.startswith('confirm'))
async def create_sign(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    gc.update_summary(data, callback.from_user.id)
    await callback.message.answer('Запись создана')
    await callback.message.delete()
    await callback.message.answer(f'Вы можете записаться, посмотреть записи или отменить запись на курсовую работу, ВКР, учебную деятельность.\n', reply_markup=kb.reply_builder(['Курсовая работа', 'ВКР', 'Учебная деятельность']))
    await state.set_state(Sign.r_type)


@router.callback_query(F.data.startswith('cancel'))
async def cancel_sign(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Запись отменена')
    await callback.message.delete()
    await callback.message.answer(f'Вы можете записаться, посмотреть записи или отменить запись на курсовую работу, ВКР, учебную деятельность.\n', reply_markup=kb.reply_builder(['Курсовая работа', 'ВКР', 'Учебная деятельность']))
    await state.set_state(Sign.r_type)


@router.callback_query(F.data.startswith('s_'))
async def choice_sign(callback: CallbackQuery, state: FSMContext):
    s_id = callback.data.replace('s_', '')
    await state.update_data(summary_id = s_id.split(',')[0])
    await state.update_data(summary_time = s_id.split(',')[1])
    await state.set_state(Form.full_name)
    await callback.message.answer('Введите ваше имя и фамилию')
    await callback.message.delete()


@router.callback_query(F.data.startswith('c_'))
async def choice_cancel_sign(callback: CallbackQuery, state: FSMContext, bot: Bot):
    s_id = callback.data.replace('c_', '')
    data = await state.get_data()
    data['summary_id'] = s_id.split(',')[0]
    gc.update_summary(data, callback.from_user.id, is_occupied=False)


    await callback.message.answer('Запись отменена')
    await callback.message.delete()
    await callback.message.answer(f'Вы можете записаться, посмотреть записи или отменить запись на курсовую работу, ВКР, УД.', reply_markup=kb.reply_builder(['Курсовая работа', 'ВКР', 'Учебная деятельность']))

    try:
        await bot.send_message(ADMIN_ID, f"Отменена запись по {data.get('r_type')} на {data.get('summary_time')}.")
    except:
        print('Ошибка: Преподавателю нужно нажать /start в боте, чтобы бот мог присылать ему сообщения')
    await state.set_state(Sign.r_type)

