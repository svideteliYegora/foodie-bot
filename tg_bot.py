import logging
import asyncio
import sys
import json

import aiogram.exceptions
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from PIL import Image
from models import food_sdb
from datetime import datetime as dtm, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler


logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Получаем config данные
with open("resources/config.json", "r") as json_file:
    config = json.load(json_file)

TG_TOKEN = config.get("TG_TOKEN")
SUPER_USER = config.get("SUPER_USER")
ADMINS_CHAT_ID = config.get("ADMINS_CHAT_ID")
SIZE_IMAGE_FOOD_CART = tuple(config.get("SIZE_IMAGE_FOOD_CART"))

# Текст для сообщений бота
with open("resources/messages.json", "r") as json_file:
    data = json.load(json_file)

# Текст для приветсвия и знакомства с пользователем
INTRODUCTION_TEXT = data.get("introduction_text")

CATEGORIES_TEXT = data.get("categories")

# Текст для активных заказов
ORDER_TEXT = data.get("order")

# Шаблон для карточки блюда
FOOD_CART_TEXT = data.get("food_cart")

BASKET_TEXT = data.get("basket")

REVIEW_TEXT = data.get("review")

# Текст ошибки выполнения
ERROR_EXECUTE_TEXT = data.get("error_execute")

MAIN_MENU = data.get("main_menu_btns")

HELP = data.get("help")

ADMIN_TEXT = data.get("admin")

# Словарь, в который будем класть полученные данные о новом пользователе, для добавления записи о нем в `User`.
new_user_data = {}

# Данные карточки блюда для каждого пользователя
food_cart_data = {}

# Данные корзины для каждого пользователя
basket_data = {}

# Словарь содержащий выбранное для измения пользователем поле
update_udata = {}

# Слоаврь с message_id активных заказов
ord_message_ids = {}

# Словарь с информацией о заказах
order_data = {}

# Словарь для формирования коментариев к товарам
good_comment_data = {}

# ID сообщений для очистки
mes_ids = {}

# Заказы в чате админов ключи - номера заказов, значения - id сообщений
orders_admin_chat = {}

# bot
bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

# Планировщик
scheduler = AsyncIOScheduler()


# Функция которая будет вызываться после успешного выполнения заказа
async def send_mess_before_successful_order(**kwargs: dict) -> None:
    """
    Функция предназначена для отправки сообщения пользователю в заданное время.

    :param kwargs: Словарь с udata - словарь с TG user_id пользователя, и номером заказа .
    :return: None
    """
    udata = kwargs.get("udata", {})

    # Получаем данные заказа
    ord_dt = food_sdb.get_record('order', order_number=udata["order_number"])

    # Проверяем статус на "Доставлен"
    if ord_dt and ord_dt["status"].lower() == "доставлен":

        # Отправляем сообщение пользователю с просьбой оценить заказ
        await bot.send_message(chat_id=udata["user_id"],
                               text=REVIEW_TEXT["order"]["thank_for_order"],
                               reply_markup=create_inline_keyboard(buttons=[REVIEW_TEXT["order"]["btn"]],
                                                                   callback_prefix=f"revo_{ord_dt['order_number']}"))


# Клавиатура главного меню
def get_kb_main_menu() -> ReplyKeyboardMarkup:
    kb_main_menu = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text=MAIN_MENU["categories"])],
            [
                KeyboardButton(text=MAIN_MENU["basket"]),
                KeyboardButton(text=MAIN_MENU["active_orders"])
            ],
            [
                KeyboardButton(text=MAIN_MENU["add_review"]),
                KeyboardButton(text=MAIN_MENU["help"])
            ],
        ]
    )

    return kb_main_menu


# Клавиатура для карточки блюда
def get_ikb_food_cart(number1: int, number2: int, amount: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="-1", callback_data="minus"),
        InlineKeyboardButton(text=f"{amount} шт.", callback_data="amount_dishes"),
        InlineKeyboardButton(text="+1", callback_data="plus")
    )
    builder.row(
        InlineKeyboardButton(text="Добавить в корзину", callback_data="add_to_basket")
    )
    builder.row(
        InlineKeyboardButton(text="<", callback_data="back"),
        InlineKeyboardButton(text=f"{number1}/{number2}", callback_data="dish_number"),
        InlineKeyboardButton(text=">", callback_data="next")
    )

    return builder.as_markup()


# Для создания инлайн-клавиатур
def create_inline_keyboard(buttons: list[str] = None, callback_prefix: str = None, btns_dct: dict = None) -> InlineKeyboardMarkup:
    '''
    Создает инлайн-клавиатуру на основе переданных параметров. Аргумент 'btns_dct' имеет высший приоритет, это значит,
    что, если он был передан функции то функция создаст клавиатуру на его основе, в ином случае функция

    :param buttons: Список строковых значений, которые будут использоватся в качестве названий кнопок.
    :param callback_prefix: Префикс для формирования callback_data. Каждый callback_data будет иметь вид "{callback_prefix}_{название кнопки}".
    :param btns_dct: Параметр, представляющий словарь, где пары: (кнопки - коллбэк данные).
    :return: Возвращает экземпляр класса `InlineKeyboardMarkup` (готовую клавиатуру)
    '''
    builder = InlineKeyboardBuilder()
    if btns_dct:
        for btn, cb_dt in btns_dct.items():
            builder.button(text=btn, callback_data=cb_dt)
    else:
        for btn_txt in buttons:
            builder.button(text=btn_txt, callback_data=f"{callback_prefix}_{btn_txt}")
    builder.adjust(1)

    return builder.as_markup()


