import asyncio
import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup,FSInputFile
from peewee import *
from aiogram.types import CallbackQuery
from models import food_sdb
from PIL import Image
from aiogram.types import InputFile


#Необходимое для работы
admins_bot_token = '5810134947:AAH4m8VTGhmDtzWbIMwkG-5Z3_Jiugz6DJI'
bot = Bot(token=admins_bot_token)
dp = Dispatcher(bot=bot)

con = SqliteDatabase('food_service_db.db')

super_user_id = 1080347509
chat_admins_id = -1002069865260

admins = food_sdb.get_records('admin')

admins_check_2 = {}
admins_check = {}
who_add_info = []
user_update_black_list = []
all_dish = [i['name'] for i in food_sdb.get_records('good')]

# Добавляем категории в списки и с ними работаем
gd = food_sdb.get_records('good')
gg_beverages = []
gg_main_dish = []
gg_sushi = []
gg_pizzes = []

for i in gd:
    if i['category'] == 'Напитки':
        gg_beverages.append(i)
    elif i['category'] == 'Основные блюда':
        gg_main_dish.append(i)
    elif i['category'] == 'Пиццы':
        gg_pizzes.append(i)
    elif i['category'] == 'Суши':
        gg_sushi.append(i)

# Кнопки
markup_admins1 = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Назначить администратора")],
    [KeyboardButton(text="Удалить администратора")]
])

markup_admins2 = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Список активных заказов")],
    [KeyboardButton(text="Редактирование меню блюд")],
    [KeyboardButton(text="Просмотр и удаление непотребных комментариев")],
    [KeyboardButton(text="список клиентов")],
    [KeyboardButton(text="список говнюков (чс для пользователей)")],
    [KeyboardButton(text="стоп блюда")]
])

markup_consent = InlineKeyboardButton(text='ДА',callback_data='YES')
markup_consent2 = InlineKeyboardButton(text='НЕТ',callback_data='NO')
keyboard_consent = InlineKeyboardMarkup(inline_keyboard=[[markup_consent],[markup_consent2]])

markup_black_list = InlineKeyboardButton(text='Добавить в ЧС', callback_data='black_list')
keyboard_black_list = InlineKeyboardMarkup(inline_keyboard=[[markup_black_list]])

markup_delete_from_black_list = InlineKeyboardButton(text='Убрать из ЧС', callback_data='delete_from_black_list')
keyboard_delete_from_black_list = InlineKeyboardMarkup(inline_keyboard=[[markup_delete_from_black_list]])

markup_delete = InlineKeyboardButton(text='удалить', callback_data='-')
keyboard_delete = InlineKeyboardMarkup(inline_keyboard=[[markup_delete]])

markup_stop = InlineKeyboardButton(text = 'Поставить блюдо на стоп',callback_data = 'stop')
markup_remove_from_stop = InlineKeyboardButton(text = 'Убрать стоп у блюда',callback_data = 'remove_from_stop')
keyboard_stop = InlineKeyboardMarkup(inline_keyboard=[[markup_stop],[markup_remove_from_stop]])

markup_remove = InlineKeyboardButton(text='Убрать стоп',callback_data='--')
keyboard_remove = InlineKeyboardMarkup(inline_keyboard=[[markup_remove]])

markup_beverages = InlineKeyboardButton(text='Напитки',callback_data='beverages')
markup_pizzes = InlineKeyboardButton(text='Пиццы',callback_data='pizzes')
markup_sushi = InlineKeyboardButton(text='Суши',callback_data='sushi')
markup_main_dishes = InlineKeyboardButton(text='Основные блюда',callback_data='main_dishes')
keyboard_creat_menu = InlineKeyboardMarkup(inline_keyboard=[[markup_beverages,markup_sushi],[markup_pizzes,markup_main_dishes]])

markup_creat = InlineKeyboardButton(text='Изменить',callback_data='creat')
keyboard_creat = InlineKeyboardMarkup(inline_keyboard=[[markup_creat]])

