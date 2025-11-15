from litestar import Litestar
from litestar.di import Provide
from sqlalchemy.orm import sessionmaker, selectinload

from controller.user_controller import UserController
from database import engine
from dependencies import provide_user_repository, provide_db_session, provide_user_service
from models import User, Address, Product, Order, Base


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

session_factory = sessionmaker(bind=engine)


with session_factory() as session:

    user1 = User(
        username="John Doe",
        email="john@example.com",
        description="Постоянный клиент"
    )
    user2 = User(
        username="Jane Smith",
        email="jane@example.com",
        description="Новый клиент"
    )
    user3 = User(
        username="Bob Johnson",
        email="bob@example.com",
        description="VIP клиент"
    )

    address1 = Address(
        user=user1,
        street="123 Main St",
        city="New York",
        state="NY",
        zip_code="10001",
        country="USA",
        is_primary=True
    )
    address2 = Address(
        user=user1,
        street="456 Oak Ave",
        city="Boston",
        state="MA",
        zip_code="02101",
        country="USA"
    )
    address3 = Address(
        user=user2,
        street="789 Pine Rd",
        city="Los Angeles",
        state="CA",
        zip_code="90001",
        country="USA",
        is_primary=True
    )

    products = [
        Product(name="Ноутбук", description="Игровой ноутбук", price=999.99),
        Product(name="Смартфон", description="Флагманский смартфон", price=699.99),
        Product(name="Наушники", description="Беспроводные наушники", price=199.99),
        Product(name="Планшет", description="Графический планшет", price=499.99),
        Product(name="Часы", description="Умные часы", price=299.99)
    ]

    session.add_all([user1, user2, user3, address1, address2, address3] + products)
    session.commit()

    orders = [
        Order(
            user_id=user1.id,
            address_id=address1.id,
            product_id=products[0].id,
            quantity=1,
            total_price=products[0].price,
            status="completed"
        ),
        Order(
            user_id=user1.id,
            address_id=address2.id,
            product_id=products[1].id,
            quantity=2,
            total_price=products[1].price * 2,
            status="pending"
        ),
        Order(
            user_id=user2.id,
            address_id=address3.id,
            product_id=products[2].id,
            quantity=1,
            total_price=products[2].price,
            status="completed"
        ),
        Order(
            user_id=user3.id,
            address_id=address1.id,
            product_id=products[3].id,
            quantity=3,
            total_price=products[3].price * 3,
            status="pending"
        ),
        Order(
            user_id=user3.id,
            address_id=address3.id,
            product_id=products[4].id,
            quantity=1,
            total_price=products[4].price,
            status="cancelled"
        )
    ]

    session.add_all(orders)
    session.commit()


    users_with_orders = session.query(User).options(
        selectinload(User.addresses),
        selectinload(User.orders).selectinload(Order.product),
        selectinload(User.orders).selectinload(Order.address)
    ).all()

    for user in users_with_orders:
        print(f"\nПользователь: {user.username} ({user.description})")
        print(f"Адреса: {[f'{addr.street}, {addr.city}' for addr in user.addresses]}")
        print("Заказы:")
        for order in user.orders:
            print(f"  - {order.product.name} x{order.quantity} - ${order.total_price} ({order.status})")

    all_products = session.query(Product).all()
    for product in all_products:
        print(f"{product.name}: ${product.price} - {product.description}")

app = Litestar(
    route_handlers=[UserController],
    dependencies={
        "db_session": Provide(provide_db_session),
        "user_repository": Provide(provide_user_repository),
        "user_service": Provide(provide_user_service),
    },
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="trace")
