from datetime import datetime, timedelta

from vk_api import VkApi, VkUpload
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from models import food_sdb

GROUP_ID = '224262397'
GROUP_TOKEN = 'vk1.a.O4b-gsCjTkGkgNgqChyB64QEGsHsxivBaZ-19GOTJo05tqLH9hB91HnfSrHEAl7AjirUJ9C2QLgdEAWlMZAQ2nydw9KEJltTGr-C9jB9PSwsBvy26FWwgtNs68n204RLxIFS_hkMBF8kkzsr97Sfj4IGE5LWvnvqJBpxEaj2oa0RiEsM77eyfSaCjKnl3tWrGfAmilLtteLYvYnchQaQYQ'
API_VERSION = '5.120'


def generation_karta_bluda(count,page,all_page):
    keyboard_karta_bluda = VkKeyboard(one_time=False, inline=True)
    keyboard_karta_bluda.add_callback_button(label='-1', color=VkKeyboardColor.PRIMARY, payload={"type": '-1'})
    keyboard_karta_bluda.add_callback_button(label=f'{count}', color=VkKeyboardColor.PRIMARY, payload={"type": 'count'})
    keyboard_karta_bluda.add_callback_button(label='+1', color=VkKeyboardColor.PRIMARY, payload={"type": '+1'})
    keyboard_karta_bluda.add_line()
    keyboard_karta_bluda.add_callback_button(label='Добавить в корзину', color=VkKeyboardColor.PRIMARY,
                                             payload={"type": 'add_in_bas'})
    keyboard_karta_bluda.add_line()
    keyboard_karta_bluda.add_callback_button(label='<', color=VkKeyboardColor.PRIMARY, payload={"type": '<'})
    keyboard_karta_bluda.add_callback_button(label=f'{page}\\{all_page}', color=VkKeyboardColor.PRIMARY, payload={"type": 'закуски'})
    keyboard_karta_bluda.add_callback_button(label='>', color=VkKeyboardColor.PRIMARY, payload={"type": '>'})
    keyboard_karta_bluda.add_line()
    keyboard_karta_bluda.add_button(label='Категории', color=VkKeyboardColor.PRIMARY, payload={"type": 'закуски'})
    return keyboard_karta_bluda

print(food_sdb.get_records("order"))

# Запускаем бот
vk_session = VkApi(token=GROUP_TOKEN, api_version=API_VERSION)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)
upload=VkUpload(vk_session)


spravka_text = """
                📚 Справка по Командам Бота:

                /addreview - Оставить отзыв о блюде или сервисе.
                /orders - Просмотреть список ваших заказов и их статус.
                /basket - Перейти в корзину для управления выбранными блюдами.
                /categories - Посмотреть список доступных категорий блюд в меню.

                🌟 Дополнительные Команды:

                /start - Начать общение с ботом.
                /help - Получить справку и поддержку.

                💡 Правила и Рекомендации:

                Отзывы: Просим вас не использовать нецензурную лексику в отзывах.

                Черный список (ЧС): Нарушение правил (например, частые отмены заказов) может привести к внесению в ЧС.

                🚨 Помните:
                Мы ценим ваши отзывы, но просим выражать свое мнение уважительно.
                Повторные нарушения правил могут привести к ограничениям в использовании сервиса

                📞 Контакты Поддержки:
                📧 Электронная почта: support@example.com
                📱 Телефон: +123456789

                🤝 Мы готовы помочь вам с любыми вопросами и обеспечить лучший опыт использования нашего сервиса. Не стесняйтесь обращаться! 🍽️✨
                Спасибо за понимание! 🍽️✨
            """

keyboard_start = VkKeyboard(one_time=False, inline=False)
keyboard_start.add_button(label='🍽️ Меню Блюд', color=VkKeyboardColor.POSITIVE, payload={"type": "text"})
keyboard_start.add_line()
keyboard_start.add_button(label='🛒 Корзина', color=VkKeyboardColor.POSITIVE, payload={"type": "text"})
keyboard_start.add_line()
keyboard_start.add_button(label='🚚 Активные заказы', color=VkKeyboardColor.POSITIVE, payload={"type": "text"})
keyboard_start.add_line()
keyboard_start.add_button(label='✏️ Добавить отзыв', color=VkKeyboardColor.POSITIVE, payload={"type": "text"})
keyboard_start.add_line()
keyboard_start.add_button(label='❓  Справка', color=VkKeyboardColor.POSITIVE, payload={"type": "text"})

