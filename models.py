from functools import reduce

from peewee import *
from typing import *
from typing import Optional, List, Dict, Tuple, Any, Type, Union


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


class GoodComment(BaseModel):
    id = IntegerField(primary_key=True)
    eval = IntegerField()
    text = TextField()
    validate = BooleanField()
    user_id = ForeignKeyField(User, backref='good_comments')
    good_id = ForeignKeyField(Good, backref='good_comments')


class OrderComment(BaseModel):
    id = IntegerField(primary_key=True)
    eval = IntegerField()
    text = TextField()
    validate = BooleanField()
    user_id = ForeignKeyField(User, backref='order_comments')
    order_id = ForeignKeyField(Order, backref='order_comments')


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
            raise

    @staticmethod
    def __get_basket_data(ufield: str, user_id: int) -> List[Dict]:
        """
        Получение данных корзины для пользователя по указанному полю и его идентификатору.

        :param ufield: Поле из таблицы User: tg_id или vk_id.
        :param user_id: Идентификатор пользователя.
        :return: Список словарей с данными о корзине, включая данные пользователя и товара.
        """
        try:
            u_id = User.get_or_none(getattr(User, ufield) == user_id)

            if u_id:
                dt_list = []
                for item in u_id.baskets:

                    good = Good.get_by_id(item.good_id)

                    bask_data = item.__dict__['__data__']
                    bask_data['user_id'] = u_id.__dict__['__data__']
                    bask_data['good_id'] = good.__dict__['__data__']
                    dt_list.append(
                        bask_data
                    )
                return dt_list
            else:
                raise ValueError(f"Запись в таблице 'User', где '{ufield}'== '{user_id}' не существует.")
        except Exception as e:
            raise

    @staticmethod
    def __get_order_price(ufield: str, user_id: int) -> float:
        """
        Получение суммы заказа по user_id.

        :param ufield: Поле из таблицы User: tg_id/vk_id.
        :param user_id: TG user_id/ Vk user_id.
        :return: Вещественное число.
        """
        try:
            user_alias = User.alias()
            price = (Basket
                     .select(fn.SUM(Basket.total_price).alias("tp_sum"))
                     .join(user_alias, on=(getattr(Basket, 'user_id') == user_alias.id))
                     .where(getattr(user_alias, ufield) == user_id)
                     .group_by(getattr(user_alias, ufield))
                     .first())
            return price.tp_sum if price else 0.0
        except Exception as e:
            raise

    @staticmethod
    def __get_union_basket_entries(user_id: int, good_id: int, field: str) -> Tuple[Any]:
        """
        Получение общего количества и общей суммы для объединенных записей корзины для пользователя и конкретного товара.

        :param user_id: Идентификатор пользователя.
        :param good_id: Идентификатор товара.
        :param field: Поле для идентификации пользователя (например, "tg_id" или "vk_id").
        :return: Кортеж, содержащий общее количество и общую сумму, если записи существуют, в противном случае пустой кортеж.
        """
        try:
            u_id = User.get_or_none(getattr(User, field) == user_id)
            data = (Basket
                    .select(fn.SUM(Basket.amount).alias('total_amount'),
                            fn.SUM(Basket.total_price).alias('total_price')
                            )
                    .where((Basket.user_id == u_id) & (Basket.good_id == good_id))
                    .group_by(Basket.user_id, Basket.good_id)
                    .first())
            return (data.total_amount, data.total_price) if data else ()
        except Exception as e:
            raise

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
            raise

    def delete_all_record(self, table: str, **params: Dict) -> int:
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
                    return model.delete_by_id(record_id)

                # Строим условие
                query = reduce(lambda q, item: q.where(getattr(model, item[0]) == item[1]), params.items(),
                               model.delete())

                # Если есть id, добавляем его к условию
                res = query.execute()
                return res
            except Exception as e:
                raise
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
                raise
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
                raise
        else:
            raise ValueError(f"Таблица '{table}' не поддерживается или не существует.")

    @staticmethod
    def add_user(**udata: Dict) -> Dict:
        """
        Добавление записи о новом пользователе в таблицу `User`.

        :param udata: Словарь с данными пользователя.
        :return: Словарь с данными созданной записи при успешном добавлении и {} в противном случае.
        """
        try:
            new_rec: User = User.create(**udata)
            return new_rec.__dict__['__data__'] if new_rec else {}
        except Exception as e:
            raise

    def add_record(self, table: str, **params: Dict[str, Any]) -> Dict:
        """
        Добавление новой записи в указанную таблицу с заданными параметрами.

        :param table: Название таблицы для добавления записи.
        :param params: Словарь с парами поле-значение для новой записи.
        :return: Словарь с данными новой записи при успешном добавлении, {} в противном случае.
        """
        table = self.__normalize_table_name(table)
        model = globals().get(table)
        if model and issubclass(model, Model):
            try:
                new_rec: Model = model.create(**params)
                new_rec.save()
                return new_rec.__dict__['__data__'] if new_rec else {}
            except Exception as e:
                raise
        else:
            raise ValueError(f"Таблица '{table}' не поддерживается или не существует.")

    def get_record(self, table: str, **params: dict) -> Dict:
        """
        Получение записи из указанной таблицы с заданными параметрами.

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
                    res = model.get_or_none(record_id)
                else:
                # Строим условие
                    query = reduce(lambda q, item: q.where(getattr(model, item[0]) == item[1]), params.items(),
                                   model.select())
                    # Получаем запись
                    res = query.first()
                return res.__dict__['__data__'] if res else {}
            except Exception as e:
                raise
        else:
            raise ValueError(f"Таблица '{table}' не поддерживается или не существует.")

    def get_records(self, table: str) -> List[Any]:
        """
        Получение всех записей из указанной таблицы.

        :param table: Имя таблицы.
        :return: Список словарей с данными если они есть и пустой список в противном случае.
        """
        try:
            table = self.__normalize_table_name(table)
            model = globals().get(table)
            if model and issubclass(model, Model):
                dt = model.select().execute()
                return [i.__dict__['__data__'] for i in dt] if dt else []
            raise ValueError(f"Таблица '{table}' не поддерживается или не существует.")
        except Exception as e:
            raise

    @staticmethod
    def get_urecord_tg(user_id: int) -> Dict:
        """
        Получение записи из таблицы User по TG user_id (tg_id).

        :param user_id: Идентификатор TG пользователя.
        :return: Словарь с данными найденой записи, {} в противном случае.
        """

        try:
            rec = User.select().where(User.tg_id == user_id).first()
            return rec.__dict__['__data__'] if rec else {}
        except Exception as e:
            raise

    @staticmethod
    def get_urecord_vk(user_id: int) -> Dict:
        """
        Получение записи из таблицы User по VK user_id (vk_id).

        :param user_id: Идентификатор VK пользователя.
        :return: Словарь с данными найденой записи, {} в противном случае.
        """

        try:
            rec = User.select().where(User.vk_id == user_id)
            return rec.__dict__['__data__'] if rec else {}
        except Exception as e:
            raise

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
            raise

    def get_basket_tg(self, user_id: int) -> List[Dict]:
        """
        Получение данных корзины для пользователя по Telegram user_id.

        :param user_id: Telegram user_id.
        :return: Список словарей с данными о корзине, включая данные пользователя и товара.
        """
        return self.__get_basket_data("tg_id", user_id)

    def get_basket_vk(self, user_id: int) -> List[Dict]:
        """
        Получение данных корзины для пользователя по VK user_id.

        :param user_id: VK user_id.
        :return: Список словарей с данными о корзине, включая данные пользователя и товара.
        """
        return self.__get_basket_data("vk_id", user_id)

    def get_order_price_tg(self, user_id: int) -> float:
        """
        Получение суммы заказа по TG user_id.

        :param user_id: TG user_id.
        :return: Вещественное число.
        """
        return self.__get_order_price("tg_id", user_id)

    def get_order_price_vk(self, user_id: int) -> float:
        """
        Получение суммы заказа по VK user_id.

        :param user_id: VK user_id.
        :return: Вещественное число.
        """
        return self.__get_order_price("vk_id", user_id)

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
                dt.append(g.__dict__['__data__'])
            return dt
        except Exception as e:
            raise

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

    @staticmethod
    def __get_order(user_id: int, field: str) -> list[Any]:
        try:
            data = []
            user = User.get_or_none(getattr(User, field) == user_id)
            if not user:
                raise ValueError("Неверный user_id. Нет такого польвателя.")
            orders = Order.select().where(Order.user_id == user)

            if orders:
                basket = Basket.get_or_none(Basket.user_id == user.id)
                for ord in orders:
                    dt_ord = ord.__dict__['__data__']
                    dt_ord["user_id"] = user.__dict__['__data__']
                    dt_ord["basket_id"] = basket.__dict__['__data__']
                    data.append(dt_ord)
                return data
            else:
                return []
        except Exception as e:
            raise

    def get_order_vk(self, user_id: int) -> list[Any]:
        return self.__get_order(user_id, "vk_id")

    def get_order_tg(self, user_id: int) -> Dict:
        return self.__get_order(user_id, "tg_id")

    @staticmethod
    def __get_delivered_order(user_id: int, field: str) -> Dict:
        try:
            data = []
            u_id = User.get_or_none(getattr(User, field) == user_id)
            if not u_id:
                raise ValueError("Неверный user_id. Нет такого польвателя.")
            orders = Order.select().where((Order.user_id == u_id) & (Order.status == 'Доставлен'))
            if orders:
                for ord in orders:
                    data.append(ord.__dict__['__data__'])
                return data
            else:
                return []
        except Exception as e:
            raise

    def get_delivered_order_tg(self, user_id) -> Dict:
        return self.__get_delivered_order(user_id, "tg_id")

    def get_delivered_order_vk(self, user_id) -> Dict:
        return self.__get_delivered_order(user_id, "vk_id")

    @staticmethod
    def get_five_gcomms(good_id: int) -> List[Any]:
        try:
            data = []
            comments = GoodComment.select()\
                                  .where((GoodComment.validate == True) & (GoodComment.good_id == good_id))\
                                  .order_by(GoodComment.id.desc())\
                                  .limit(5)
            for com in comments:
                rec = com.__dict__['__data__']
                user_id = User.get(rec['user_id'])
                good_id = Good.get(rec['good_id'])

                rec['user_id'] = user_id.__dict__['__data__']
                rec['good_id'] = good_id.__dict__['__data__']

                data.append(rec)
            return data
        except Exception as e:
            raise


food_sdb = FoodServiceDB(con)
