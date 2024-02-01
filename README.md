# praktikum_new_diplom
![name badge](https://github.com/Anna9449/foodgram-project-react/actions/workflows/main.yml/badge.svg?event=push)
## Описание:

Foodgram - социальная сеть для обмена рецептами, которая дает возможность:
- добавлять/редактировать свои рецепты и просматривать рецепты всех пользователей
- подписываться на интересных авторов рецептов и следить за их новыми публикациями
- добавлять любимые рецепты в изранное
- сосавлять список покупок на основе любых опубликованных рецептов

### Технологии:

[![name badge](https://img.shields.io/badge/Python_d?logo=python&logoColor=white)](https://www.python.org/)
[![name badge](https://img.shields.io/badge/Django-logo=django&logoColor=white)](https://docs.djangoproject.com/en/4.2/releases/3.2/)
[![name badge](https://img.shields.io/badge/Django_REST_framework-logo=djangorestramework&logoColor=white)](https://www.django-rest-framework.org/)
[![name badge](https://img.shields.io/badge/PostgreSQL-logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![name badge](https://img.shields.io/badge/Gunicorn-logo=gunicorn&logoColor=white)](https://docs.gunicorn.org/en/latest/)
[![name badge](https://img.shields.io/badge/Nginx-logo=nginx&logoColor=white)](https://nginx.org/)
[![name badge](https://img.shields.io/badge/Docker-logo=docker&logoColor=white)](https://www.docker.com/)

### Как запустить проект:

Установить Docker Compose:

```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin 
```

Cоздать папку проекта и перейти в нее:

```
mkdir foodgram
cd foodgram
```

Создать файл .env и заполните его своими данными, пример: 

```
POSTGRES_DB=foodgram # Имя_БД
POSTGRES_USER=foodgram_user # Имя пользователя БД
POSTGRES_PASSWORD=foodgram_password # Пароль к БД
DB_NAME=foodgram
DB_HOST=db # Адрес, по которому Django будет соединяться с БД
DB_PORT=5432 # Порт соединения к БД
SECRET_KEY=*** # Секретный ключ Django (без кавычек).
ALLOWED_HOSTS=*** # Список разрешённых хостов (через запятую и без пробелов)
DEBUG=False # Выбрать режим отладки
```

Скачать файл docker-compose.yml и запустить его:

```
sudo docker compose -f docker-compose.yml up
```

Создаем и выполяем миграции, создаем суперпользователя, собираем статические файлы бэкенда и копируем их:

```
sudo docker compose -f docker-compose.yml exec backend python manage.py makemigrations
sudo docker compose -f docker-compose.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.yml exec backend python manage.py createsuperuser
sudo docker compose -f docker-compose.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.yml exec backend cp -r /app/static/. /static/static/ 
```

### Автор
[![name badge](https://img.shields.io/badge/Anna-Pestova-logo=github&logoColor=white)](https://github.com/Anna9449)

