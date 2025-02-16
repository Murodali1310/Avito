# Avito Shop Service

Привет! Это наш backend для магазина мерча Avito. Сервис позволяет:
- Войти (или зарегистрироваться, если юзера ещё нет) и получить JWT-токен.
- Узнать, сколько у тебя монет, посмотреть купленные товары и историю транзакций.
- Переводить монеты другим сотрудникам.
- Покупать мерч за монеты.

## Как это работает

Сервер запускается из файла `app.py`

### Основные эндпоинты

- **POST /api/auth**  
  Логин и регистрация. Отправляешь JSON:
  ```json
  {
    "username": "user1",
    "password": "password"
  }
  ```
  И получаешь в ответ JWT-токен:
  ```json
  {
    "token": "<JWT-токен>"
  }
  ```

- **GET /api/info**  
  Получаешь инфу о своих монетах, купленных товарах и истории транзакций. Не забудь передать заголовок:
  ```
  Authorization: Bearer <твой токен>
  ```

- **POST /api/sendCoin**  
  Переводи монеты другому пользователю. Пример запроса:
  ```json
  {
    "toUser": "user2",
    "amount": 100
  }
  ```
  Обязательно указывай заголовок `Authorization`.

- **GET /api/buy/{item}**  
  Купи мерч (например, `cup`, `t-shirt` и т.д.). Просто замени `{item}` на нужное название и не забудь заголовок `Authorization`.

## Как запустить сервис

### Через Docker Compose

1. Убедись, что у тебя установлены Docker и Docker Compose.
2. В корне проекта запусти:
   ```bash
   docker-compose up --build
   ```
3. Открывай браузер и переходи по адресу [http://localhost:8080](http://localhost:8080) — сервер там уже работает.

### Без Docker (локально)

1. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Запусти сервер:
   ```bash
   python app.py
   ```
   Сервер стартует на порту **4000** (а в Docker Compose он проброшен на 8080).

## Переменные окружения

- **DB_URL** – строка подключения к базе данных. По умолчанию для Docker:
  ```
  postgresql://postgres:password@db:5432/shop
  ```
- **JWT_SECRET_KEY** – секрет для генерации JWT. В продакшене обязательно поменяй его на свой!

## Тесты

Чтобы запустить unit и интеграционные тесты, сделай так:
```bash
python -m unittest discover -s tests
```

## Линтинг

Конфигурация для flake8 лежит в файле [`.flake8`](.flake8).

## Что ещё есть в проекте

- **Тесты:** Есть unit и интеграционные тесты (папка `tests`), покрытие выше 40%.
- **Автоматическое создание БД:** Таблицы создаются при первом запросе.
- **Покупка мерча и переводы:** Логика покупки и перевода монет полностью реализована (см. эндпоинты `/api/buy` и `/api/sendCoin`).

---

```
