## Сбор статистики
[Вход](https://umami.is/docs/login)
[Добавление сайта](https://umami.is/docs/add-a-website)
В HTML Head необходимые скрипты уже вставлены, трекинга кнопок пока нет

## Изменения в работе с БД
- Данные теперь возвращаются в виде моделей Pydantic, а не словарей. Взаимодействие с Jinja никак не изменилось, код на фронте менять не надо.
- Операции чтения и записи теперь выполняются асинхронно.
- Репозитории с функциями передаются в эндпоинты через Dependency Injection
- Коннекты к БД всё также закрываются после выполнения запроса, как и в синхронном варианте

## 🚀 Запуск проекта

### 1. Установка зависимостей

```sh
pip install -r requirements.txt
```

**Примечание:** Если при установке возникают ошибки, возможно, потребуется установить дополнительные библиотеки. Проверьте сообщения об ошибках и установите недостающие пакеты.

### 2. Запуск приложения

```sh
uvicorn main:app --reload
```
**или**
```sh
fastapi dev main.py
```
### 3. Просмотр приложения

После успешного запуска приложение будет доступно по адресу: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## 📂 Структура проекта

```
app/
│   main.py
│   __init__.py
│
├───db
│       database.py
│       db.py
│       owner.db
│       repo.py
│       responses.txt
│       survey.db
│       survey_old.db
│       __init__.py
│
├───routes
│       dependencies.py
│       __init__.py
│
├───schemas
│       schemas.py
│       __init__.py
│
├───services
│       calculator.py
│       __init__.py
│
├───static
│       Picture1.jpg
│       Picture2.jpg
│       Picture3.jpg
│       Picture4.jpg
│       script.js
│       style.css
│       style_gloss.css
│       style_menu.css
│       style_stats.css
│       style_user.css
│
├───templates
│       contract.html
│       economic.html
│       glossary.html
│       index.html
│       owner.html
│       result_econom.html
│       stats.html
│       survey1.html
│       user.html
```

## 📝 Дополнительная информация

- **survey.db**: База данных, содержащая вопросы для опроса. Убедитесь, что этот файл присутствует в корневой директории проекта перед запуском.
- **responses.db**: База данных для хранения ответов пользователей. Создается автоматически при первом запуске приложения.
- **responses.txt**: Файл, в который сохраняются ответы пользователей в текстовом формате для удобства анализа.
