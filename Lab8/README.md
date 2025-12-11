pip install litestar pip install sqlalchemy pip install alembic pip install pytest pip install aiosqlite pip install faststream pip install pika pip install 'faststream[rabbit]' pip install redis
pip install taskiq

для запуска: 

alembic upgrade head
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management   
python main.py
taskiq scheduler scheduler_client:scheduler --skip-first-run
