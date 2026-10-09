# DF1 — API для управления библиотекой

Дипломный проект. REST API для управления библиотекой: книги, авторы, жанры, пользователи, выдача книг.

**Автор:** Виктор Безуглов

---

## Стек

- Python 3.12, Django, Django REST Framework
- PostgreSQL
- JWT-авторизация (SimpleJWT)
- Docker, Docker Compose
- Nginx, Gunicorn
- drf-spectacular (OpenAPI)
- GitHub Actions (CI/CD)
- Yandex Cloud

---

## Возможности

- Регистрация и JWT-авторизация
- Роли: библиотекарь, читатель
- CRUD для авторов, жанров, книг, выдач
- Выдача и возврат книг, отметка о потере
- Автоматическое управление количеством доступных экземпляров
- Фильтрация, поиск, сортировка, пагинация
- Права доступа по ролям
- OpenAPI-документация (Swagger UI)

---

## Быстрый старт

### Требования
- Docker, Docker Compose

### Запуск

1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/bezza8418/df1_library_api_diploma.git
   cd df1_library_api_diploma
   ```
2. Создать .env (по образцу .env.template):

    ```bash
    cp .env.template .env
    ```
Заполнить SECRET_KEY, POSTGRES_PASSWORD.

3. Запустить:

    ```bash
    docker compose up -d --build
    ```

4. Применить миграции и создать суперпользователя:

    ```bash
    docker compose exec web python manage.py migrate
    docker compose exec web python manage.py createsuperuser
    ```

### Доступ
 - API: http://localhost:8000/api/

 - Swagger UI: http://localhost:8000/api/schema/swagger-ui/

 - Админка: http://localhost:8000/admin/

### Демо (production)
 - Swagger UI: http://111.88.242.42/api/schema/swagger-ui/

 - Админка: http://111.88.242.42/admin/

### Основные эндпоинты

|Метод   |URL   |Описание   |
|---|---|---|
|POST   |/api/users/register/   |Регистрация   |
|POST   |/api/users/token/   |Получить JWT   |
|POST   |/api/users/token/refresh/   |Обновить JWT   |
|GET   |/api/users/me/   |Профиль   |
|GET/POST   |/api/library/authors/   |Авторы   |
|GET/POST   |/api/library/genres/   |Жанры   |
|GET/POST   |/api/library/books/   |Книги   |
|GET/POST   |/api/library/loans/   |Выдачи   |
|POST   |/api/library/loans/{id}/return_book/   |Вернуть книгу   |
|POST   |/api/library/loans/{id}/mark_lost/   |Отметить как потерянную   |


### Тесты

```bash
    docker compose exec web python manage.py test
```

Структура проекта
```text
df1_library_api_diploma/
├── library_api/        # настройки Django
├── users/              # пользователи, JWT, permissions
├── library/            # книги, авторы, жанры, выдачи
├── nginx/              # конфиг Nginx
├── postman/            # Postman-коллекция
├── .github/workflows/  # CI/CD
├── docker-compose.yml       # dev
├── docker-compose.prod.yml  # production
├── Dockerfile
└── requirements.txt
```

### Лицензия

Учебный проект.
