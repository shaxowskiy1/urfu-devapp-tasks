Для запуска приложения необходимы зависимости:

pip install Litestar
pip install uvicorn

Запуск приложения: 
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug --reload