# Функция для изменения размеров изображения
def resize_image(image_path: str) -> None:
    """
    Изменяет размер изображения по указанному пути и перезаписывает его в том же формате.

    :param image_path: Путь к файлу изображения.
    :return: None
    """
    try:
        # Открываем изображение
        image = Image.open(image_path)

        # Изменяем размер изображения
        resized_image = image.resize(SIZE_IMAGE_FOOD_CART)

        # Перезаписываем изображение
        resized_image.save(image_path, format=image.format)
    except Exception as e:
        print(f"Произошла ошибка: {e}")


@dp.message(Command("start"))
async def handle_command_start(message: Message) -> None:
    user_id = message.from_user.id

    # получаем кортеж всех TG пользователей из таблицы User и проверяем на нового пользователя
    if user_id in food_sdb.get_tg_ids():
        name = food_sdb.get_urecord_tg(user_id)['name']
        await message.answer(text=INTRODUCTION_TEXT["welcome_user"].format(name=name),
                               reply_markup=get_kb_main_menu())
    else:
        new_user_data[user_id] = {"tg_id": user_id}

        # ключ для получения вопроса из `INTRODUCTION_TEXT["user_introduction"]`
        new_user_data[user_id]["u_reg_quest"] = 1

        await message.answer(text=INTRODUCTION_TEXT["user_introduction"]["0"])
        await message.answer(text=INTRODUCTION_TEXT["user_introduction"]["1"])


@dp.message(Command("help"))
async def handle_command_help(message: Message) -> None:
    await message.answer(text=HELP)


@dp.message(F.text == MAIN_MENU["categories"])
async def handle_food_categories(message: Message) -> None:
    user_id = message.from_user.id

    # кортеж всех уникальных категорий блюд для создания кнопок
    categories = food_sdb.get_uniq_cats()
    food_cart_data[user_id] = {"categories": categories}
    await message.answer(text=CATEGORIES_TEXT,
                           reply_markup=create_inline_keyboard(buttons=categories, callback_prefix="dbc"))


@dp.message(F.text == MAIN_MENU["basket"])
async def handle_basket(message: Message) -> None:
    user_id = message.from_user.id

    # получаем список всех данных корзины пользователя
    basket = food_sdb.get_basket_tg(user_id)
    if basket:
        # выводим название раздела меню
        sent_title_message = await message.answer(text=BASKET_TEXT["basket_data"]["title"])

        buffer = []  # сюда добавляем message_id каждого сообщения, чтобы их можно было легко удалить
        order_price = 0

        # перебираем всю корзину и выводим каждый продукт одельным сообщением
        for num, item in enumerate(basket):
            good = item['good_id']

            photo = good['tg_image_id']
            name = good['name']
            amount = item['amount']
            price = item['total_price']

            order_price += price

            sent_message = await bot.send_photo(chat_id=user_id,
                                                photo=photo,
                                                caption=BASKET_TEXT["basket_data"]["good_text"].
                                                format(number=num+1, name=name, amount=amount, price=price),
                                                reply_markup=create_inline_keyboard(buttons=["Удалить из коозины"],
                                                                                    callback_prefix=f"rfb_{num}"))
            buffer.append(sent_message.message_id)

        ikb = create_inline_keyboard(buttons=["Оформить заказ", "Очистить корзину"], callback_prefix="ba")

        sent_order_summary_message = await message.answer(text=BASKET_TEXT["basket_data"]["order_summary_message"].format(order_price=order_price),
                                           reply_markup=ikb)
        basket_data[user_id] = {
            "message_ids": buffer,
            "message_title_id": sent_title_message.message_id,
            "message_order_summary_id": sent_order_summary_message.message_id,
            "order_price": order_price,
            "basket_items": basket,
            "ikb": ikb
        }
    else:
        await bot.send_message(chat_id=user_id,
                               text=BASKET_TEXT["empty_basket_message"])


