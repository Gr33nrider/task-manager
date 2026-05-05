# Task_manager - Интеллектуальный планировщик задач

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-blue)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18.3-blue)](https://www.postgresql.org/)
[![GigaChat](https://img.shields.io/badge/GigaChat-AI-green)](https://developers.sber.ru/portal/products/gigachat)


Веб-приложение для управления задачами с интеграцией искусственного интеллекта GigaChat.
Ключевая особенность: при создании задачи AI автоматически разбивает её на подзадачи и оценивает время выполнения.

## Технологии

### Backend
| Технология | Назначение |
|------------|------------|
| **Python 3.14** | Язык программирования |
| **FastAPI** | Веб-фреймворк |
| **SQLAlchemy 2.0** | ORM |
| **Alembic** | Миграции БД |
| **PostgreSQL 18** | База данных |
| **Pydantic v2** | Валидация данных |
| **python-jose** | JWT токены |
| **passlib + bcrypt** | Хэширование паролей |
| **GigaChat API** | API для работы с запросами к ИИ GigaChat |
| **Celery** | Асинхронная очередь задач |
| **Redis** | Брокер сообщений для Celery и кеширование |


