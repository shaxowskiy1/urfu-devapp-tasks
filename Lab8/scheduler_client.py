import os
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from taskiq_aio_pika import AioPikaBroker
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from models import Order, Report, Base


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

broker = AioPikaBroker(
    RABBITMQ_URL,
    exchange_name="report",
    queue_name="cmd_order"
)

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
if DATABASE_URL.startswith("sqlite://"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
scheduler_engine = create_async_engine(DATABASE_URL, echo=True)
scheduler_session_factory = sessionmaker(
    scheduler_engine, class_=AsyncSession, expire_on_commit=False
)


@broker.task(
    schedule=[
        {
            "cron": "*/1 * * * *",
            "args": ["Cron_User"],
            "schedule_id": "greet_every_minute",
        }
    ]
)
async def my_scheduled_task(name: str) -> str:
    report_date = date.today()
    report_datetime = datetime.combine(report_date, datetime.min.time())
    
    async with scheduler_session_factory() as session:
        try:
            query = select(Order)
            result = await session.execute(query)
            orders = result.scalars().all()
            
            reports_created = 0
            for order in orders:
                existing_report_query = select(Report).where(
                    Report.order_id == order.id,
                    Report.report_at == report_datetime
                )
                existing_result = await session.execute(existing_report_query)
                existing_report = existing_result.scalar_one_or_none()
                
                if not existing_report:
                    report = Report(
                        report_at=report_datetime,
                        order_id=order.id,
                        count_product=order.quantity
                    )
                    session.add(report)
                    reports_created += 1
            
            await session.commit()
            
            message = f"Scheduled report created for {name} at {datetime.now()}. Created {reports_created} new reports for {report_date}."
            print(message)
            return message
            
        except Exception as e:
            await session.rollback()
            error_message = f"Error creating reports: {str(e)}"
            print(error_message)
            return error_message