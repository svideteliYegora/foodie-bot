import logging
import asyncio
import sys
import json

import aiogram.exceptions
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatType
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

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Получаем config данные
with open("venv/config.json", "r") as json_file:
    config = json.load(json_file)

TG_TOKEN = config.get("TG_TOKEN")
SUPER_USER = config.get("SUPER_USER")
ADMINS_CHAT_ID = config.get("ADMINS_CHAT_ID")
SIZE_IMAGE_FOOD_CART = tuple(config.get("SIZE_IMAGE_FOOD_CART"))

# Текст для сообщений бота
with open("messages.json", "r") as json_file:
    data = json.load(json_file)

# Текст для приветсвия и знакомства с пользователем
INTRODUCTION_TEXT = data.get("introduction_text")

CATEGORIES_TEXT = data.get("categories")

# Шаблон для карточки блюда
FOOD_CART_TEXT = data.get("food_cart")

BASKET_TEXT = data.get("basket")

# Текст ошибки выполнения
ERROR_EXECUTE = data.get("error_execute")

# Текстовый шаблон

# Словарь, где ключи - user_id новых пользователей, а значения номера из `user_introduction`
u_reg_questions = {}

# Словарь, в который будем класть полученные данные о новом пользователе, для добавления записи о нем в `User`.
new_user_data = {}

# Данные карточки блюда для каждого пользователя
food_cart_data = {}

# Данные корзины для каждого пользователя
basket_data = {}

# Данные заказов для каждого пользователя
order_data = {}


# bot
bot = Bot(token=TG_TOKEN)
dp = Dispatcher()


# Клавиатура главного меню
def get_kb_main_menu() -> ReplyKeyboardMarkup:
    kb_main_menu = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="🍽️ Категории Блюд")],
            [
                KeyboardButton(text="🛒 Корзина"),
                KeyboardButton(text="🚚 Активные заказы")
            ],
            [
                KeyboardButton(text="✏️ Добавить отзыв"),
                KeyboardButton(text="❓  Справка")
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
def create_inline_keyboard(buttons: list[str], callback_prefix: str) -> InlineKeyboardMarkup:
    '''
    Создает инлайн-клавиатуру на основе переданных параметров.

    :param buttons: Список строковых значений, которые будут использоватся в качестве названий кнопок.
    :param callback_prefix: Префикс для формирования callback_data. Каждый callback_data будет иметь вид "{callback_prefix}_{название кнопки}".
    :return: Возвращает экземпляр класса `InlineKeyboardMarkup` (готовую клавиатуру)
    '''
    builder = InlineKeyboardBuilder()
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

        # проверяем пишет ли он из групового чата
        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            # если это чат для админов
            if message.chat.id == ADMINS_CHAT_ID:
                await bot.send_message(chat_id=message.chat.id,
                                       text=INTRODUCTION_TEXT["welcome_admin"],
                                       reply_markup=None)  # панель админов
            else:
                await bot.send_message(chat_id=message.chat.id,
                                       text=INTRODUCTION_TEXT["away_message"])
        else:
            name = food_sdb.get_urecord_tg(user_id)['name']
            await message.answer(text=INTRODUCTION_TEXT["welcome_user"].format(name=name),
                                 reply_markup=get_kb_main_menu())
    else:
        u_reg_questions[user_id] = 1  # ключ для получения вопроса из `INTRODUCTION_TEXT["user_introduction"]`
        new_user_data[user_id] = {"tg_id": user_id}
        await message.answer(text=INTRODUCTION_TEXT["user_introduction"]["0"])
        await message.answer(text=INTRODUCTION_TEXT["user_introduction"]["1"])


@dp.message(F.text == "🍽️ Категории Блюд")
async def handle_food_categories(message: Message) -> None:
    # кортеж всех уникальных категорий блюд для создания кнопок
    categories = food_sdb.get_uniq_cats()
    food_cart_data[message.from_user.id] = {"categories": categories}
    await message.answer(text=CATEGORIES_TEXT,
                         reply_markup=create_inline_keyboard(buttons=categories, callback_prefix="dbc"))


@dp.message(F.text == "🛒 Корзина")
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
            "basket_items": basket
        }
    else:
        await bot.send_message(chat_id=user_id,
                               text=BASKET_TEXT["empty_basket_message"])