@dp.message(F.text == MAIN_MENU["active_orders"])
async def active_orders(message: Message) -> None:
    user_id = message.from_user.id

    # Полуаем список активных заказов
    ords = food_sdb.get_uactive_order_tg(user_id)

    if ords:
        # Отправляем заголовок
        await message.answer(text=ORDER_TEXT["title"])

        # Создаем клавиатуру с кнопкой "отменить заказ"
        ikb = create_inline_keyboard(buttons=["Отменить заказ"], callback_prefix="oa")

        # Создаем словарь для добавления message_id активных заказов пользователя
        order_data[user_id] = {}

        # Проходим циклом и отправляем сообщение с информацие о каждом заказе
        for ord in ords:
            # Список с текстом с информацией о товарах в заказе
            goodst = []

            # Проходим циклом по всем корзинам в заказе и заполняем список информацией о товаре
            for basket in ord["basket_id"]:
                goodst.append(ORDER_TEXT["good_info"].format(
                    name=basket["good_id"]["name"],
                    amount=basket["amount"],
                    price=basket["total_price"])
                )

            text = ORDER_TEXT["order_info"].format(
                order_number=ord["order_number"],
                order_time=ord["order_time"].strftime("%Y-%m-%d %H:%M"),
                delivery_time=ord["delivery_time"].strftime("%H:%M"),
                status=ord["status"],
                goods="\n".join(goodst),
                order_price=ord["order_price"],
                payment=ord["payment_method"],
                address=ord["delivery_address"],
                user_name=ord["user_name"],
                age=ord["age"],
                phone=ord["phone"],
            )
            s_mes = await message.answer(text=text, reply_markup=ikb)
            order_data[user_id][s_mes.message_id] = ord["order_number"]
    else:
        await message.answer(text=ORDER_TEXT["no_active_orders"])


@dp.message(F.text == MAIN_MENU["add_review"])
async def add_review(message: Message) -> None:
    user_id = message.from_user.id

    # Получаем все товары пользователя которые он заказывал
    ugoods = food_sdb.get_uordered_goods_tg(user_id)
    if ugoods:
        await message.answer(text=REVIEW_TEXT["good"]["title"])
        for g in ugoods:
            text = REVIEW_TEXT["good"]["good_info"].format(name=g["name"], category=g["category"],
                                                           description=g["description"])
            img = g.get('tg_image_id')
            if not img:
                # уставнавливаем размер изображения (300, 300) используя функцию `resize_image`
                resize_image(g['image'])
                img = FSInputFile(g['image'])
            ikb = create_inline_keyboard(buttons=REVIEW_TEXT["good"]["btn"], callback_prefix=f"revg_{g['id']}")
            await bot.send_photo(chat_id=user_id,
                                 photo=img,
                                 caption=text,
                                 reply_markup=ikb)
    else:
        await message.answer(text=REVIEW_TEXT["good"]["no_goods"])


@dp.message(F.text)
async def handle_text_message(message: Message) -> None:
    user_id = message.from_user.id
    mdt = message.text

    # номер вопроса из `INTRODUCTION_TEXT["user_introduction"]` который будем обрабатывать.
    if new_user_data.get(user_id):
        n_user = new_user_data[user_id]
        quest_num = n_user["u_reg_quest"]
        if quest_num == 1:
            n_user['name'] = mdt
            n_user['u_reg_quest'] += 1
            await message.answer(text=INTRODUCTION_TEXT["user_introduction"][str(n_user['u_reg_quest'])])

        elif quest_num == 2:
            try:
                n_user['age'] = int(mdt)
                n_user['u_reg_quest'] += 1
                await message.answer(text=INTRODUCTION_TEXT["user_introduction"][str(n_user['u_reg_quest'])])
            except ValueError as e:
                await message.answer(text=INTRODUCTION_TEXT["age_error"])

        elif quest_num == 3:
            if mdt[0] == "+" and mdt[1:4] == "375" and mdt[4:6] in ["29", "25", "44", "33"] and len(mdt[6:]) == 7 and mdt[6:].isdigit():
                n_user['phone'] = mdt
                n_user['u_reg_quest'] += 1
                await message.answer(text=INTRODUCTION_TEXT["user_introduction"][str(n_user['u_reg_quest'])])
            else:
                await message.answer(text=INTRODUCTION_TEXT["phone_error"])

        elif quest_num == 4:
            n_user['delivery_address'] = mdt
            n_user['u_reg_quest'] += 1

            new_user = food_sdb.add_record("user", **new_user_data[user_id])
            if new_user:
                await message.answer(text=INTRODUCTION_TEXT["user_introduction"][str(n_user['u_reg_quest'])])

                # т.к. new_user теперь просто user (: , удаляем его из словарей с данными о новых пользователях.
                del new_user_data[user_id]
                await message.answer(text=INTRODUCTION_TEXT["welcome_user"].format(name=new_user['name']),
                                     reply_markup=get_kb_main_menu())
            else:
                await message.answer(text=ERROR_EXECUTE_TEXT)

            # Удаляем данные пользователя из словаря
            del new_user_data[user_id]

    # пользователь изменил данные
    elif update_udata.get(user_id):
        field = update_udata[user_id]

        del update_udata[user_id]
        new_value = mdt

        # проверяем на целое число
        if field == "age":
            if not new_value.isdigit():
                await message.answer(text=INTRODUCTION_TEXT["age_error"])
                return

        elif field == "phone":
            if not (mdt[0] == "+" and mdt[1:4] == "375" and mdt[4:6] in ["29", "25", "44", "33"] and len(
                    mdt[6:]) == 7 and mdt[6:].isdigit()):
                await message.answer(text=INTRODUCTION_TEXT["phone_error"])
                return


        # обновляем поле field таблицы User на new_value
        if food_sdb.update_record("user", {field: new_value}, tg_id=user_id):
            await message.answer(text=BASKET_TEXT["update_success_message"])

            # получаем обновленные данные пользователя
            u = food_sdb.get_urecord_tg(user_id)
            text = BASKET_TEXT["confirmation_message"].format(name=u['name'], age=u['age'], phone=u['phone'],
                                                              address=u['delivery_address'])
            ikb = create_inline_keyboard(buttons=["Подтвердить данные", "Изменить данные"], callback_prefix="ba")
            await message.answer(text=text, reply_markup=ikb)

    # текст для коммента к заказу
    elif order_data.get(user_id) and order_data[user_id].get("review"):
        ord_com = mdt
        ord_n = order_data[user_id]["review"]["order_number"]

        # добовляем текст отзыва к уже существующей записи в ordercomment
        if food_sdb.update_record("ordercomment", {"text": ord_com}, order_number=ord_n):
            await message.answer(text=REVIEW_TEXT["order"]["answer_comment"])
            del order_data[user_id]["review"]
        else:
            await message.answer(text=ERROR_EXECUTE_TEXT)

    # текст для коммента к товару
    elif good_comment_data.get(user_id) and good_comment_data[user_id].get("goodcomment_id"):
        g_com = mdt
        gc_id = good_comment_data[user_id]["goodcomment_id"]

        # добавляем текст отзыва к уже существующей записи в goodcomment
        if food_sdb.update_record("goodcomment", {"text": g_com}, id=gc_id):
            await message.answer(text=REVIEW_TEXT["order"]["answer_comment"])
            del good_comment_data[user_id]
        else:
            await message.answer(text=ERROR_EXECUTE_TEXT)