markup_beverages_comment = InlineKeyboardButton(text='Напитки',callback_data='beverages_comment')
markup_pizzes_comment = InlineKeyboardButton(text='Пиццы',callback_data='pizzes_comment')
markup_sushi_comment = InlineKeyboardButton(text='Суши',callback_data='sushi_comment')
markup_main_dishes_comment = InlineKeyboardButton(text='Основные блюда',callback_data='main_dishes_comment')
keyboard_comment_menu = InlineKeyboardMarkup(inline_keyboard=[[markup_beverages_comment,markup_sushi_comment],[markup_pizzes_comment,markup_main_dishes_comment]])

@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message):
    user_id = message.from_user.id
    admin = next((admin for admin in admins if user_id == admin['user_id']), None)
    if user_id == super_user_id or (admin and admin['level']):
        await message.bot.send_message(chat_id=user_id, text='Привет, Администратор!', reply_markup=markup_admins1)
    elif admin:
        await message.bot.send_message(chat_id=user_id, text='Привет, Администратор!', reply_markup=markup_admins2)
    else:
        await message.answer('Извините, у вас нет прав администратора')

@dp.message()
async def send_echo(message: Message):
    msc = message.text
    user_id = message.from_user.id
    admin = next((admin for admin in admins if user_id == admin['user_id']), None)

    if msc == "Назначить администратора" and (admin is not None or user_id == super_user_id) and message.chat.id != chat_admins_id:
        await message.answer('Перешлите сообщение от пользователя, которого хотите назначить администратором')
        admins_check[user_id] = True

    elif msc != 'Назначить администратора' and msc != "Удалить администратора" and admin is not None and admin['level'] is True or user_id == super_user_id and message.chat.id != chat_admins_id and admins_check.get(user_id, False) == True:
        try:
            name_new_admin = message.forward_from.full_name
            id_new_admin = message.forward_from.id
            who_add_info.append(name_new_admin)
            who_add_info.append(id_new_admin)
            await message.answer(f'Имя пользователя: {name_new_admin}\nID пользователя: {id_new_admin}')
            await message.answer(text='Сделать данного пользователя администратором?', reply_markup=keyboard_consent)
            admins_check[user_id] = False
        except Exception as e:
            print(f"Произошла ошибка при обработке данных пользователя: {e}")
            await message.answer('Произошла ошибка при обработке данных пользователя.')
            admins_check[user_id] = False

    elif msc == 'Удалить администратора' and (admin is not None or user_id == super_user_id) and message.chat.id != chat_admins_id:
        await message.answer(f'Список администраторов 2-го уровня:\n')
        for ad in admins:
            if not ad['level']:
                await message.answer(str(ad['name']), reply_markup=keyboard_delete)

    elif msc == 'список клиентов' and any(admin['user_id'] == user_id and admin['level'] == 0 for admin in admins) and message.chat.id != chat_admins_id:
        users_name = food_sdb.get_records('user')
        await message.answer('Список клиентов:')
        for i in users_name:
            if i['black_list'] == False:
                await message.answer(f"{i['name']} \n телеграм id - {i['tg_id']} \n вк id - {i['vk_id']} \n телефон: {i['phone']}", reply_markup=keyboard_black_list)

    elif msc == 'список говнюков (чс для пользователей)' and any(admin['user_id'] == user_id and not admin['level'] for admin in admins) and message.chat.id != chat_admins_id:
        users_black_list = food_sdb.get_records('user')
        await message.answer('ЧС:')
        for j in users_black_list:
            if j['black_list']:
                await message.answer(f"{j['name']} \n телеграм id - {j['tg_id']} \n вк id - {j['vk_id']} \n телефон: {j['phone']}", reply_markup=keyboard_delete_from_black_list)

    elif msc == 'стоп блюда' and any(admin['user_id'] == user_id and not admin['level'] for admin in admins) and message.chat.id != chat_admins_id:
        await message.answer('Ввыберети действие:',reply_markup=keyboard_stop)

    if admins_check_2 != {} and any(admin['user_id'] == user_id and not admin['level'] for admin in admins):
        if admins_check_2[message.from_user.id] == True and message.text != 'Введите название блюда которое хотите поставить на стоп:' and message.text in all_dish:
            try:
                m_t = message.text
                food_sdb.update_record('good',{'available':False} ,name = m_t)
                await message.answer('Блюдо поставленно на стоп!')
                admins_check_2.clear()
            except:
                await message.answer('Вы ввели неправельное название блюда!')
        else:
            await message.answer('Вы ввели неправельное название блюда!')
            admins_check_2.clear()

    elif msc == 'Список активных заказов' and any(admin['user_id'] == user_id and not admin['level'] for admin in admins) and message.chat.id != chat_admins_id:
        # list_active_order = food_sdb.get_records('order')
        # user_active_order = food_sdb.get_records('user')
        # basket_active_order = food_sdb.get_records('basket')

        # Получаем список активных заказов
        actords = food_sdb.get_all_actorders()

        if actords:
            for ord in actords:
                good_text = ""
                for bask in ord["basket_id"]:
                    print(ord)
                    good = bask["good_id"]
                    good_text += f"Название: {good['name']}\n" \
                                 f"Колличество: {bask['amount']}\n" \
                                 f"Стоимость: {bask['total_price']}\n\n"

                text = f"Номер заказа № {ord['order_number']}\n" \
                       f"Время заказа: {ord['order_time'].strftime('%Y-%m-%d %H-%M')}\n" \
                       f"Время доставки: {ord['delivery_time'].strftime('%Y-%m-%d %H-%M')}\n" \
                       f"Статус: {ord['status']}\n" \
                       f"Способ оплаты: {ord['payment_method']}\n" \
                       f"Товары: \n\n{good_text}\n" \
                       f"Данные заказчика: \n" \
                       f"{ord['user_name']}, {ord['age']} лет\n" \
                       f"{ord['phone']}\n" \
                       f"{ord['delivery_address']}"

                await message.answer(text=text)

        else:
            await message.answer(text="Нет активных заказов.")

        # flag = False

        # for order in list_active_order:
        #     if order['status'] == 'active':
        #         flag = True
        #         user_id = order['user_id']
        #         basket_id = order['basket_id']
        #         user_info = next((user for user in user_active_order if user['id'] == user_id), None)
        #         basket_info = next((basket for basket in basket_active_order if basket['id'] == basket_id), None)
        #         if user_info and basket_info:
        #             await message.answer(f"Имя пользователя: {user_info['name']}\nКорзина: {basket_info['amount'],' ',basket_info['total_price']}")
        #         else:
        #             await message.answer("Нет активных заказов")
        # if flag == False:
        #     await message.answer("Нет активных заказов")

    elif msc == 'Редактирование меню блюд' and any(admin['user_id'] == user_id and not admin['level'] for admin in admins) and message.chat.id != chat_admins_id:
        await message.answer('Выберите категорию, в которой вы хотите внести изменения:',reply_markup=keyboard_creat_menu)

    elif msc == 'Просмотр и удаление непотребных комментариев' and any(admin['user_id'] == user_id and not admin['level'] for admin in admins) and message.chat.id != chat_admins_id:
        await message.answer('Введите категорию, в которой хотите просмотреть комментарии:',reply_markup=keyboard_comment_menu)

    elif not any(admin['user_id'] == user_id for admin in admins) and user_id != super_user_id:
        await message.answer('Не в тот чат ты зашел, воин')
    else:
        pass

