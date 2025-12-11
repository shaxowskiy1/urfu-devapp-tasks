import pytest
try:
    import pytest_asyncio
    pytest_asyncio_available = True
except ImportError:
    pytest_asyncio_available = False
    # Если pytest-asyncio не установлен, используем обычный pytest.fixture
    # но это может не работать правильно с async фикстурами
    pytest_asyncio = pytest

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from dto.user_create_dto import UserCreate
from dto.user_update_dto import UserUpdate
from dto.product_create_dto import ProductCreate
from dto.product_update_dto import ProductUpdate
from dto.address_create_dto import AddressCreate
from dto.address_update_dto import AddressUpdate
from dto.order_create_dto import OrderCreate
from dto.order_update_dto import OrderUpdate
from models import Base
from repositories.user_repository import UserRepository
from repositories.product_repository import ProductRepository
from repositories.address_repository import AddressRepository
from repositories.order_repository import OrderRepository
from service.user_service import UserService
from service.product_service import ProductService
from service.address_service import AddressService
from service.order_service import OrderService

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def engine():
    return create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest_asyncio.fixture(scope="session")
async def tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Удаляем таблицы после всех тестов
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine, tables):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        # Таблицы уже могут быть созданы, это нормально
        pass
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as s:
        yield s
        await s.rollback()


@pytest_asyncio.fixture
async def user_repository(session):
    return UserRepository(session)


@pytest_asyncio.fixture
async def product_repository(session):
    return ProductRepository(session)


@pytest_asyncio.fixture
async def address_repository(session):
    return AddressRepository(session)


@pytest_asyncio.fixture
async def order_repository(session):
    return OrderRepository(session)


@pytest_asyncio.fixture
async def user_service(user_repository):
    return UserService(user_repository)


@pytest_asyncio.fixture
async def product_service(product_repository):
    return ProductService(product_repository)


@pytest_asyncio.fixture
async def address_service(address_repository, user_repository):
    return AddressService(address_repository, user_repository)


@pytest_asyncio.fixture
async def order_service(order_repository, user_repository, product_repository, address_repository):
    return OrderService(order_repository, user_repository, product_repository, address_repository)



class TestUserRepository:
    @pytest.mark.asyncio
    async def test_create_user(self, user_repository: UserRepository, session: AsyncSession):
        user_data = UserCreate(
            username="John_doe",
            email="test@example.com",
            description="Test user description"
        )

        user = await user_repository.create(user_data)
        await session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "John_doe"
        assert user.description == "Test user description"
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_repository: UserRepository, session: AsyncSession):
        user_data = UserCreate(
            username="get_user",
            email="get@example.com",
            description="Get user"
        )
        user = await user_repository.create(user_data)
        await session.commit()

        found_user = await user_repository.get_by_id(user.id)
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.email == "get@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_repository: UserRepository, session: AsyncSession):
        user_data = UserCreate(
            username="email_user",
            email="unique@example.com",
            description="Email user"
        )
        user = await user_repository.create(user_data)
        await session.commit()

        found_user = await user_repository.get_by_email("unique@example.com")

        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.email == "unique@example.com"

    @pytest.mark.asyncio
    async def test_update_user(self, user_repository: UserRepository, session: AsyncSession):
        user_data = UserCreate(
            username="update_user",
            email="update@example.com",
            description="Original"
        )
        user = await user_repository.create(user_data)
        await session.commit()

        update_data = UserUpdate(description="Updated")
        updated_user = await user_repository.update(user.id, update_data)
        await session.commit()

        assert updated_user.username == "update_user"
        assert updated_user.description == "Updated"

    @pytest.mark.asyncio
    async def test_delete_user(self, user_repository: UserRepository, session: AsyncSession):
        user_data = UserCreate(
            username="delete_user",
            email="delete@example.com",
            description="Delete user"
        )
        user = await user_repository.create(user_data)
        await session.commit()

        await user_repository.delete(user.id)
        await session.commit()

        deleted_user = await user_repository.get_by_email("delete@example.com")
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_get_by_filter(self, user_repository: UserRepository, session: AsyncSession):
        user1 = UserCreate(username="filter1", email="filter1@example.com")
        user2 = UserCreate(username="filter2", email="filter2@example.com")
        
        await user_repository.create(user1)
        await user_repository.create(user2)
        await session.commit()

        users = await user_repository.get_by_filter(10, 1, username="filter1")
        assert len(users) == 1
        assert users[0].username == "filter1"


