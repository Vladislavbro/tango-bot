# Танго Бот

Простой Telegram бот для записи на бесплатный урок танго.

## Установка

1.  Клонируйте репозиторий:
    ```bash
    git clone <url-репозитория>
    cd tango-bot
    ```
2.  Создайте и активируйте виртуальное окружение:
    ```bash
    python -m venv venv
    source venv/bin/activate  # для Linux/macOS
    # venv\Scripts\activate  # для Windows
    ```
3.  Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```
4.  Создайте файл `.env` в корневой папке проекта и добавьте в него токен вашего бота:
    ```
    TELEGRAM_BOT_TOKEN=ВАШ_ТЕЛЕГРАМ_БОТ_ТОКЕН
    ```

## Запуск

```bash
python main.py
``` 