@dp.callback_query(F.data == 'YES')
async def process_button_yes(callback: CallbackQuery):
    new_admin = food_sdb.add_record('admin', user_id=who_add_info[1], level=False, name=who_add_info[0])
    if new_admin:
        admins.append(new_admin)
        await callback.message.delete()
        await callback.message.answer(
            text='Пользователь получил права администратора 2-го уровня',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[])
        )
        await callback.answer(
            text='Вы выдали пользователю права администратора',
            show_alert=True
        )
    else:
        callback.answer(text = 'Произошла ошибка')

    if who_add_info:
        who_add_info.clear()

@dp.callback_query(F.data == 'NO')
async def process_button_no(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        text='Пользователь не получил права администратора!',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[])
    )

@dp.callback_query(F.data == '-')
async def admin_delete(callback: CallbackQuery):
    user_id_to_delete = None
    for admin in admins:
        if admin['name'] == callback.message.text:
            user_id_to_delete = admin['user_id']
            admins.remove(admin)
            break

    try:
        food_sdb.delete_all_record('admin',user_id = user_id_to_delete)
        await callback.message.delete()
        await callback.message.answer(
        text='Админ удален!',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[])
    )
    except Exception as e:
        print(f"Список пустой")

@dp.callback_query(F.data == 'black_list')
async def bl(callback: CallbackQuery):
    us_data = callback.message.text
    us = us_data.split('\n')
    us_id_tg = [i for i in us[1] if i.isdigit()]
    us_id_tg = ''.join(us_id_tg)
    us_id_vk = [i for i in us[2] if i.isdigit()]
    us_id_vk = ''.join(us_id_vk)
    try:
        if us_id_tg:
            food_sdb.update_record('user', {'black_list': True}, tg_id=int(us_id_tg))
        elif us_id_vk:
            food_sdb.update_record('user', {'black_list': True}, vk_id=int(us_id_vk))

        await callback.message.delete()
        await callback.message.answer(
            text='Пользователь добавлен в черный список!',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[])
        )
    except Exception:
        print(f"Произошла ошибка")