class TestUserService:
    @pytest.mark.asyncio
    async def test_create_user(self, user_service: UserService, session: AsyncSession):
        user_data = UserCreate(
            username="service_user",
            email="service@example.com",
            description="Service user"
        )

        user = await user_service.create(user_data)

        assert user.id is not None
        assert user.email == "service@example.com"
        assert user.username == "service_user"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service: UserService, session: AsyncSession):
        user_data = UserCreate(
            username="dup1",
            email="duplicate@example.com"
        )
        await user_service.create(user_data)

        user_data2 = UserCreate(
            username="dup2",
            email="duplicate@example.com"
        )

        with pytest.raises(ValueError, match="already exists"):
            await user_service.create(user_data2)

    @pytest.mark.asyncio
    async def test_get_by_id(self, user_service: UserService, session: AsyncSession):
        user_data = UserCreate(username="get_service", email="get_service@example.com")
        user = await user_service.create(user_data)

        found_user = await user_service.get_by_id(user.id)
        assert found_user is not None
        assert found_user.id == user.id

    @pytest.mark.asyncio
    async def test_update_user(self, user_service: UserService, session: AsyncSession):
        user_data = UserCreate(username="update_service", email="update_service@example.com")
        user = await user_service.create(user_data)

        update_data = UserUpdate(description="Updated description")
        updated_user = await user_service.update(user.id, update_data)

        assert updated_user.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_user(self, user_service: UserService, session: AsyncSession):
        user_data = UserCreate(username="delete_service", email="delete_service@example.com")
        user = await user_service.create(user_data)

        await user_service.delete(user.id)

        found_user = await user_service.get_by_id(user.id)
        assert found_user is None


class TestProductRepository:
    @pytest.mark.asyncio
    async def test_create_product(self, product_repository: ProductRepository, session: AsyncSession):
        product_data = ProductCreate(
            name="Test Product",
            description="Test Description",
            price=99.99
        )

        product = await product_repository.create(product_data)
        await session.commit()

        assert product.id is not None
        assert product.name == "Test Product"
        assert product.description == "Test Description"
        assert product.price == 99.99

    @pytest.mark.asyncio
    async def test_get_product_by_id(self, product_repository: ProductRepository, session: AsyncSession):
        product_data = ProductCreate(name="Get Product", price=50.0)
        product = await product_repository.create(product_data)
        await session.commit()

        found_product = await product_repository.get_by_id(product.id)
        assert found_product is not None
        assert found_product.id == product.id
        assert found_product.name == "Get Product"

    @pytest.mark.asyncio
    async def test_update_product(self, product_repository: ProductRepository, session: AsyncSession):
        product_data = ProductCreate(name="Original Product", price=50.00)
        product = await product_repository.create(product_data)
        await session.commit()

        update_data = ProductUpdate(name="Updated Product", price=75.00)
        updated_product = await product_repository.update(product.id, update_data)
        await session.commit()

        assert updated_product.name == "Updated Product"
        assert updated_product.price == 75.00

    @pytest.mark.asyncio
    async def test_delete_product(self, product_repository: ProductRepository, session: AsyncSession):
        product_data = ProductCreate(name="Delete Product", price=30.00)
        product = await product_repository.create(product_data)
        await session.commit()

        await product_repository.delete(product.id)
        await session.commit()

        deleted_product = await product_repository.get_by_id(product.id)
        assert deleted_product is None

    @pytest.mark.asyncio
    async def test_get_all_products(self, product_repository: ProductRepository, session: AsyncSession):
        product1 = ProductCreate(name="Product 1", price=10.00)
        product2 = ProductCreate(name="Product 2", price=20.00)

        p1 = await product_repository.create(product1)
        p2 = await product_repository.create(product2)
        await session.commit()

        products = await product_repository.get_all()

        assert len(products) >= 2
        assert any(p.id == p1.id for p in products)
        assert any(p.id == p2.id for p in products)


class TestProductService:
    @pytest.mark.asyncio
    async def test_create_product(self, product_service: ProductService, session: AsyncSession):
        product_data = ProductCreate(
            name="Service Product",
            description="Service Description",
            price=99.99
        )

        product = await product_service.create(product_data)

        assert product.id is not None
        assert product.name == "Service Product"
        assert product.price == 99.99

    @pytest.mark.asyncio
    async def test_create_product_negative_price(self, product_service: ProductService, session: AsyncSession):
        product_data = ProductCreate(name="Negative Product", price=-10.0)

        with pytest.raises(ValueError, match="non-negative"):
            await product_service.create(product_data)

    @pytest.mark.asyncio
    async def test_get_by_id(self, product_service: ProductService, session: AsyncSession):
        product_data = ProductCreate(name="Get Service Product", price=50.0)
        product = await product_service.create(product_data)

        found_product = await product_service.get_by_id(product.id)
        assert found_product is not None
        assert found_product.id == product.id

    @pytest.mark.asyncio
    async def test_update_product(self, product_service: ProductService, session: AsyncSession):
        product_data = ProductCreate(name="Update Service Product", price=50.00)
        product = await product_service.create(product_data)

        update_data = ProductUpdate(price=75.00)
        updated_product = await product_service.update(product.id, update_data)

        assert updated_product.price == 75.00

    @pytest.mark.asyncio
    async def test_delete_product(self, product_service: ProductService, session: AsyncSession):
        product_data = ProductCreate(name="Delete Service Product", price=30.00)
        product = await product_service.create(product_data)

        await product_service.delete(product.id)

        found_product = await product_service.get_by_id(product.id)
        assert found_product is None


