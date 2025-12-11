import redis

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def check_redis_connection():
    try:
        redis_client.ping()
        print("Успешное подключение к Redis")
        return True
    except redis.ConnectionError:
        print("Ошибка подключения к Redis")
        return False
client = redis.Redis(host='localhost', port=6379, db=0)

client.set("user:name", "Иван")
name = client.get("user:name")
if name:
    name = name.decode('utf-8')
print(f"Имя пользователя: {name}")

client.setex("session:123", 3600, "active")

client.set("counter", 0)
client.incr("counter")
client.incrby("counter", 5)
client.decr("counter")
current_value = client.get("counter")
print(f"Текущее значение счетчика: {current_value}")

client.lpush("tasks", "task1", "task2")
client.rpush("tasks", "task3", "task4")
print(f"После lpush: {client.lrange('tasks', 0, -1)}")
print(f"После rpush: {client.lrange('tasks', 0, -1)}")

tasks = client.lrange("tasks", 0, -1)
first_task = client.lpop("tasks")
last_task = client.rpop("tasks")

length = client.llen("tasks")
print(f"\nДлина списка 'tasks': {length}")

client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

client.delete("tags", "languages")

client.sadd("tags", "python", "redis", "database")
print(f"Множество 'tags': {client.smembers('tags')}")

client.sadd("languages", "python", "java", "javascript")
print(f"Множество 'languages': {client.smembers('languages')}")

is_member = client.sismember("tags", "python")
print(f"'python' в множестве 'tags'? {is_member}")

is_member = client.sismember("tags", "java")
print(f"'java' в множестве 'tags'? {is_member}")

all_tags = client.smembers("tags")
print(f"Все тэги: {all_tags}")

tags_count = client.scard("tags")
print(f"Количество тэгов: {tags_count}")

client.srem("tags", "database")  # Удаляем 'database'
print(f"Тэги после удаления 'database': {client.smembers('tags')}")

intersection = client.sinter("tags", "languages")
print(f"Пересечение (tags ∩ languages): {intersection}")

union = client.sunion("tags", "languages")
print(f"Объединение (tags ∪ languages): {union}")

difference = client.sdiff("tags", "languages")
print(f"Разность (tags - languages): {difference}")

diff_reverse = client.sdiff("languages", "tags")
print(f"Разность (languages - tags): {diff_reverse}")

client.hset("user:1000", mapping={
    "name": "Иван",
    "age": "30",
    "city": "Москва"
})
print(f"   Хеш создан: {client.hgetall('user:1000')}")

name = client.hget("user:1000", "name")
all_data = client.hgetall("user:1000")
print(f"   Имя: {name}")
print(f"   Все данные: {all_data}")

exists = client.hexists("user:1000", "email")

keys = client.hkeys("user:1000")
values = client.hvals("user:1000")

client.zadd("leaderboard", {
    "player1": 100,
    "player2": 200,
    "player3": 150,
    "player4": 50,
    "player5": 250
})

top_players = client.zrange("leaderboard", 0, 2, withscores=True)
print(f"TOP-3 игроков: {top_players}")

players_by_score = client.zrangebyscore("leaderboard", 100, 200, withscores=True)
print(f"Игроки со score 100-200: {players_by_score}")

rank = client.zrank("leaderboard", "player1")
print(f"Ранг player1: {rank}")

score = client.zscore("leaderboard", "player3")
print(f"Score player3: {score}")

reverse_rank = client.zrevrank("leaderboard", "player1")
print(f"Обратный ранг player1: {reverse_rank}")


def cache_user(user_id: int, user_data: dict):
    redis_client.setex(f"user:{user_id}", 3600, str(user_data))

if __name__ == "__main__":
    check_redis_connection()