# dbc - dishes by category
@dp.callback_query(F.data.startswith("dbc"))
async def cb_handle_category(callback_query: CallbackQuery) -> None:
    current_cat = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    f_cart = food_cart_data[user_id]

    # получаем список словарей с данными из таблицы `Good`, которые соответствуют выбранной категории.
    goods_list = food_sdb.get_goods_by_cat(current_cat)

    # определяем его длину, номер блюда и другие данные. И заносим все данные в `food_cart_data`
    amount = 1
    good_number = 1

    len_goods_list = len(goods_list)
    f_cart["goods_list"] = goods_list
    f_cart["len_goods_list"] = len_goods_list
    f_cart["amount"] = amount
    f_cart["good_number"] = good_number

    # первое блюдо выбранной категории
    good = goods_list[good_number - 1]

    # если `tg_image_id` отсутствует, используем путь к изображению из папки `images` в проекте.
    image = good.get('tg_image_id')
    if not image:
        # уставнавливает размер изображения (300, 300) используя функцию `resize_image`
        resize_image(good['image'])
        image = FSInputFile(good['image'])

    ikb = get_ikb_food_cart(amount=amount, number1=good_number, number2=len_goods_list)

    caption = FOOD_CART_TEXT["food_cart_text"].format(name=good['name'], price=good['price'], category=good['category'],
                                                      cooking_time=good['cooking_time'], description=good['description'],
                                                      available=("Да" if good['available'] else "Нет"))

    # Получаем 5 последних отзывов к выбранному товару
    good_review = food_sdb.get_five_gcomms(good['id'])

    if good_review:
        review_text = []
        for gr in good_review:
            review_text.append(
                FOOD_CART_TEXT["template_review"].format(
                    eval=gr['eval'] * "⭐️",
                    name=gr["user_id"]["name"],
                    review_text=gr["text"]
                )
            )
        caption += "\n\n⬇️ Отзывы ⬇️\n\n" + "\n\n".join(review_text)

    if not good_review:
        caption += '\n\n*Отзывы:*\n\n'

    sent_photo = await callback_query.bot.send_photo(chat_id=user_id, photo=image, caption=caption,
                                                     reply_markup=ikb)

    # добавляем file_id отправленного фото, если поле `tg_image_id` пустое.
    if not good.get('tg_image_id'):

        # обработать -------------------------------------------------------------------------------------------------
        good_id = good['id']
        food_sdb.update_record('good', {'tg_image_id': sent_photo.photo[0].file_id}, id=good_id)


@dp.callback_query(F.data.in_({"minus", "plus"}))
async def cb_amount_change(callback_query: CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    f_cart = food_cart_data[user_id]
    message_id = callback_query.message.message_id

    # увеличиваем количество товаров на 1, если data равен "plus", иначе уменьшаем на 1.
    # при уменьшении также используем max, чтобы не допустить отрицательного значения.
    f_cart["amount"] = f_cart["amount"] + 1 if callback_query.data == "plus" else max(
        f_cart["amount"] - 1, 1)

    ikb = get_ikb_food_cart(amount=f_cart["amount"],
                            number1=f_cart["good_number"],
                            number2=f_cart["len_goods_list"])
    try:
        await callback_query.bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=ikb)
    except aiogram.exceptions.TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer(text=FOOD_CART_TEXT["amount_goods_error"])