class TestAddressRepository:
    @pytest.mark.asyncio
    async def test_create_address(self, address_repository: AddressRepository, user_repository: UserRepository, session: AsyncSession):
        user_data = UserCreate(username="addr_user", email="addr@example.com")
        user = await user_repository.create(user_data)
        await session.commit()

        address_data = AddressCreate(
            user_id=user.id,
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA",
            is_primary=True
        )

        address = await address_repository.create(address_data)
        await session.commit()

        assert address.id is not None
        assert address.street == "123 Main St"
        assert address.city == "New York"
        assert address.is_primary is True

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, address_repository: AddressRepository, user_repository: UserRepository, session: AsyncSession):
        user_data = UserCreate(username="addr_user2", email="addr2@example.com")
        user = await user_repository.create(user_data)
        await session.commit()

        address1 = AddressCreate(
            user_id=user.id,
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA"
        )
        address2 = AddressCreate(
            user_id=user.id,
            street="456 Oak Ave",
            city="Boston",
            state="MA",
            zip_code="02101",
            country="USA"
        )

        a1 = await address_repository.create(address1)
        a2 = await address_repository.create(address2)
        await session.commit()

        addresses = await address_repository.get_by_user_id(user.id)
        assert len(addresses) >= 2


class TestAddressService:
    @pytest.mark.asyncio
    async def test_create_address(self, address_service: AddressService, user_repository: UserRepository, session: AsyncSession):
        user_data = UserCreate(username="service_addr_user", email="service_addr@example.com")
        user = await user_repository.create(user_data)
        await session.commit()

        address_data = AddressCreate(
            user_id=user.id,
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA"
        )

        address = await address_service.create(address_data)

        assert address.id is not None
        assert address.street == "123 Main St"

    @pytest.mark.asyncio
    async def test_create_address_invalid_user(self, address_service: AddressService, session: AsyncSession):
        fake_user_id = uuid4()
        address_data = AddressCreate(
            user_id=fake_user_id,
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA"
        )

        with pytest.raises(ValueError, match="not found"):
            await address_service.create(address_data)


class TestOrderRepository:
    @pytest.mark.asyncio
    async def test_create_order(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        address_repository: AddressRepository,
        session: AsyncSession
    ):
        user_data = UserCreate(username="order_user", email="order@example.com")
        user = await user_repository.create(user_data)
        await session.commit()

        product_data = ProductCreate(name="Order Product", price=15.00)
        product = await product_repository.create(product_data)
        await session.commit()

        address_data = AddressCreate(
            user_id=user.id,
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA"
        )
        address = await address_repository.create(address_data)
        await session.commit()

        order_data = OrderCreate(
            user_id=user.id,
            address_id=address.id,
            product_id=product.id,
            quantity=2,
            total_price=30.00,
            status="pending"
        )

        order = await order_repository.create(order_data)
        await session.commit()

        assert order.id is not None
        assert order.user_id == user.id
        assert order.product_id == product.id
        assert order.quantity == 2
        assert order.total_price == 30.00

    @pytest.mark.asyncio
    async def test_get_by_user_id(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        address_repository: AddressRepository,
        session: AsyncSession
    ):
        user_data = UserCreate(username="order_user2", email="order2@example.com")
        user = await user_repository.create(user_data)
        await session.commit()

        product_data = ProductCreate(name="Order Product 2", price=20.00)
        product = await product_repository.create(product_data)
        await session.commit()

        address_data = AddressCreate(
            user_id=user.id,
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA"
        )
        address = await address_repository.create(address_data)
        await session.commit()

        order_data = OrderCreate(
            user_id=user.id,
            address_id=address.id,
            product_id=product.id,
            quantity=1,
            total_price=20.00
        )
        order = await order_repository.create(order_data)
        await session.commit()

        orders = await order_repository.get_by_user_id(user.id)
        assert len(orders) >= 1
        assert any(o.id == order.id for o in orders)


