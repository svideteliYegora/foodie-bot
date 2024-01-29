from playhouse.migrate import *
from models import con, Order


migrator = SqliteMigrator(con)

migrate(
    migrator.add_column('order', 'order_number', Order.order_number),
)