@dp.callback_query(F.data.in_({"back", "next"}))
async def cb_switch_goods(callback_query: CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    f_cart = food_cart_data[user_id]

    if f_cart["len_goods_list"] > 1:

        # увеличиваем или уменьшаем номер товара в корзине на 1 в зависимости от значения data.
        if callback_query.data == "next":
            f_cart["good_number"] += 1
            if f_cart["good_number"] > f_cart["len_goods_list"]:
                f_cart["good_number"] = 1
        else:
            f_cart["good_number"] -= 1
            if f_cart["good_number"] < 1:
                f_cart["good_number"] = f_cart["len_goods_list"]


        good_number = f_cart["good_number"]

        # обнуляем количество товара (блюд)
        f_cart["amount"] = 1
        good = food_cart_data[user_id]["goods_list"][good_number - 1]

        image = good['tg_image_id']
        if not image:
            # уставнавливает размер изображения (300, 300) используя функцию `resize_image`
            resize_image(good['image'])
            image = FSInputFile(good['image'])

        chat_id = callback_query.from_user.id
        message_id = callback_query.message.message_id

        caption = FOOD_CART_TEXT["food_cart_text"].format(name=good['name'], price=good['price'], category=good['category'],
                                                          cooking_time=good['cooking_time'], description=good['description'],
                                                          available=("Да" if good['available'] else "Нет"))

        ikb = get_ikb_food_cart(amount=f_cart["amount"],
                                number1=f_cart["good_number"],
                                number2=f_cart["len_goods_list"])

        media_photo = InputMediaPhoto(media=image, caption=caption)
        sent_photo = await callback_query.bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media_photo,
                                                                 reply_markup=ikb)
        # добавляем file_id отправленного фото, если поле `tg_image_id` пустое.
        if not good.get('tg_image_id'):
            good_id = good['id']

            # обработать -------------------------------------------------------------------------------------------------
            g = food_sdb.update_record("good", {"tg_image_id": sent_photo.photo[0].file_id}, id=good_id)


@dp.callback_query(F.data == "add_to_basket")
async def cb_add_to_basket(callback_query: CallbackQuery) -> None:
    f_cart = food_cart_data[callback_query.from_user.id]
    good_number = f_cart["good_number"]
    user_id = callback_query.from_user.id
    current_good = f_cart["goods_list"][good_number - 1]

    # получаем кортеж с общим колиичеством и прайсом (amount, total_price) для одинаковых товаров в корзине
    basket_entry = food_sdb.union_basket_entries_tg(user_id, current_good['id'])

    # удаляем всзаписи пользователя с одинаковым товаром (good_id)
    u_id = food_sdb.get_urecord_tg(user_id)
    food_sdb.delete_all_records('basket', good_id=current_good['id'], user_id=u_id['id'], added_to_order=False)


    total_amount = 0
    total_price = 0
    if basket_entry:
        total_amount += basket_entry[0]
        total_price += basket_entry[1]

    # если товар не на стопе то, добавляем новую звпись в `Baskets`
    if current_good["available"]:
        basket = food_sdb.add_record('basket', amount=f_cart["amount"] + total_amount,
                                     total_price=f_cart["amount"] * current_good["price"] + total_price,
                                     user_id=food_sdb.get_urecord_tg(user_id)["id"], good_id=current_good["id"])
        f_cart["amount"] = 1

        try:
            await callback_query.bot.edit_message_reply_markup(chat_id=user_id,
                                                               message_id=user_id,
                                                               reply_markup=get_ikb_food_cart(
                                                                   number1=good_number,
                                                                   number2=f_cart["len_goods_list"],
                                                                   amount=f_cart["amount"]
                                                               ))
        except Exception as e:
            pass

        await callback_query.answer(text=FOOD_CART_TEXT["basket_add_success"])
    else:
        await callback_query.answer(text=FOOD_CART_TEXT["good_stop"])