keyboard_basket=VkKeyboard(one_time=False, inline=True)
keyboard_basket.add_callback_button(label='Оформить заказ', color=VkKeyboardColor.PRIMARY, payload={"type": 'add_order'})
keyboard_basket.add_line()
keyboard_basket.add_callback_button(label='Очистить корзину', color=VkKeyboardColor.PRIMARY, payload={"type": 'clear_basket'})

keybord_add_order=VkKeyboard(one_time=False,inline=True)
keybord_add_order.add_callback_button(label='Подвердить данные', color=VkKeyboardColor.PRIMARY, payload={"type": 'yes_data'})
keybord_add_order.add_line()
keybord_add_order.add_callback_button(label='Обновить данные', color=VkKeyboardColor.PRIMARY, payload={"type": 'no_data'})

keybord_payment_method=VkKeyboard(one_time=False,inline=True)
keybord_payment_method.add_callback_button(label='По карте', color=VkKeyboardColor.PRIMARY, payload={"type": 'по карте'})
keybord_payment_method.add_line()
keybord_payment_method.add_callback_button(label='Наличными', color=VkKeyboardColor.PRIMARY, payload={"type": 'наличными'})


keybord_update_user_data=VkKeyboard(one_time=False,inline=True)
keybord_update_user_data.add_callback_button(label='Имя', color=VkKeyboardColor.PRIMARY, payload={"type": 'имя'})
keybord_update_user_data.add_line()
keybord_update_user_data.add_callback_button(label='Номер телефона', color=VkKeyboardColor.PRIMARY, payload={"type": 'телефон'})
keybord_update_user_data.add_line()
keybord_update_user_data.add_callback_button(label='Адрес', color=VkKeyboardColor.PRIMARY, payload={"type": 'адрес'})

dishes_categories=food_sdb.get_uniq_cats()
keyboard_menu_blud = VkKeyboard(one_time=False, inline=True)
for i in range(len(dishes_categories)):
    if i==len(dishes_categories)-1:
        keyboard_menu_blud.add_callback_button(label=dishes_categories[i], color=VkKeyboardColor.PRIMARY, payload={"type": dishes_categories[i]})
    else:
        keyboard_menu_blud.add_callback_button(label=dishes_categories[i], color=VkKeyboardColor.PRIMARY, payload={"type": dishes_categories[i]})
        keyboard_menu_blud.add_line()


keyboard_comment = VkKeyboard(one_time=False, inline=True)
keyboard_comment.add_callback_button(label="На заказ", color=VkKeyboardColor.PRIMARY, payload={"type": "order_comment"})
keyboard_comment.add_line()
keyboard_comment.add_callback_button(label="На блюдо", color=VkKeyboardColor.PRIMARY, payload={"type": "good_comment"})

keybord_rating=VkKeyboard(one_time=False,inline=True)
keybord_rating.add_callback_button(label='🌟🌟🌟🌟🌟', color=VkKeyboardColor.PRIMARY, payload={"type": '5'})
keybord_rating.add_line()
keybord_rating.add_callback_button(label='🌟🌟🌟🌟', color=VkKeyboardColor.PRIMARY, payload={"type": '4'})
keybord_rating.add_line()
keybord_rating.add_callback_button(label='🌟🌟🌟', color=VkKeyboardColor.PRIMARY, payload={"type": '3'})
keybord_rating.add_line()
keybord_rating.add_callback_button(label='🌟🌟', color=VkKeyboardColor.PRIMARY, payload={"type": '2'})
keybord_rating.add_line()
keybord_rating.add_callback_button(label='🌟', color=VkKeyboardColor.PRIMARY, payload={"type": '1'})


start_comands = ["start", "начать", "старт", "начало", "бот"]
image='pfsta.jpg'
count = 0
page = 1
step=0
update_data=False
add_ord_comment=False
add_good_comment=False
del_order=False
order_num_for_del=0
order_id_for_com=0
good_id_for_com=0
data_for_update=''
val=''

new_user_dict={}