@dp.message(F.text)
async def handle_text_message(message: Message) -> None:
    user_id = message.from_user.id

    # номер вопроса из `INTRODUCTION_TEXT["user_introduction"]` который будем обрабатывать.
    question_number = u_reg_questions.get(user_id)
    if question_number:

        if question_number == 1:
            new_user_data[user_id]['name'] = message.text
            u_reg_questions[user_id] += 1
            await message.answer(text=INTRODUCTION_TEXT["user_introduction"][str(u_reg_questions[user_id])])

        elif question_number == 2:
            try:
                new_user_data[user_id]['age'] = int(message.text)
                u_reg_questions[user_id] += 1
                await message.answer(text=INTRODUCTION_TEXT["user_introduction"][str(u_reg_questions[user_id])])
            except ValueError as e:
                await message.answer(text=INTRODUCTION_TEXT["age_error"])

        elif question_number == 3:
            new_user_data[user_id]['phone'] = message.text
            u_reg_questions[user_id] += 1
            await message.answer(text=INTRODUCTION_TEXT["user_introduction"][str(u_reg_questions[user_id])])

        elif question_number == 4:
            new_user_data[user_id]['delivery_address'] = message.text
            u_reg_questions[user_id] += 1

            # обработать ----------------------------------------------------------------------------------------------
            new_user = food_sdb.add_user(**new_user_data[user_id])

            await message.answer(text=INTRODUCTION_TEXT["user_introduction"][str(u_reg_questions[user_id])])

            # т.к. new_user теперь просто user (: , удаляем его из словарей с данными о новых пользователях.
            del u_reg_questions[user_id]
            del new_user_data[user_id]

            await message.answer(text=INTRODUCTION_TEXT["welcome_user"].format(name=new_user['name']),
                                 reply_markup=get_kb_main_menu())


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
        else:
            raise


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
    food_sdb.delete_all_records('basket', good_id=current_good['id'], user_id=u_id['id'])


    total_amount = 0
    total_price = 0
    if basket_entry:
        total_amount += basket_entry[0]
        total_price += basket_entry[1]

    # добавляем новую звпись в `Baskets`
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
    print(del_g)
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

        await bot.delete_message(chat_id=user_id, message_id=u_basket_dt['message_title_id'])
        u_basket_dt["order_price"] = 0
        for message_id in u_basket_dt["message_ids"]:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
        u_basket_dt["message_ids"].clear()
        for bi in u_basket_dt["basket_items"]:
            food_sdb.delete_record('basket', id=bi['id'])

        await callback_query.bot.edit_message_text(chat_id=user_id,
                                                   message_id=callback_query.message.message_id,
                                                   text=BASKET_TEXT["empty_basket_message"])

    elif cb_data == "Подтвердить данные":
        order_data[user_id] = {}
        buttons = ["Картой", "Наличными при получении"]
        await callback_query.bot.edit_message_text(chat_id=user_id,
                                                   message_id=callback_query.message.message_id,
                                                   text="Выберите удобный способ оплаты:",
                                                   reply_markup=create_inline_keyboard(buttons, "ba"))

    elif cb_data in ("Картой", "Наличными при получении"):
        # рассчитываем время приготовления
        mx_cooking_t = max([i["good_id"]["cooking_time"] for i in u_basket_dt["basket_items"]])

        # данные для создания ордера
        dtn = dtm.now()

        # добавляем новые ордеры и получаем их
        ord_recs = food_sdb.add_ords_tg(
            ord_tm=dtn,
            deliv_tm=dtn + timedelta(minutes=int(mx_cooking_t) + 30),
            ord_p=u_basket_dt["order_price"],
            status="В обработке",
            pay_m=cb_data,
            user_id=user_id,
        )

        # очищаем данные пользователя в таблице Basket
        food_sdb.delete_all_records("basket", id=u_basket_dt["basket_items"][0]["user_id"]["id"])

        # создаем список с id сообщений о товарах из корзины
        del_mess_ids = u_basket_dt["message_ids"]
        del_mess_ids.append(u_basket_dt["message_title_id"])

        # удаляем сообщения с информацией о товарах в корзине
        for m_id in del_mess_ids:
            await callback_query.bot.delete_message(chat_id=user_id, message_id=m_id)

        # удаляем эллемент словаря связанный с корзиной пользователя
        del basket_data[user_id]

        # содержимое заказа для чека
        gs_list = [f"Название: {bi['good_id']['name']}\nКоличество: {bi['amount']}\nСтоимость: {bi['total_price']}" for bi in u_basket_dt["basket_items"]]

        # выводим чек
        text = BASKET_TEXT["checkout_receipt"].format(datetime=dtn.strftime("%Y-%m-%d %H:%M"),
                                                      order_number=ord_recs[0]["order_number"],
                                                      )
        await callback_query.bot.edit_message_text(text=BASKET_TEXT["checkout_receipt"])
