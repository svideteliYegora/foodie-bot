from playhouse.migrate import *
from models import con, Order, Basket, OrderComment, GoodComment
from peewee import *


migrator = SqliteMigrator(con)

# migrate(
#     migrator.add_column('order', 'order_number', Order.order_number),
# )
#
# migrate(
#     migrator.add_column('basket', 'order_active', Basket.order_active),
# )

# migrate(
#     migrator.rename_column('basket', 'order_active', 'added_to_order')
# )

# migrate(
#     migrator.add_column('order', 'delivery_address', Basket.delivery_address),
# )

# migrate(
#     migrator.add_column('order', 'phone', Order.phone),
#     migrator.add_column('order', 'age', Order.age),
#     migrator.add_column('order', 'user_name', Order.user_name),
# )
#
# migrate(
#     migrator.rename_column('ordercomment', 'order_id', 'order_number')
# )

# migrate(
#     migrator.drop_column('goodcomment', 'text'),
#     migrator.add_column('goodcomment', 'text', GoodComment.text)
# )

# migrate(
#     migrator.drop_column('goodcomment', 'validate')
# # )
#
# migrate(
#     migrator.add_column('goodcomment', 'validate', GoodComment.validate),
#     migrator.drop_column('ordercomment', 'validate'),
#     migrator.add_column('ordercomment', 'validate', OrderComment.validate),
# )