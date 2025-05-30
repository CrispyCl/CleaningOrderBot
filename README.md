# CleaningOrder

## Инструкция по запуску:

### Создайте ".env" файл в корневой директории проекта.

```bash
cp .env.example .env
```

В Windows:

```bat
copy .env.example .env
```

Заполните файл переменными окружения.

(Пример файла .env)

```yml
# Bot environments
BOT_TOKEN=
DEBUG=false
LOGGER_FILE_PATH="app.log"

# Database environments
POSTGRES_USER=root
POSTGRES_PASSWORD=111
POSTGRES_DB=db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379
```

После заполнения .env файла требуется перезапустить терминал.

### Запуск баз данных:

Выполните команду:

```bash
docker-compose up -d redis postgres
```

## Готовим бота к локальному запуску:

### Настройте и активируйте окружение:

```bash
python -m venv venv
source venv/bin/activate
```

В Windows:

```bat
venv\Scripts\activate
```

### Установите зависимости:

```bash
pip install -r requirements/prod.txt
```

### Применить миграции:

```bash
cd bot
alembic upgrade head
cd ..
```

## Запуск бота через Docker:

```bash
docker-compose up -d
```

## Запуск бота через консоль:

(выполнить шаги настройки виртуального окружения и установки зависимостей)

```bash
docker-compose up -d redis postgres
python bot/
```

## Добавляем пользователя-администратора:

### Затем выполните команду:

```bash
python bot/scripts.py
```

#### Выберите пункт 1 и следуйте инструкциям.

Пользователь предварительно должен написать боту /start

После обновления прав пользователь должен написать боту /start