# rfb - remove from basket
@dp.callback_query(F.data.startswith("rfb"))
async def cb_remove_from_basket(callback_query: CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    user_basket_dt = basket_data[user_id]

    # получение номера товара из callback_data
    num = int(callback_query.data.split("_")[1])

    # получение информации о товаре используем num как индекс
    basket_item = user_basket_dt["basket_items"][num]
    message_id = user_basket_dt["message_ids"].pop(num)

    # стоимость удаляемого товара
    price = basket_item['total_price']

    # удаляем товар из корзины в `Basket`
    del_g = food_sdb.delete_record('basket', id=basket_item['id'])
    # удаляем соощбщение с товаром
    await bot.delete_message(chat_id=user_id, message_id=message_id)

    # обновляем стоимость заказа
    user_basket_dt["order_price"] -= price

    if user_basket_dt["message_ids"]:
        await callback_query.bot.edit_message_text(text=BASKET_TEXT["basket_data"]["order_summary_message"].
                                                   format(order_price=user_basket_dt["order_price"]),
                                                   chat_id=user_id,
                                                   message_id=user_basket_dt["message_order_summary_id"],
                                                   reply_markup=user_basket_dt["ikb"])
    else:
        await bot.delete_message(chat_id=user_id, message_id=user_basket_dt["message_title_id"])
        await callback_query.bot.edit_message_text(text=BASKET_TEXT["empty_basket_message"],
                                                   chat_id=user_id,
                                                   message_id=user_basket_dt["message_order_summary_id"])


# ba - basket action
@dp.callback_query(F.data.startswith("ba"))
async def cb_basket_action(callback_query: CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id

    # получаем данные пользователя
    u = food_sdb.get_urecord_tg(user_id)

    u_basket_dt = basket_data[user_id]
    cb_data = callback_query.data.split("_")[1]

    if cb_data == "Оформить заказ":
        text = BASKET_TEXT["confirmation_message"].format(name=u['name'], age=u['age'], phone=u['phone'], address=u['delivery_address'])
        ikb = create_inline_keyboard(buttons=["Подтвердить данные", "Изменить данные"], callback_prefix="ba")
        await callback_query.bot.edit_message_text(chat_id=user_id,
                                                   message_id=callback_query.message.message_id,
                                                   text=text,
                                                   reply_markup=ikb)

    elif cb_data == "Очистить корзину":

        for bi in u_basket_dt["basket_items"]:
            food_sdb.delete_record('basket', id=bi['id'])

        await bot.delete_message(chat_id=user_id, message_id=u_basket_dt['message_title_id'])
        u_basket_dt["order_price"] = 0
        for message_id in u_basket_dt["message_ids"]:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
        u_basket_dt["message_ids"].clear()


        await callback_query.bot.edit_message_text(chat_id=user_id,
                                                   message_id=callback_query.message.message_id,
                                                   text=BASKET_TEXT["empty_basket_message"])

    elif cb_data == "Подтвердить данные":
        buttons = ["Картой", "Наличными при получении"]
        await callback_query.bot.edit_message_text(chat_id=user_id,
                                                   message_id=callback_query.message.message_id,
                                                   text="Выберите удобный способ оплаты:",
                                                   reply_markup=create_inline_keyboard(buttons, "ba"))

    elif cb_data in ("Картой", "Наличными при получении"):
        # рассчитываем время приготовления
        mx_cooking_t = max([i["good_id"]["cooking_time"] for i in u_basket_dt["basket_items"]])

        # дата для создания ордера
        dtn = dtm.now()

        # Рассчитываем время доставки
        deliv_tm = dtn + timedelta(minutes=int(mx_cooking_t) + 30)

        # добавляем новые ордеры и получаем их
        ord_recs = food_sdb.add_ords_tg(
            ord_tm=dtn,
            deliv_tm=deliv_tm,
            ord_p=u_basket_dt["order_price"],
            status="Оформлен",
            pay_m=cb_data,
            user_id=user_id,
            deliv_address=u["delivery_address"],
            uname=u["name"],
            age=u["age"],
            phone=u["phone"]
        )
        ord_recs = ord_recs[0]

        # Вычисляем время выполнения задачи, добавляем к времени доставки 5 мин
        scheduled_time = deliv_tm + timedelta(minutes=5)

        # Добавляем задачу в планировщик
        udata = {"user_id": user_id, "order_number": ord_recs["order_number"]}
        scheduler.add_job(send_mess_before_successful_order, 'date', run_date=scheduled_time, kwargs={"udata": udata})

        # ставим поля Basket.added_to_order в значение True
        # тем самым как бы очищаем корзину пользователя показывая что заказ оформлен
        up_fields = food_sdb.basket_change_added_to_ord_tg(user_id)
        if up_fields:
            # создаем список с id сообщений о товарах из корзины
            del_mess_ids = u_basket_dt["message_ids"]
            del_mess_ids.append(u_basket_dt["message_title_id"])

            # удаляем сообщения с информацией о товарах в корзине
            await bot.delete_messages(chat_id=user_id, message_ids=del_mess_ids)

            # удаляем эллемент словаря связанный с корзиной пользователя
            del basket_data[user_id]

            # содержимое заказа для чека
            gs_list = []
            for bi in u_basket_dt["basket_items"]:
                t = BASKET_TEXT["checkout_receipt"]["good_info"].format(name=bi['good_id']['name'],
                                                                        amount=bi['amount'],
                                                                        price=bi['total_price'])
                gs_list.append(t)

            # выводим чек
            text = BASKET_TEXT["checkout_receipt"]["check_info"].format(datetime=dtn.strftime("%Y-%m-%d %H:%M"),
                                                                        goods="\n".join(gs_list),
                                                                        order_number=ord_recs["order_number"],
                                                                        order_price=ord_recs["order_price"],
                                                                        address=u_basket_dt["basket_items"][0]["user_id"]["delivery_address"],
                                                                        phone=u_basket_dt["basket_items"][0]["user_id"]["phone"],
                                                                        payment=ord_recs["payment_method"],
                                                                        user_name=u["name"],
                                                                        age=u["age"])
            await callback_query.bot.edit_message_text(text=text,
                                                       chat_id=user_id,
                                                       message_id=message_id)
            await callback_query.message.answer(text=BASKET_TEXT["checkout_receipt"]["footer_text"])

            # Получаем новый заказ
            nord = food_sdb.get_order_by_ordnum(ord_recs["order_number"])
            nord = nord[0]
            # Формируем сообщения для отправки в чат админов
            good_info = []
            for item in nord["basket_id"]:
                good_info.append(
                    ADMIN_TEXT["good_info"].format(
                        name=item["good_id"]["name"],
                        amount=item["amount"],
                        price=item["total_price"]
                    )
                )
            text = ADMIN_TEXT["order"].format(
                order_number=nord["order_number"],
                order_time=nord["order_time"].strftime("%Y-%m-%d %H:%M"),
                delivery_time=nord["delivery_time"].strftime("%H:%M"),
                goods="/n".join(good_info),
                order_price=nord["order_price"],
                address=nord["delivery_address"],
                user_name=nord["user_name"],
                age=nord["age"],
                phone=nord["phone"],
                payment=nord["payment_method"],
                status=nord["status"]
            )
            print(ord_recs)
            ikb = create_inline_keyboard(buttons=ADMIN_TEXT["btns"], callback_prefix=f"chngst_{ord_recs['order_number']}")
            sent_mes = await callback_query.bot.send_message(chat_id=ADMINS_CHAT_ID,
                                                             text=text,
                                                             reply_markup=ikb)

            # Добавляем message_id в словарь связывая его с order_number
            orders_admin_chat[nord["order_number"]] = sent_mes.message_id
        else:
            await callback_query.answer(text=ERROR_EXECUTE_TEXT)

    elif cb_data == "Изменить данные":
        btns = ["Имя", "Возраст", "Номер телефона", "Адрес доставки"]
        await callback_query.bot.edit_message_text(text=BASKET_TEXT["update_data_message"],
                                                   chat_id=user_id,
                                                   message_id=message_id,
                                                   reply_markup=create_inline_keyboard(buttons=btns,
                                                                                       callback_prefix="ba"))

    elif cb_data in ("Имя", "Возраст", "Номер телефона", "Адрес доставки"):
        fields_dicty = {"Имя": "name",
                        "Возраст": "age",
                        "Номер телефона": "phone",
                        "Адрес доставки": "delivery_address"}


        # поле, которое выбрал пользователь для изменения
        f = fields_dicty[cb_data]

        # добавляем его в словарь и чтобы зафиксировать состояние
        update_udata[user_id] = f
        await callback_query.bot.edit_message_text(text=BASKET_TEXT["update_questions"][f],
                                                   chat_id=user_id,
                                                   message_id=message_id)


# oa - order action
@dp.callback_query(F.data.startswith("oa"))
async def cb_order_action(callback_query: CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    cb_data = callback_query.data.split("_")[1]

    # Получаем message_id для заказа который пользователь хочет отменить
    m_id = callback_query.message.message_id

    # Пользователь отменяет заказ
    if cb_data == ORDER_TEXT["cancel_btn"]:
        # Получаем номер заказа
        ord_n = order_data[user_id][m_id]

        # Помечаем номер отмененного заказа
        order_data[user_id]["cancel_ord_num"] = ord_n

        # Отменяем заказ
        res = food_sdb.cancel_order_tg(user_id, ord_n)
        if res:
            # Удаляем сообщение о заказе
            await callback_query.bot.delete_message(chat_id=user_id, message_id=m_id)
            del order_data[user_id][m_id]

            # Выводим сообщение об успешной отмене
            await callback_query.message.answer(text=ORDER_TEXT["cancel_order"]["successful_cancel_order"])

            # Просим пользователя указать причну отмены
            ikb = create_inline_keyboard(buttons=ORDER_TEXT["cancel_order"]["cancellation_reason_buttons"],
                                         callback_prefix="oa")
            await callback_query.message.answer(text=ORDER_TEXT["cancel_order"]["title"], reply_markup=ikb)

            # Получаем по номеру удаленного заказа message_id заказа в чате админов
            m_id = orders_admin_chat.get(ord_n)
            if m_id:
                # Информируем админов о том, что заказ был отменен
                await callback_query.bot.edit_message_text(text=ADMIN_TEXT["cancel_order"].format(order_number=ord_n),
                                                           chat_id=ADMINS_CHAT_ID,
                                                           message_id=m_id)
                del orders_admin_chat[ord_n]


    # Пользователь указал причину отмены
    elif cb_data in ORDER_TEXT["cancel_order"]["cancellation_reason_buttons"]:
        # Добавляем причину отмены в таблицу Order
        ord_n = order_data[user_id]["cancel_ord_num"]
        if food_sdb.update_record("order", {"cancellation_reason": cb_data.strip()}, order_number=ord_n):
            del order_data[user_id]["cancel_ord_num"]
            await callback_query.bot.edit_message_text(text=ORDER_TEXT["cancel_order"]["thank_text"],
                                                       chat_id=user_id,
                                                       message_id=callback_query.message.message_id)
            # Информируем админов о том, что пользователь указал причину
            await callback_query.bot.send_message(chat_id=ADMINS_CHAT_ID,
                                                  text=ADMIN_TEXT["cancellation_reason"].format(
                                                      order_number=ord_n,
                                                      cancellation_reason=cb_data.strip()
                                                  ))
        else:
            await callback_query.answer(text=ERROR_EXECUTE_TEXT)


@dp.callback_query(F.data.startswith("eval"))
async def cb_evaluation(callback_query: CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    cb_data = callback_query.data.split("_")

    # данные пользователя
    u = food_sdb.get_urecord_tg(user_id)

    # оценка из callback_data
    ev = cb_data[1]

    # оценка для заказа
    if cb_data[0] == "evalord":
        # Добавляем запись в таблицу ordercomment
        ord_n = order_data[user_id]["review"]["order_number"]
        if food_sdb.add_record("ordercomment", eval=ev, validate=False, user_id=u["id"], order_number=ord_n):
            # отправляем сообщение с просьбой написать коммент
            await callback_query.bot.edit_message_text(text=REVIEW_TEXT["order"]["order_comment"],
                                                       chat_id=user_id,
                                                       message_id=callback_query.message.message_id)
        else:
            await callback_query.answer(text=ERROR_EXECUTE_TEXT)

    elif cb_data[0] == "evalgood":
        # Добавляем запись в таблицу goodcomment
        good_id = good_comment_data[user_id]["good_id"]
        nrec = food_sdb.add_record("goodcomment", eval=ev, validate=False, user_id=u["id"], good_id=good_id)
        if nrec:
            good_comment_data[user_id]["goodcomment_id"] = nrec["id"]

            # отправляем сообщение с просьбой написать коммент
            await callback_query.bot.edit_message_text(text=REVIEW_TEXT["good"]["good_comment"],
                                                       chat_id=user_id,
                                                       message_id=callback_query.message.message_id)
        else:
            await callback_query.answer(text=ERROR_EXECUTE_TEXT)


@dp.callback_query(F.data.startswith("rev"))
async def cb_review(callback_query: CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    cb_data = callback_query.data.split("_")
    m_id = callback_query.message.message_id

    # отзвыв к заказу
    if cb_data[0] == "revo":

        # Получаем из callback_data номер заказа
        ord_n = int(cb_data[1])

        # Фиксируем состояние, добавляем соответствующую запись в словарь
        order_data[user_id]["review"] = {"order_number": ord_n}

        # Отправляем сообщение где просим поставить оценку
        ikb = create_inline_keyboard(btns_dct=REVIEW_TEXT["order"]["eval_btns_dict"])
        await callback_query.bot.edit_message_text(chat_id=user_id,
                                                   message_id=m_id,
                                                   text=REVIEW_TEXT["order"]["eval_text"],
                                                   reply_markup=ikb)
    # отзвыв к товару
    elif cb_data[0] == "revg":
        # Получаем из callback_data id товара
        good_id = int(cb_data[1])

        # Фиксируем состояние, добавляем соответствующую запись в словарь
        good_comment_data[user_id] = {"good_id": good_id}

        # Отправляем сообщение где просим поставить оценку
        ikb = create_inline_keyboard(btns_dct=REVIEW_TEXT["good"]["eval_btns_dict"])
        await callback_query.message.answer(text=REVIEW_TEXT["good"]["eval_text"], reply_markup=ikb)


# Изменение статуса заказа в чате админов
@dp.callback_query(F.data.startswith("chngst"))
async def cb_change_order_status(callback_query: CallbackQuery) -> None:
    # Поулчаем номер заказа
    ord_n = callback_query.data.split("_")[1]

    ikb = create_inline_keyboard(buttons=ADMIN_TEXT["statuses_btns"], callback_prefix=f"stselect_{ord_n}")
    await callback_query.bot.edit_message_text(text=ADMIN_TEXT["status_selection"],
                                               chat_id=ADMINS_CHAT_ID,
                                               message_id=callback_query.message.message_id,
                                               reply_markup=ikb)


# Выбор статуса заказа в чате админов
@dp.callback_query(F.data.startswith("stselect"))
async def cb_status_selection(callback_query: CallbackQuery) -> None:
    cb_dt = callback_query.data.split("_")

    # Получаем номер и статус заказа
    ord_n = int(cb_dt[1])
    st = cb_dt[2]

    # Обновляем статус заказа
    if food_sdb.update_record('order', {"status": st}, order_number=ord_n):
        # Получаем новый заказ
        nord = food_sdb.get_order_by_ordnum(ord_n)
        print(nord)
        print(nord["status"])
        # Формируем сообщения для отправки в чат админов
        good_info = []
        for item in nord["basket_id"]:
            good_info.append(
                ADMIN_TEXT["good_info"].format(
                    name=item["good_id"]["name"],
                    amount=item["amount"],
                    price=item["total_price"]
                )
            )
        text = ADMIN_TEXT["order"].format(
            order_number=nord["order_number"],
            order_time=nord["order_time"].strftime("%Y-%m-%d %H:%M"),
            delivery_time=nord["delivery_time"].strftime("%H:%M"),
            goods="/n".join(good_info),
            order_price=nord["order_price"],
            address=nord["delivery_address"],
            user_name=nord["user_name"],
            age=nord["age"],
            phone=nord["phone"],
            payment=nord["payment_method"],
            status=nord["status"]
        )

        ikb = create_inline_keyboard(buttons=ADMIN_TEXT["btns"], callback_prefix=f"chngst_{ord_n}")
        await callback_query.bot.edit_message_text(text=text,
                                                   chat_id=ADMINS_CHAT_ID,
                                                   message_id=callback_query.message.message_id,
                                                   reply_markup=ikb)

    else:
        await callback_query.answer(ERROR_EXECUTE_TEXT)


async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:

        asyncio.run(main())
    finally:
        scheduler.shutdown()