class TestOrderService:
    @pytest.mark.asyncio
    async def test_create_order(
        self,
        order_service: OrderService,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        address_repository: AddressRepository,
        session: AsyncSession
    ):
        user_data = UserCreate(username="service_order_user", email="service_order@example.com")
        user = await user_repository.create(user_data)
        await session.commit()

        product_data = ProductCreate(name="Service Order Product", price=25.00)
        product = await product_repository.create(product_data)
        await session.commit()

        address_data = AddressCreate(
            user_id=user.id,
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA"
        )
        address = await address_repository.create(address_data)
        await session.commit()

        order_data = OrderCreate(
            user_id=user.id,
            address_id=address.id,
            product_id=product.id,
            quantity=2,
            total_price=50.00
        )

        order = await order_service.create(order_data)

        assert order.id is not None
        assert order.user_id == user.id
        assert order.quantity == 2

    @pytest.mark.asyncio
    async def test_create_order_invalid_user(
        self,
        order_service: OrderService,
        product_repository: ProductRepository,
        address_repository: AddressRepository,
        session: AsyncSession
    ):
        fake_user_id = uuid4()
        
        product_data = ProductCreate(name="Test Product", price=10.00)
        product = await product_repository.create(product_data)
        await session.commit()

        # Create a user for the address
        from repositories.user_repository import UserRepository
        user_repo = UserRepository(session)
        user_data = UserCreate(username="temp_user", email="temp@example.com")
        user = await user_repo.create(user_data)
        await session.commit()

        address_data = AddressCreate(
            user_id=user.id,
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA"
        )
        address = await address_repository.create(address_data)
        await session.commit()

        order_data = OrderCreate(
            user_id=fake_user_id,
            address_id=address.id,
            product_id=product.id,
            quantity=1
        )

        with pytest.raises(ValueError, match="not found"):
            await order_service.create(order_data)

    @pytest.mark.asyncio
    async def test_update_order(
        self,
        order_service: OrderService,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        address_repository: AddressRepository,
        session: AsyncSession
    ):
        user_data = UserCreate(username="update_order_user", email="update_order@example.com")
        user = await user_repository.create(user_data)
        await session.commit()

        product_data = ProductCreate(name="Update Order Product", price=30.00)
        product = await product_repository.create(product_data)
        await session.commit()

        address_data = AddressCreate(
            user_id=user.id,
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA"
        )
        address = await address_repository.create(address_data)
        await session.commit()

        order_data = OrderCreate(
            user_id=user.id,
            address_id=address.id,
            product_id=product.id,
            quantity=1,
            total_price=30.00,
            status="pending"
        )
        order = await order_service.create(order_data)

        update_data = OrderUpdate(status="completed")
        updated_order = await order_service.update(order.id, update_data)

        assert updated_order.status == "completed"

    @pytest.mark.asyncio
    async def test_delete_order(
        self,
        order_service: OrderService,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        address_repository: AddressRepository,
        session: AsyncSession
    ):
        user_data = UserCreate(username="delete_order_user", email="delete_order@example.com")
        user = await user_repository.create(user_data)
        await session.commit()

        product_data = ProductCreate(name="Delete Order Product", price=40.00)
        product = await product_repository.create(product_data)
        await session.commit()

        address_data = AddressCreate(
            user_id=user.id,
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA"
        )
        address = await address_repository.create(address_data)
        await session.commit()

        order_data = OrderCreate(
            user_id=user.id,
            address_id=address.id,
            product_id=product.id,
            quantity=1,
            total_price=40.00
        )
        order = await order_service.create(order_data)

        await order_service.delete(order.id)

        found_order = await order_service.get_by_id(order.id)
        assert found_order is None


class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_user_workflow(
        self,
        user_service: UserService,
        address_service: AddressService,
        product_service: ProductService,
        order_service: OrderService,
        session: AsyncSession
    ):
        user_data = UserCreate(
            username="integration_user",
            email="integration@example.com",
            description="Integration test user"
        )
        user = await user_service.create(user_data)
        assert user.id is not None

        # Create address
        address_data = AddressCreate(
            user_id=user.id,
            street="Integration St",
            city="Test City",
            state="TS",
            zip_code="12345",
            country="USA",
            is_primary=True
        )
        address = await address_service.create(address_data)
        assert address.id is not None

        product_data = ProductCreate(
            name="Integration Product",
            description="Integration test product",
            price=99.99
        )
        product = await product_service.create(product_data)
        assert product.id is not None

        order_data = OrderCreate(
            user_id=user.id,
            address_id=address.id,
            product_id=product.id,
            quantity=1,
            total_price=99.99
        )
        order = await order_service.create(order_data)
        assert order.id is not None

        found_user = await user_service.get_by_id(user.id)
        assert found_user is not None

        update_data = OrderUpdate(status="completed")
        updated_order = await order_service.update(order.id, update_data)
        assert updated_order.status == "completed"
