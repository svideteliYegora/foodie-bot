from functools import reduce
from peewee import *
from typing import List, Dict, Tuple, Any, Type



# соединение с нашей базой данных
con = SqliteDatabase('food_service_db.db', check_same_thread=False)


class BaseModel(Model):
    class Meta:
        database = con


class User(BaseModel):
    id = IntegerField(primary_key=True)
    vk_id = IntegerField(null=True)
    tg_id = IntegerField(null=True)
    name = CharField()
    age = IntegerField()
    phone = CharField()
    delivery_address = CharField()
    black_list = BooleanField(default=False)


class Admin(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    user_id = IntegerField()
    level = BooleanField(default=False)


class Good(BaseModel):
    id = IntegerField(primary_key=True)
    name = TextField()
    price = FloatField()
    cooking_time = TextField()
    available = BooleanField(default=True)
    category = TextField()
    image = TextField()
    tg_image_id = TextField(null=True)
    vk_image_id = TextField(null=True)
    description = TextField()


class Basket(BaseModel):
    id = IntegerField(primary_key=True)
    amount = IntegerField()
    total_price = FloatField()
    user_id = ForeignKeyField(User, backref='baskets')
    good_id = ForeignKeyField(Good, backref='baskets')
    added_to_order = BooleanField(default=False)


class Order(BaseModel):
    id = IntegerField(primary_key=True)
    order_time = TimestampField()
    delivery_time = TimestampField()
    order_price = FloatField()
    status = TextField()
    payment_method = TextField()
    cancellation_reason = TextField(null=True)
    user_id = ForeignKeyField(User, backref='orders')
    basket_id = ForeignKeyField(Basket, backref='orders')
    order_number = IntegerField()
    user_name = CharField(null=True)
    age = IntegerField(null=True)
    phone = CharField(null=True)
    delivery_address = CharField(null=True)


class GoodComment(BaseModel):
    id = IntegerField(primary_key=True)
    eval = IntegerField()
    text = TextField(null=True)
    validate = BooleanField(null=True)
    user_id = ForeignKeyField(User, backref='good_comments')
    good_id = ForeignKeyField(Good, backref='good_comments')


class OrderComment(BaseModel):
    id = IntegerField(primary_key=True)
    eval = IntegerField()
    text = TextField(null=True)
    validate = BooleanField(null=True)
    user_id = ForeignKeyField(User, backref='order_comments')
    order_number = ForeignKeyField(Order, to_field="order_number", backref='order_comments')


con.create_tables([User, Admin, Good, Basket, Order, GoodComment, OrderComment])

class FoodServiceDB:
    def __init__(self, con: SqliteDatabase):
        self.con: SqliteDatabase = con

    @staticmethod
    def __normalize_table_name(table: str) -> str:
        """
        Нормализация имени таблицы для соответствия ожидаемым названиям классов.

        :param table: Имя таблицы для нормализации.
        :return: Нормализованное имя таблицы в виде строки.
        """
        if table.lower() == "ordercomment":
            return "OrderComment"
        elif table.lower() == "goodcomment":
            return "GoodComment"
        else:
            return table.capitalize()

    @staticmethod
    def __get_field_values(table: Type, field: str) -> Tuple:
        """
        Получение значений поля для текущей таблицы.

        :param table: Модель данных.
        :param field: Поле данных.
        :return: Кортеж значений текущего поля.
        """
        try:
            return tuple(getattr(item, field) for item in table.select() if getattr(item, field) is not None)
        except Exception as e:
            raise ValueError(f"Произошла ошибка при получении значений поля: {str(e)}")

    @staticmethod
    def __get_basket_data(ufield: str, user_id: int) -> List[Dict]:
        """
        Получение данных корзины для пользователя
        по указанному полю, его идентификатору и значению - False для поля 'Basket.added_to_order'.

        :param ufield: Поле из таблицы User: tg_id или vk_id.
        :param user_id: Идентификатор пользователя.
        :return: Список словарей с данными о корзине, включая данные пользователя и товара.
        """
        try:
            u_id = User.get_or_none(getattr(User, ufield) == user_id)

            if u_id:
                dt_list = []
                for item in u_id.baskets:
                    if not item.added_to_order:
                        good = Good.get_by_id(item.good_id)
                        bask_data = item.__data__
                        bask_data['user_id'] = u_id.__data__
                        bask_data['good_id'] = good.__data__
                        dt_list.append(bask_data)
                return dt_list
            else:
                raise ValueError(f"Запись в таблице 'User', где '{ufield}'== '{user_id}' не существует.")
        except DoesNotExist:
            raise ValueError(f"Запись в таблице 'User', где '{ufield}'== '{user_id}' не существует.")
        except Exception as e:
            raise ValueError(f"Произошла ошибка при получении данных корзины: {str(e)}")

    @staticmethod
    def __get_union_basket_entries(user_id: int, good_id: int, field: str) -> Tuple[Any]:
        """
        Получение общего количества и общей суммы для объединенных записей корзины для пользователя и конкретного товара.

        :param user_id: Идентификатор пользователя.
        :param good_id: Идентификатор товара.
        :param field: Поле для идентификации пользователя ("tg_id" или "vk_id").
        :return: Кортеж, содержащий общее количество и общую сумму, если записи существуют, в противном случае пустой кортеж.
        """
        try:
            u_id = User.get_or_none(getattr(User, field) == user_id)
            data = (Basket
                    .select(fn.SUM(Basket.amount).alias('total_amount'),
                            fn.SUM(Basket.total_price).alias('total_price')
                            )
                    .where((Basket.user_id == u_id) & (Basket.good_id == good_id) & (Basket.added_to_order == False))
                    .group_by(Basket.user_id, Basket.good_id)
                    .first())
            return (data.total_amount, data.total_price) if data else ()
        except Exception as e:
            raise ValueError(f"Произошла ошибка при получении общего количества и суммы корзины: {str(e)}")

    def execute_sql_query(self, query: str, params: Any = None) -> Any:
        """
        Выполнение SQL-запроса к подключенной базе данных.

        :param query: Строка SQL-запроса.
        :param params: Кортеж значений для подстановки в SQL-запрос или None, если параметры не требуются.
        :return: Результат запроса или None в случае ошибки.
        """
        try:
            res = self.con.execute_sql(query, params if params else ())
            return res
        except Exception as e:
            raise ValueError(f"Произошла ошибка при выполнении SQL-запроса: {str(e)}")

    def delete_all_records(self, table: str, **params: Dict) -> int:
        """
        Удаление всех записей из указанной таблицы, которые соответвуют переданным параметрам.

        :param table: Название таблицы для удаления записи.
        :param params: Словарь с парами поле-значение для условия удаления записи.
        :return: Количество удаленных записей в таблице.
        """
        table = self.__normalize_table_name(table)
        model = globals().get(table)

        if model and issubclass(model, Model):
            try:
                # Получаем значение id из params
                record_id = params.pop('id', None)
                if record_id:
                    deleted_count = model.delete_by_id(record_id)
                    return deleted_count

                # Строим условие
                query = reduce(lambda q, item: q.where(getattr(model, item[0]) == item[1]), params.items(),
                               model.delete())

                deleted_count = query.execute()
                return deleted_count
            except Exception as e:
                raise ValueError(f"Произошла ошибка при удалении записей из таблицы '{table}': {str(e)}")
        else:
            raise ValueError(f"Таблица '{table}' не поддерживается или не существует.")

    def delete_record(self, table: str, **params: Dict) -> int:
        """
        Удаление одной записи из указанной таблицы, соответствующей переданным параметрам.

        :param table: Название таблицы для удаления записи.
        :param params: Словарь с парами поле-значение для условия удаления записи.
        :return: Количество удаленных записей (0 или 1).
        """
        table = self.__normalize_table_name(table)
        model = globals().get(table)

        if model and issubclass(model, Model):
            try:

                record_id = params.pop('id', None)
                if record_id:
                    return model.delete_by_id(record_id)

                record = model.get(**params)

                # Если есть id, проверяем его
                if record_id is not None and record.id != record_id:
                    raise ValueError(f"Запись с id={record_id} не найдена в таблице '{table}'.")

                # Удаляем запись
                record.delete_instance()

                return 1
            except model.DoesNotExist:
                return 0
            except Exception as e:
                raise ValueError(f"Произошла ошибка при удалении записей из таблицы '{table}': {str(e)}")
        else:
            raise ValueError(f"Таблица '{table}' не поддерживается или не существует.")

    def update_record(self, table: str, values: Dict, **params: Dict) -> int:
        """
        Обновление записей в указанной таблице с заданными значениями и условиями.

        :param table: Название таблицы для обновления.
        :param values: Словарь значений для обновления.
        :param params: Словарь параметров для условия выборки записей.
        :return: Количество обновленных записей.
        """
        table = self.__normalize_table_name(table)
        model = globals().get(table)
        if model and issubclass(model, Model):
            try:
                # Получаем значение id из params
                record_id = params.pop('id', None)

                # Строим условие
                query = reduce(lambda q, item: q.where(getattr(model, item[0]) == item[1]), params.items(),
                               model.update(values))

                # Если есть id, добавляем его к условию
                if record_id is not None:
                    query = query.where(model.id == record_id)
                res = query.execute()
                return res
            except Exception as e:
                raise ValueError(f"Произошла ошибка при обновлении записи в таблицы '{table}': {str(e)}")
        else:
            raise ValueError(f"Таблица '{table}' не поддерживается или не существует.")

    def add_record(self, table: str, **values: Dict[str, Any]) -> Dict:
        """
        Добавление новой записи в указанную таблицу с заданными параметрами.

        :param table: Название таблицы для добавления записи.
        :param values: Словарь с парами поле-значение для новой записи.
        :return: Словарь с данными новой записи при успешном добавлении, в противном случае будет вызвано исключение.
        """
        table = self.__normalize_table_name(table)
        model = globals().get(table)
        if model and issubclass(model, Model):
            try:
                new_rec: Model = model.create(**values)
                new_rec.save()
                if new_rec:
                    return new_rec.__data__
                else:
                    raise ValueError(f"Ошибка добавления новой записи в таблицу '{table}'")
            except Exception as e:
                raise ValueError(f"Произошла ошибка при добавлении новой записей в таблицу '{table}': {str(e)}")

        else:
            raise ValueError(f"Таблица '{table}' не поддерживается или не существует.")

    def get_record(self, table: str, **params: dict) -> Dict:
        """
        Получение записи из указанной таблицы с заданными параметрами,
        если параметры не указаны, метод вернет первую запись из указанной таблицы.

        :param table: Название таблицы.
        :param params: Словарь параметров для условия выборки записи.
        :return: Словарь с данными найденной записи или пустой словарь, если запись не найдена.
        """
        table = self.__normalize_table_name(table)
        model = globals().get(table)

        if model and issubclass(model, Model):
            try:
                # Получаем значение id из params
                record_id = params.pop('id', None)
                if record_id:
                    try:
                        res = model.get_by_id(record_id)
                    except DoesNotExist:
                        return {}
                else:
                    # Строим условие
                    query = reduce(lambda q, item: q.where(getattr(model, item[0]) == item[1]), params.items(),
                                   model.select())
                    # Получаем запись
                    res = query.first()
                return res.__data__ if res else {}
            except Exception as e:
                raise ValueError(f"Произошла ошибка при получении записи из таблицы '{table}': {str(e)}")
        else:
            raise ValueError(f"Таблица '{table}' не поддерживается или не существует.")

    def get_records(self, table: str, **params: dict) -> List[Any]:
        """
        Получение всех записей из указанной таблицы.

        :param table: Имя таблицы.
        :param params: Параметры для выборки записей.
        :return: Список словарей с данными если они есть и пустой список в противном случае.
        """
        try:
            table = self.__normalize_table_name(table)
            model = globals().get(table)
            if model and issubclass(model, Model):
                if params:
                    model_id = params.pop("id", None)
                    if model_id:
                        query = model.select().where(model.id == model_id)
                    else:
                        # Строим условие
                        query = reduce(lambda q, item: q.where(getattr(model, item[0]) == item[1]), params.items(),
                                       model.select())
                else:
                    query = model.select()
                dt = query.execute()
                return [i.__data__ for i in dt] if dt else []
            raise ValueError(f"Таблица '{table}' не поддерживается или не существует.")
        except Exception as e:
            raise ValueError(f"Произошла ошибка при получении записи из таблицы '{table}': {str(e)}")

    @staticmethod
    def get_urecord_tg(user_id: int) -> Dict:
        """
        Получение записи из таблицы User по TG user_id (tg_id).

        :param user_id: Идентификатор TG пользователя.
        :return: Словарь с данными найденой записи, {} в противном случае.
        """

        try:
            rec = User.select().where(User.tg_id == user_id).first()
            return rec.__data__ if rec else {}
        except Exception as e:
            raise ValueError(f"Произошла ошибка при получении записи из таблицы 'User': {str(e)}")

    @staticmethod
    def get_urecord_vk(user_id: int) -> Dict:
        """
        Получение записи из таблицы User по VK user_id (vk_id).

        :param user_id: Идентификатор VK пользователя.
        :return: Словарь с данными найденой записи, {} в противном случае.
        """

        try:
            rec = User.select().where(User.vk_id == user_id).first()
            return rec.__data__ if rec else {}
        except Exception as e:
            raise ValueError(f"Произошла ошибка при получении записи из таблицы 'User': {str(e)}")

    def get_tg_ids(self) -> Tuple:
        """
        Получение кортежа со всеми значениями поля tg_id из таблицы User.

        :return: Кортеж со значениями tg_id.
        """
        return self.__get_field_values(User, "tg_id")

    def get_vk_ids(self) -> Tuple:
        """
        Получение кортежа со всеми значениями поля vk_id из таблицы User.

        :return: Кортеж со значениями vk_id.
        """
        return self.__get_field_values(User, "vk_id")

    @staticmethod
    def get_uniq_cats() -> Tuple:
        """
        Получение уникальных категорий из таблицы `Goods`.

        :return: Кортеж категорий товаров.
        """
        dt = []
        try:
            for g in Good.select(Good.category).distinct():
                dt.append(g.category)
            return tuple(dt)
        except Exception as e:
            raise ValueError("Произошла ошибка при получении записи из таблицы 'Good'")

    def get_basket_tg(self, user_id: int) -> List[Dict]:
        """
        Получение данных корзины для пользователя по по Telegram user_id и значению - False для поля 'Basket.added_to_order'.

        :param user_id: Telegram user_id.
        :return: Список словарей с данными о корзине, включая данные пользователя и товара.
        """
        return self.__get_basket_data("tg_id", user_id)

    def get_basket_vk(self, user_id: int) -> List[Dict]:
        """
        Получение данных корзины для пользователя по по VK user_id и значению - False для поля 'Basket.added_to_order'.

        :param user_id: VK user_id.
        :return: Список словарей с данными о корзине, включая данные пользователя и товара.
        """
        return self.__get_basket_data("vk_id", user_id)

    @staticmethod
    def get_goods_by_cat(category: str) -> List[Dict]:
        """
        Получение списка товаров по категории.

        :param category: Категория товаров.
        :return: Список словарей с информацией о товарах.
        """
        try:
            goods = Good.select().where(Good.category == category)
            dt = []

            for g in goods:
                dt.append(g.__data__)
            return dt
        except Exception as e:
            raise ValueError(f"Произошла ошибка при получении записи из таблицы 'Good' по категории '{category}'")

    def union_basket_entries_tg(self, user_id: int, good_id: int) -> Tuple[Any]:
        """
        Получение общего количества и общей стоимости объединенных записей корзины для пользователя Telegram и конкретного товара.

        :param user_id: Идентификатор пользователя в Telegram.
        :param good_id: Идентификатор товара.
        :return: Кортеж, содержащий общее количество и общую стоимость, если записи существуют, в противном случае - пустой кортеж.
        """
        return self.__get_union_basket_entries(user_id, good_id, "tg_id")

    def union_basket_entries_vk(self, user_id: int, good_id: int) -> Tuple[Any]:
        """
        Получение общего количества и общей стоимости объединенных записей корзины для пользователя VK и конкретного товара.

        :param user_id: Идентификатор пользователя в VK.
        :param good_id: Идентификатор товара.
        :return: Кортеж, содержащий общее количество и общую стоимость, если записи существуют, в противном случае - пустой кортеж.
        """
        return self.__get_union_basket_entries(user_id, good_id, "vk_id")






    # check
    @staticmethod
    def __get_uactive_order(user_id: int, field: str) -> List[Dict[str, Any]]:
        """
        Получение данных по активным заказам пользователя.

        :param user_id: Идентификатор пользователя (VK или TG).
        :param field: Название поля таблицы 'User' ('tg_user_id' или 'vk_user_id').
        :return: Список словарей с данными по активным заказам пользователя.
        """
        try:
            data = []
            user = User.get(getattr(User, field) == user_id)

            # Получаем все активные заказы пользователя
            orders = Order.select().where((Order.user_id == user.id) & (Order.status.not_in(["Доставлен", "Отменен"])))

            # Список уникальных номеров заказов
            uniq_ord_nums = []

            if orders:
                for ord in orders:
                    basket = Basket.get(Basket.id == ord.basket_id)
                    good = Good.get(Good.id == basket.good_id)

                    if ord.order_number not in uniq_ord_nums:
                        dt_ord = ord.__data__
                        dt_ord["user_id"] = user.__data__
                        bdt = basket.__data__
                        bdt["good_id"] = good.__data__
                        bdt["user_id"] = user.__data__
                        dt_ord["basket_id"] = [bdt]
                        uniq_ord_nums.append(ord.order_number)
                        data.append(dt_ord)
                    else:
                        bdt = basket.__data__
                        bdt["good_id"] = good.__data__
                        bdt["user_id"] = user.__data__
                        data[len(uniq_ord_nums) - 1]["basket_id"].append(bdt)

                return data
            else:
                return []
        except DoesNotExist:
            raise
        except Exception as e:
            raise ValueError(f"Произошла ошибка при получении активных заказов: {str(e)}")

    def get_uactive_order_vk(self, user_id: int) -> List[Any]:
        return self.__get_uactive_order(user_id, "vk_id")

    def get_uactive_order_tg(self, user_id: int) -> List[Any]:
        return self.__get_uactive_order(user_id, "tg_id")

    @staticmethod
    def __get_delivered_order(user_id: int, field: str) -> Dict:
        try:
            data = []
            u_id = User.get_or_none(getattr(User, field) == user_id)
            if not u_id:
                raise ValueError("Неверный user_id. Нет такого пользователя.")
            orders = Order.select().where((Order.user_id == u_id) & (Order.status == 'Доставлен'))
            if orders:
                for ord in orders:
                    data.append(ord.__data__)
                return data
            else:
                return []
        except DoesNotExist:
            raise ValueError("Запись в таблице 'User' не существует.")
        except Exception as e:
            raise ValueError(f"Произошла ошибка при получении доставленных заказов: {str(e)}")

    def get_delivered_order_tg(self, user_id) -> Dict:
        return self.__get_delivered_order(user_id, "tg_id")

    def get_delivered_order_vk(self, user_id) -> Dict:
        return self.__get_delivered_order(user_id, "vk_id")

    @staticmethod
    def get_five_gcomms(good_id: int) -> List[Any]:
        try:
            data = []
            comments = GoodComment.select() \
                .where((GoodComment.validate == True) & (GoodComment.good_id == good_id)) \
                .order_by(GoodComment.id.desc()) \
                .limit(5)
            for com in comments:
                rec = com.__data__
                u = User.get_or_none(User.id == rec['user_id'])
                g = Good.get_or_none(Good.id == rec['good_id'])

                if not u or not g:
                    raise ValueError("Ошибка при получении комментариев: не найден пользователь или товар.")

                rec['user_id'] = u.__data__
                rec['good_id'] = g.__data__

                data.append(rec)
            return data
        except DoesNotExist:
            raise ValueError("Запись в таблице не существует.")
        except Exception as e:
            raise ValueError(f"Произошла ошибка при получении комментариев: {str(e)}")

    def __add_orders(self, ord_tm: str, deliv_tm: str, ord_p: float, status: str, pay_m: str, user_id: int, ufield: str, deliv_address: str, uname: str, age: str, phone: str) -> List[Any]:
        try:
            u = User.get_or_none(getattr(User, ufield) == user_id)
            if u:
                bask_ids = Basket.select().where((Basket.user_id == u.id) & (Basket.added_to_order == False))
                bask_ids = [b.id for b in bask_ids]
                buff = []

                # получаем номер последнего заказа
                last_ord_n = Order.select().order_by(Order.id.desc()).first()
                if not last_ord_n:
                    last_ord_n = 0
                else:
                    last_ord_n = last_ord_n.order_number
                for b_id in bask_ids:
                    buff.append(self.add_record("order",
                                                order_time=ord_tm,
                                                delivery_time=deliv_tm,
                                                order_price=ord_p,
                                                status=status,
                                                payment_method=pay_m,
                                                delivery_address=deliv_address,
                                                user_name=uname,
                                                age=age,
                                                phone=phone,
                                                user_id=u.id,
                                                basket_id=b_id,
                                                order_number=last_ord_n + 1)
                                )
                return buff

            raise ValueError(f"Запись в таблице 'User' с '{ufield}' = '{user_id}' не найдена.")

        except DoesNotExist:
            raise ValueError("Запись в таблице не существует.")
        except Exception as e:
            raise ValueError(f"Произошла ошибка при добавлении заказа: {str(e)}")

    def add_ords_tg(self, ord_tm: str, deliv_tm: str, ord_p: float, status: str, pay_m: str, user_id: int, deliv_address: str, uname: str, age: str, phone: str) -> List[Any]:
        """
        Добавляет записи в таблицу "basket" для каждой корзины пользователя по TG user_id.

        :param ord_tm: Время размещения заказа.
        :param deliv_tm: Время доставки заказа.
        :param ord_p: Стоимость заказа.
        :param status: Статус заказа.
        :param pay_m: Способ оплаты.
        :param user_id: Идентификатор пользователя TG.
        :param deliv_address: Адрес доставки,
        :param uname: Имя пользователя.
        :param age: Возраст пользователя.
        :param phone: Номер телефона пользователя.
        :return: Список, содержащий словари с данными добавленных заказов пользователя.
        """
        return self.__add_orders(ord_tm, deliv_tm, ord_p, status, pay_m, user_id, "tg_id", deliv_address, uname, age, phone)

    def add_ords_vk(self, ord_tm: str, deliv_tm: str, ord_p: float, status: str, pay_m: str, user_id: int, deliv_address: str, uname: str, age: str, phone: str) -> List[Any]:
        """
        Добавляет записи в таблицу "basket" для каждой корзины пользователя по VK user_id.

        :param ord_tm: Время размещения заказа.
        :param deliv_tm: Время доставки заказа.
        :param ord_p: Стоимость заказа.
        :param status: Статус заказа.
        :param pay_m: Способ оплаты.
        :param user_id: Идентификатор пользователя VK.
        :param deliv_address: Адрес доставки.
        :param uname: Имя пользователя.
        :param age: Возраст пользователя.
        :param phone: Номер телефона пользователя.
        :return: Список, содержащий словари с данными добавленных заказов пользователя.
        """
        return self.__add_orders(ord_tm, deliv_tm, ord_p, status, pay_m, user_id, "vk_id", deliv_address, uname, age, phone)

    @staticmethod
    def __basket_change_added_to_ord(user_id: int, ufield: str) -> int:
        """
        Метод ставит значение поля 'added_to_order' таблицы 'Basket' в значение 'True' по user_id.

        :param user_id: ID пользователя VK или TG.
        :param ufield: Названия поля таблицы 'User' (tg_user_id/vk_user_id)
        :return: Количество обновленных записей.
        """
        try:
            u_id = User.get(getattr(User, ufield) == user_id)
            baskets = Basket.select().where((Basket.user_id == u_id) & (Basket.added_to_order == False))

            updated_records_count = 0

            for basket in baskets:
                basket.added_to_order = True
                basket.save()
                updated_records_count += 1

            return updated_records_count
        except Exception as e:
            raise

    def basket_change_added_to_ord_tg(self, user_id: int) -> int:
        """
        Метод ставит значение поля 'added_to_order' таблицы 'Basket' в значение 'True' по TG user_id.

        :param user_id: ID пользователя TG.
        :param ufield: Названия поля таблицы 'User' (tg_user_id)
        :return: Количество обновленных записей.
        """
        return self.__basket_change_added_to_ord(user_id, "tg_id")

    def basket_added_to_ord_vk(self, user_id: int) -> int:
        """
        Метод ставит значение поля 'added_to_order' таблицы 'Basket' в значение 'True' по VK user_id.

        :param user_id: ID пользователя VK.
        :param ufield: Названия поля таблицы 'User' (vk_user_id)
        :return: Количество обновленных записей.
        """
        return self.__basket_change_added_to_ord(user_id, "vk_id")

    @staticmethod
    def __cancel_order(user_id: int, ord_num: int, ufield: str) -> int:
        """
        Метод для отмены заказа.
        Отменяет заказ, присваивая, полю 'Order.status' значение 'Отменен'.

        :param user_id: Идентификатор пользователя (VK/TG).
        :param ord_num: Номер заказа.
        :param ufield: Название поля таблицы User (vk_id/tg_id)
        :return: Колличество измененных строк.
        """
        try:
            u = User.get_or_none(getattr(User, ufield) == user_id)
            if u:
                count = 0
                for ord in u.orders:
                    if ord.order_number == ord_num:
                        ord.status = "Отменен"
                        ord.save()
                        count += 1
                return count
            raise ValueError(f"Пользователя c {ufield} = {user_id} в таблице User не существует.")
        except Exception as e:
            raise ValueError("Ошибка обновления значения поля таблицы 'Order'.")

    def cancel_order_tg(self, user_id: int, ord_num: int) -> int:
        """
        Метод для отмены заказа.
        Отменяет заказ, присваивая, полю 'Order.status' значение 'Отменен'.

        :param user_id: Идентификатор пользователя TG.
        :param ord_num: Номер заказа.
        :return: Колличество измененных строк.
        """
        return self.__cancel_order(user_id, ord_num, "tg_id")

    def cancel_order_vk(self, user_id: int, ord_num: int) -> int:
        """
        Метод для отмены заказа.
        Отменяет заказ, присваивая, полю 'Order.status' значение 'Отменен'.

        :param user_id: Идентификатор пользователя VK.
        :param ord_num: Номер заказа.
        :return: Колличество измененных строк.
        """
        return self.__cancel_order(user_id, ord_num, "vk_id")

    @staticmethod
    def __get_uordered_goods(user_id: int, ufield: str) -> List[Any]:
        """
        Получение списка доставленных пользователю товаров.

        :param user_id: Идентификатор пользователя TG/VK
        :param ufield: Поле талблицы User (tg_id/vk_id)
        :return: Список словарей с данными товаров.
        """
        goods = []
        try:
            # Пытаемся получить пользователя
            u = User.get(getattr(User, ufield) == user_id)

            # Получение списка заказов
            ords = Order.select().where((Order.user_id == u.id) & (Order.status == "Доставлен"))

            for ord in ords:
                # Пытаемся получить корзину
                try:
                    bask = Basket.get(Basket.id == ord.basket_id)
                except Basket.DoesNotExist:
                    # Обработка случая, если корзина не найдена
                    continue

                # Пытаемся получить товар
                good = Good.get_or_none(Good.id == bask.good_id)

                if good:
                    if good.__data__ not in goods:
                        goods.append(good.__data__)
        except User.DoesNotExist:
            # Обработка случая, если пользователь не найден
            raise ValueError(f"Пользователь с {ufield}={user_id} не найден.")
        except Order.DoesNotExist:
            # Обработка случая, если заказы не найдены
            raise ValueError(f"Не найдено доставленных заказов для пользователя {user_id}.")
        except Exception as e:
            # Обработка других исключений
            raise ValueError(f"Произошла ошибка: {str(e)}")

        return goods

    def get_uordered_goods_tg(self, user_id: int) -> List[Any]:
        """
        Получение списка доставленных пользователю товаров.

        :param user_id: Идентификатор пользователя TG.
        :param ufield: Поле талблицы User tg_id.
        :return: Список словарей с данными товаров.
        """
        return self.__get_uordered_goods(user_id, "tg_id")

    def get_uordered_goods_vk(self, user_id: int) -> List[Any]:
        """
        Получение списка доставленных пользователю товаров.

        :param user_id: Идентификатор пользователя VK.
        :param ufield: Поле талблицы User - vk_id.
        :return: Список словарей с данными товаров.
        """
        return self.__get_uordered_goods(user_id, "vk_id")

    @staticmethod
    def get_all_actorders() -> List[Any]:
        """
        Получение списка словарей всех активных заказов.

        :return: Список словарей с данными активных заказов, данными пользователей и корзин.
        """
        try:
            data = []
            recs = Order.select().where(Order.status.not_in(["Доставлен", "Отменен"])).execute()
            if recs:
                ord_nums = []
                for rec in recs:
                    bask = Basket.get(Basket.id == rec.basket_id)
                    good = Good.get(Good.id == bask.good_id)
                    if rec.__data__["order_number"] not in ord_nums:
                        ord = rec.__data__

                        b_dt = bask.__data__
                        b_dt["good_id"] = good.__data__
                        ord["basket_id"] = b_dt
                        ord["basket_id"] = [ord["basket_id"]]
                        data.append(ord)
                        ord_nums.append(ord["order_number"])
                    else:
                        g_dt = good.__data__
                        b_dt = bask.__data__
                        b_dt["good_id"] = g_dt
                        data[len(ord_nums) - 1]["basket_id"].append(b_dt)
            return data
        except User.DoesNotExist:
            raise ValueError(f"Пользователь не найден.")
        except Basket.DoesNotExist:
            raise ValueError(f"Запись корзины не найдена")
        except Good.DoesNotExist:
            raise ValueError(f"Запись товара не найдена")
        except Exception as e:
            # Обработка других исключений
            raise ValueError(f"Произошла ошибка: {str(e)}")


food_sdb = FoodServiceDB(con)