for event in longpoll.listen():

    if event.type == VkBotEventType.MESSAGE_NEW:

        if event.obj.message['text'].lower() in start_comands:
            users_list=food_sdb.get_vk_ids()

            if event.obj.message['from_id'] in users_list:
                user=food_sdb.get_urecord_vk(event.obj.message['from_id'])

                attachments=[]
                upload_image=upload.photo_messages(photos=image)[0]
                attachments.append("photo{}_{}".format(upload_image['owner_id'],upload_image['id']))

                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    keyboard=keyboard_start.get_keyboard(),
                    message=f"""
                            Добро пожаловать в наш бот, {user['name']}! 🌟 
                            Мы рады видеть вас здесь. Готовы помочь с выбором блюд или обработкой заказа. 
                            Чем могу помочь сегодня?
                            """,
                    )
            elif event.obj.message['from_id'] not in users_list:
                vk.messages.send(
                                user_id=event.obj.message['from_id'],
                                random_id=get_random_id(),
                                peer_id=event.obj.message['from_id'],
                                message='Приветствую вас! 😊 Давайте с вами познакомимся!')

                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    message='🌟 Как мне к вам обращаться? Пожалуйста, укажите ваше имя.')

                step+=1

        elif event.obj.message['text'] not in start_comands and step==1:

            new_user_dict['black_list']=False
            new_user_dict['vk_id']=event.obj.message['from_id']

            new_user_dict['name']=event.obj.message['text']
            step+=1

            vk.messages.send(
                user_id=event.obj.message['from_id'],
                random_id=get_random_id(),
                peer_id=event.obj.message['from_id'],
                message='🎂 Спасибо! А сколько вам лет? Нам важно знать ваш возраст.')

        elif event.obj.message['text'] not in start_comands and step == 2:

            try:
                int(event.obj.message['text'])
                new_user_dict['age'] = event.obj.message['text']
                step += 1

                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    message="Спасибо! Теперь введите ваш номер телефонаю.")

            except:
                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    message='Введены некоректные данные. Повторите.')
        
        elif event.obj.message['text'] not in start_comands and step == 3:

            phone_val="'{0}'[0]=='+' and '{0}'[1:].isdigit() and len('{0}')==13"

            if eval(phone_val.format(event.obj.message['text']))==True:
                new_user_dict['phone']=event.obj.message['text']
                step+=1

                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    message='🏡 Спасибо за предоставленную информацию! Для успешной доставки нам нужен ваш адрес. Пожалуйста, укажите город, улицу, номер дома, подъезд и квартиру, если возможно.')

            else:
                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    message='Введены некоректные данные. Повторите.')

        elif event.obj.message['text'] not in start_comands and step == 4:

            new_user_dict['delivery_address'] = event.obj.message['text']
            step += 1

            vk.messages.send(
                user_id=event.obj.message['from_id'],
                random_id=get_random_id(),
                peer_id=event.obj.message['from_id'],
                keyboard=keyboard_start.get_keyboard(),
                message='🎉 Отлично! Теперь у нас есть все необходимые данные. Спасибо за сотрудничество! Если у вас есть ещё какие-то вопросы или пожелания, не стесняйтесь сообщить нам. Мы готовы помочь!')

            food_sdb.add_record("user",**new_user_dict)
            step=0
            new_user_dict={}

        elif event.obj.message['text'] not in start_comands and update_data == True:
            food_sdb.update_record("user",{f'{data_for_update}':event.obj.message['text']},id=user['id'])
            update_data=False
            user=food_sdb.get_urecord_vk(event.obj.message['from_id'])
            vk.messages.send(
                user_id=event.obj.message['from_id'],
                random_id=get_random_id(),
                peer_id=event.obj.message['from_id'],
                keyboard=keybord_add_order.get_keyboard(),
                message=f"""
                            Пожалуйста, подтверди, верны ли следующие сведения:
                            Имя: {user['name']}
                            Телефон: {user['phone']}
                            Адрес: {user['delivery_address']}
                            Если есть какие-то изменения или несоответствия, 
                            дай знать, чтобы мы могли обновить информацию.
                            Спасибо!
                        """)

        elif event.obj.message['text'] == '🍽️ Меню Блюд' or event.obj.message['text'] == "Категории":
            vk.messages.send(
                user_id=event.obj.message['from_id'],
                random_id=get_random_id(),
                peer_id=event.obj.message['from_id'],
                keyboard=keyboard_menu_blud.get_keyboard(),
                message='Выбери категорию блюд 🍕🍣🥗🍝🍨')

        elif event.obj.message['text'] == '🛒 Корзина':

            basket=food_sdb.get_basket_vk(event.obj.message['from_id'])

            if len(basket)==0:
                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    message="""🛒 Ваша корзина пока пуста!
                                Загляните в наше меню и добавьте в нее свои любимые блюда. 
                                Мы уверены, у нас есть что-то вкусное для вас! 
                                Если у вас есть вопросы или нужна помощь, дайте нам знать.
                                Спасибо за ваш интерес к нашим блюдам! 🍽️🌟
                            """)
            else:
                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    message="🛒 **Ваша корзина:**")

                order_price=0
                max_time=0
                spisok_tovarov=""
                for i in range(len(basket)):
                    order_price=float(basket[i]['total_price'])+order_price
                    if max_time<int(basket[i]['good_id']['cooking_time']):
                        max_time=int(basket[i]['good_id']['cooking_time'])
                    spisok_tovarov+=f"{basket[i]['good_id']['name']}: {basket[i]['amount']} шт.\n"
                    vk.messages.send(
                        user_id=event.obj.message['from_id'],
                        random_id=get_random_id(),
                        peer_id=event.obj.message['from_id'],
                        message=f"""
                                    {i+1}. 🍔 **{basket[i]['good_id']['name']}**
                                    ФОТОГРАФИЯ
                                    Количество: {basket[i]['amount']}
                                    Cтоимость: {basket[i]['total_price']} BUN
                                """)

                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    keyboard=keyboard_basket.get_keyboard(),
                    message=f"""
                            **Общая сумма заказа: {order_price} BUN**
                            Чтобы оформить заказ, выберите соответствующую опцию из меню.
                            Если у вас есть изменения или вопросы, дайте нам знать.
                            Спасибо за ваш заказ! 🚀
                            """)

        elif event.obj.message['text'] == '🚚 Активные заказы':
            ords=food_sdb.get_uactive_order_vk(event.obj.message['from_id'])

            if len(ords)==0:
                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    message="В данный момент у вас нет активных заказов!")
            else:
                vk.messages.send(
                    user_id=event.obj.message['from_id'],
                    random_id=get_random_id(),
                    peer_id=event.obj.message['from_id'],
                    message="🛒 Активные заказы 🚚")

                for i in range(len(ords)):

                    keyboard_otmena_z = VkKeyboard(one_time=False, inline=True)
                    keyboard_otmena_z.add_callback_button(label="Отменить", color=VkKeyboardColor.PRIMARY,
                                                          payload={"type": f"del_ord {ords[i]['order_number']}" })

                    vk.messages.send(
                        user_id=event.obj.message['from_id'],
                        random_id=get_random_id(),
                        peer_id=event.obj.message['from_id'],
                        keyboard=keyboard_otmena_z.get_keyboard(),
                        message=f"""
                                    Заказ #{ords[i]['order_number']}
                                    📅 Дата и время заказа: {ords[i]['order_time']}
                                    
                                    ⏰ Время доставки:
                                    {ords[i]['delivery_time']}
                                    
                                    🍽️ Блюда:
                        
                                    - {ords[i]['basket_id'][0]['good_id']['name']}-{ords[i]['basket_id'][0]['amount']} шт.
                                    
                                    Сумма: {ords[i]['order_price']} BUN
                                    """)

        elif event.obj.message['text'] not in start_comands and del_order == True:

            del_order=False
            food_sdb.update_record("order",{'status':'Отменен','cancellation_reason':event.obj.message['text']},order_number=order_num_for_del)
            vk.messages.send(
                user_id=event.obj.message['from_id'],
                random_id=get_random_id(),
                peer_id=event.obj.message['from_id'],
                message="Спасибо за ваш ответ! Будем жадть от вас новых заказов!")

        elif event.obj.message['text'] == '✏️ Добавить отзыв':

            vk.messages.send(
                user_id=event.obj.message['from_id'],
                random_id=get_random_id(),
                peer_id=event.obj.message['from_id'],
                keyboard=keyboard_comment.get_keyboard(),
                message="На что хотите ставить отзыв?")

        elif event.obj.message['text'] not in start_comands and add_ord_comment == True:
            food_sdb.update_record("ordercomment", {'text':event.obj.message['text']},
                                   order_number_id=order_id_for_com)
            add_ord_comment=False

        elif event.obj.message['text'] not in start_comands and add_good_comment == True:
            food_sdb.update_record("goodcomment", {'text':event.obj.message['text']},
                                   good_id=good_id_for_com)
            add_good_comment=False


    elif event.type == VkBotEventType.MESSAGE_EVENT:
        if event.object.payload.get('type') in dishes_categories:

            bluda_from_cat=food_sdb.get_goods_by_cat(event.object.payload.get('type'))

            available=''
            if bluda_from_cat[page-1]['available']==True:
                available='Есть в наличии'
            else:
                available='Нет в наличии'

            last_id = vk.messages.edit(
                peer_id=event.obj.peer_id,
                message=f"""
                        {bluda_from_cat[page - 1]['name']}
                        {bluda_from_cat[page-1]['description']}
                        Время приготовления: {bluda_from_cat[page - 1]['cooking_time']} мин.
                        Ценa: {bluda_from_cat[page - 1]['price']}
                        {available}
                        """,
                conversation_message_id=event.obj.conversation_message_id,
                keyboard=generation_karta_bluda(count,page,len(bluda_from_cat)).get_keyboard(),
                attachment=','.join(attachments))

        elif event.object.payload.get('type') == "+1":

            count+=1

            last_id = vk.messages.edit(
                peer_id=event.obj.peer_id,
                message=f"""
                        {bluda_from_cat[page - 1]['name']}
                        {bluda_from_cat[page - 1]['description']}
                        Время приготовления: {bluda_from_cat[page - 1]['cooking_time']} мин.
                        Ценa: {bluda_from_cat[page - 1]['price']}
                        {available}
                        """,
                conversation_message_id=event.obj.conversation_message_id,
                keyboard=generation_karta_bluda(count, page, len(bluda_from_cat)).get_keyboard(),
                attachment=','.join(attachments))

        elif event.object.payload.get('type') == "-1":
            if count > 0:
                count -= 1

                last_id = vk.messages.edit(
                    peer_id=event.obj.peer_id,
                    message=f"""
                    {bluda_from_cat[page - 1]['name']}
                    {bluda_from_cat[page - 1]['description']}
                    Время приготовления: {bluda_from_cat[page - 1]['cooking_time']} мин.
                    Ценa: {bluda_from_cat[page - 1]['price']}
                    {available}
                    """,
                    conversation_message_id=event.obj.conversation_message_id,
                    keyboard=generation_karta_bluda(count, page, len(bluda_from_cat)).get_keyboard(),
                    attachment=','.join(attachments))
            else:
                print("нельзя сотворить здесь")

        elif event.object.payload.get('type') == ">":

            if page<len(bluda_from_cat):
                count = 0
                page+=1

                last_id = vk.messages.edit(
                    peer_id=event.obj.peer_id,
                    message=f"""
                            {bluda_from_cat[page - 1]['name']}
                            {bluda_from_cat[page - 1]['description']}
                            Время приготовления: {bluda_from_cat[page - 1]['cooking_time']} мин.
                            Ценa: {bluda_from_cat[page - 1]['price']}
                            {available}
                            """,
                    conversation_message_id=event.obj.conversation_message_id,
                    keyboard=generation_karta_bluda(count, page, len(bluda_from_cat)).get_keyboard(),
                    attachment=','.join(attachments))

        elif event.object.payload.get('type') == "<":

            if page > 1:
                count = 0
                page -= 1

                last_id = vk.messages.edit(
                    peer_id=event.obj.peer_id,
                    message=f"""
                                {bluda_from_cat[page - 1]['name']}
                                {bluda_from_cat[page - 1]['description']}
                                Время приготовления: {bluda_from_cat[page - 1]['cooking_time']} мин.
                                Ценa: {bluda_from_cat[page - 1]['price']}
                                {available}
                                """,
                    conversation_message_id=event.obj.conversation_message_id,
                    keyboard=generation_karta_bluda(count, page, len(bluda_from_cat)).get_keyboard(),
                    attachment=','.join(attachments))

        elif event.object.payload.get('type') == "add_in_bas":

            food_sdb.add_record('basket',amount=count,total_price=count*bluda_from_cat[page-1]['price'],user_id=user['id'],good_id=bluda_from_cat[page-1]['id'],added_to_order=0)
            vk.messages.send(
                user_id=event.obj.peer_id,
                random_id=get_random_id(),
                peer_id=event.obj.peer_id,
                message="Блюдо добавлено в корзину")

        elif event.object.payload.get('type') == "add_order":

            last_id = vk.messages.edit(
                peer_id=event.obj.peer_id,
                message=f"""
                            Пожалуйста, подтверди, верны ли следующие сведения:
                            Имя: {user['name']}
                            Телефон: {user['phone']}
                            Адрес: {user['delivery_address']}
                            Если есть какие-то изменения или несоответствия, 
                            дай знать, чтобы мы могли обновить информацию.
                            Спасибо!
                        """,
                conversation_message_id=event.obj.conversation_message_id,
                keyboard=keybord_add_order.get_keyboard())

        elif event.object.payload.get('type') == "clear_basket":
            for i in range(len(basket)):
                food_sdb.delete_record("basket",user_id=basket[i]['user_id']['id'])

        elif event.object.payload.get('type') == "yes_data":
            last_id = vk.messages.edit(
                peer_id=event.obj.peer_id,
                message="Выберите удобный способ оплаты:",
                conversation_message_id=event.obj.conversation_message_id,
                keyboard=keybord_payment_method.get_keyboard())

        elif event.object.payload.get('type') == "no_data":
            last_id = vk.messages.edit(
                peer_id=event.obj.peer_id,
                message="""
                            Конечно, мы готовы обновить ваши данные.
                            Пожалуйста, уточните, какие именно сведения вы хотели бы изменить, 
                            и предоставьте новую информацию. 
                            Будем рады помочь!
                        """,
                conversation_message_id=event.obj.conversation_message_id,
                keyboard=keybord_update_user_data.get_keyboard())


        elif event.object.payload.get('type') in ("по карте","наличными"):
            order_time=datetime.now()

            last_id = vk.messages.edit(
                peer_id=event.obj.peer_id,
                message=f"""
                            🌟 Спасибо за ваш заказ! 🌟

                            Детали заказа:
                            ---------------------
                            📅 Дата и время заказа: {order_time}
                            💼 Номер заказа: #{1}
                            
                            🛍️ Содержимое заказа:
                            ---------------------
                            {spisok_tovarov}
                            
                            💳 Сумма к оплате: {order_price} BUN
                            
                            📍 Адрес доставки: {user['delivery_address']}
                            
                            📞 Контактный номер:
                            {user['phone']}
                            
                            📢 Способ оплаты: {event.object.payload.get('type')}
                            
                            🚀 Статус заказа: В обработке
                            
                            📌 Пожалуйста, ожидайте подтверждения заказа от нашей команды. Если у вас есть какие-то вопросы, не стесняйтесь связаться с нами.
                            
                            Благодарим за выбор нашего сервиса! Приятного аппетита и отличного дня! 🌮🚚
                        """,
                conversation_message_id=event.obj.conversation_message_id)

            orders=food_sdb.get_records("order")
            food_sdb.add_record("order",order_time=order_time,delivery_time=order_time+timedelta(hours=0, minutes=max_time+30),order_price=order_price,status="в обработке",payment_method=event.object.payload.get('type'),user_id=user['id'],basket_id=basket[0]['id'],user_name=user['name'],age=user['age'],phone=user['phone'],delivery_address=user['delivery_address'],order_number=orders[len(orders)-1]['id']+1)

            for i in range(len(basket)):
                food_sdb.update_record("basket", {'added_to_order':1},id=basket[i]['id'])

        elif event.object.payload.get('type') in ("имя","телефон","адрес"):
            if event.object.payload.get('type')=="имя":
                data_for_update="name"
            elif event.object.payload.get('type')=="телефон":
                data_for_update="phone"
            else:
                data_for_update="delivery_address"
            update_data=True
            last_id = vk.messages.edit(
                peer_id=event.obj.peer_id,
                message=f"Введите {event.object.payload.get('type')}",
                conversation_message_id=event.obj.conversation_message_id)

        elif event.object.payload.get('type')=="order_comment":

            delivered_order=food_sdb.get_delivered_order_vk(user["vk_id"])

            last_id = vk.messages.edit(
                peer_id=event.obj.peer_id,
                message=f"Ваши доставленные заказы",
                conversation_message_id=event.obj.conversation_message_id)

            for i in range(len(delivered_order)):
                keyboard_add_comment = VkKeyboard(one_time=False, inline=True)
                keyboard_add_comment.add_callback_button(label="Оставить отзыв", color=VkKeyboardColor.PRIMARY,
                                                         payload={"type": f"add_ord_com {delivered_order[i]['id']}"})

                vk.messages.send(
                    user_id=event.obj.peer_id,
                    random_id=get_random_id(),
                    peer_id=event.obj.peer_id,
                    keyboard=keyboard_add_comment.get_keyboard(),
                    message=f"Заказ номер {delivered_order[i]['order_number']}")


        elif event.object.payload.get('type') == "good_comment":

            goods=food_sdb.get_uordered_goods_vk(user['vk_id'])

            last_id = vk.messages.edit(
                peer_id=event.obj.peer_id,
                message=f"Вот блюда, которые вы заказывали",
                conversation_message_id=event.obj.conversation_message_id)

            for i in range(len(goods)):
                keyboard_add_comment = VkKeyboard(one_time=False, inline=True)
                keyboard_add_comment.add_callback_button(label="Оставить отзыв", color=VkKeyboardColor.PRIMARY,
                                                         payload={"type": f"add_good_com {goods[i]['id']}"})

                vk.messages.send(
                    user_id=event.obj.peer_id,
                    random_id=get_random_id(),
                    peer_id=event.obj.peer_id,
                    keyboard=keyboard_add_comment.get_keyboard(),
                    message=f"{goods[i]['name']}")


        elif event.object.payload.get('type').split()[0] == "del_ord":
            order_num_for_del= int(event.object.payload.get('type').split()[1])
            vk.messages.send(
                user_id=event.obj.peer_id,
                random_id=get_random_id(),
                peer_id=event.obj.peer_id,
                message=f"Заказ {event.object.payload.get('type').split()[1]} отменен")

            vk.messages.send(
                user_id=event.obj.peer_id,
                random_id=get_random_id(),
                peer_id=event.obj.peer_id,
                message=f"Введите причину отмены заказа")

            del_order=True

        elif event.object.payload.get('type').split()[0] == "add_ord_com":
            val='order'
            order_id_for_com=int(event.object.payload.get('type').split()[1])
            vk.messages.send(
                user_id=event.obj.peer_id,
                random_id=get_random_id(),
                peer_id=event.obj.peer_id,
                keyboard=keybord_rating.get_keyboard(),
                message="На сколько вы оцените заказ")

        elif event.object.payload.get('type').split()[0] == "add_good_com":
            val="good"
            good_id_for_com=int(event.object.payload.get('type').split()[1])
            vk.messages.send(
                user_id=event.obj.peer_id,
                random_id=get_random_id(),
                peer_id=event.obj.peer_id,
                keyboard=keybord_rating.get_keyboard(),
                message="На сколько вы оцените заказ")


        elif event.object.payload.get('type') in ("1","2","3","4","5"):

            if val=='order':

                food_sdb.add_record("ordercomment",eval=event.object.payload.get('type'),user_id=user['id'],order_number_id=int(order_id_for_com))
                add_ord_comment=True

                vk.messages.send(
                    user_id=event.obj.peer_id,
                    random_id=get_random_id(),
                    peer_id=event.obj.peer_id,
                    message="Оставьте коментарий к заказу")
            elif val=="good":
                food_sdb.add_record("goodcomment", eval=event.object.payload.get('type'), user_id=user['id'],
                                    good_id=int(good_id_for_com))
                add_good_comment = True

                vk.messages.send(
                    user_id=event.obj.peer_id,
                    random_id=get_random_id(),
                    peer_id=event.obj.peer_id,
                    message="Оставьте коментарий к блюду")





