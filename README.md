[![CI/CD Status](https://github.com/Shagin-SN/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Shagin-SN/foodgram/actions)
# Проект Foodgarm

## Описание проекта

«Фудграм» — сайтом, на котором пользователи могут публиковать свои рецепты,
добавлять чужие рецепты в избранное и подписываться на публикации других авторов.
Зарегистрированным пользователям доступен сервис «Список покупок».
Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Shagin-SN/foodgarm.git
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
cd backend
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

Импорт списка ингридиентов^

```
python3 manage.py import_ingredients
```
=======

## Примеры запросов к API

Регистрация пользователя

```
Запрос:
POST /api/users/
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "first_name": "Имя",
  "last_name": "Фамилия",
  "password": "string"
}

Ответ:
{
  "email": "user@example.com",
  "id": 0,
  "username": "username",
  "first_name": "Имя",
  "last_name": "Фамилия"
}
```

Получение списка рецептов

```
Запрос:
GET /api/recipes/

Ответ:
{
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=4",
  "previous": "http://foodgram.example.org/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "tags": [
        {
          "id": 0,
          "name": "Завтрак",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Пупкин",
        "is_subscribed": false
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
      "text": "string",
      "cooking_time": 1
    }
  ]
}
```

### Использованные технологии

Python 3.10+

Django 5.1.1

Django REST Framework

PostgreSQL

Pytest

Docker

GitHub Actions

### Авторы

Сергей Шагин https://github.com/Shagin-SN