@dp.callback_query(F.data == 'delete_from_black_list')
async def del_bl(callback: CallbackQuery):
    us_data = callback.message.text
    us = us_data.split('\n')
    us_id_tg = [i for i in us[1] if i.isdigit()]
    us_id_tg = ''.join(us_id_tg)
    us_id_vk = [i for i in us[2] if i.isdigit()]
    us_id_vk = ''.join(us_id_vk)
    try:
        if us_id_tg:
            food_sdb.update_record('user', {'black_list': False}, tg_id=int(us_id_tg))
        elif us_id_vk:
            food_sdb.update_record('user', {'black_list': False}, vk_id=int(us_id_vk))

        await callback.message.delete()
        await callback.message.answer(
            text='Пользователь больше не в ЧС!',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[])
        )
    except Exception:
        print(f"Произошла ошибка")

@dp.callback_query(F.data == 'stop')
async def stop(callback: CallbackQuery):
    admins_check_2[callback.message.chat.id] = True
    await callback.message.answer('Введите название блюда которое хотите поставить на стоп:')

@dp.callback_query(F.data == 'remove_from_stop')
async def stop(callback: CallbackQuery):
    await callback.message.answer('Блюда на стопе:')
    stop_dish = food_sdb.get_records('good')
    for i in stop_dish:
        if i['available'] == False:
            await callback.message.answer(i['name'],reply_markup = keyboard_remove)

@dp.callback_query(F.data == '--')
async def stop(callback: CallbackQuery):
    await callback.message.delete()
    food_sdb.update_record('good',{'available':True} ,name = callback.message.text)

@dp.callback_query(F.data == 'beverages')
async def creat_beverages(callback: CallbackQuery):
    size = (300,300)
    for i in gg_beverages:
        try:
            image_path = i['image']
            image = Image.open(image_path)
            image.thumbnail(size)
        except Exception as e:
            print(f"Ошибка: {e}")

@dp.callback_query(F.data == 'beverages_comment')
async def creat_beverages_comment(callback: CallbackQuery):
    list_markup = []
    for i, beverage in enumerate(gg_beverages):
        callback_data = f'com_{i}'
        markup_comment_button = InlineKeyboardButton(text=beverage['name'], callback_data=callback_data)
        list_markup.append([markup_comment_button])

    keyboard_comment = InlineKeyboardMarkup(inline_keyboard=list_markup)
    await callback.message.answer('Выберете блюда, в котором хотите просмотреть комментарии:', reply_markup=keyboard_comment)

@dp.callback_query(F.data.startswith('com_'))
async def creat_com(callback: CallbackQuery):
    button_data = callback.data
    button_index = int(button_data.split('_')[1])
    selected_beverage = gg_beverages[button_index]
    food_sdb.get_records('goodcomment')


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())