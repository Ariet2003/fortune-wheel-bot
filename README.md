# Колесо Фортуны - Телеграм Бот

Телеграм бот для проведения розыгрышей призов среди учащихся 9-11 классов.

## Функциональность

### Для игроков:
- Регистрация с указанием ФИО и класса
- Участие в розыгрыше
- Просмотр выигранных призов

### Для администратора:
- Запуск розыгрыша
- Просмотр списка победителей
- Управление процессом розыгрыша

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/fortune-wheel-bot.git
cd fortune-wheel-bot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` и заполните его:
```
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_id_here
```

## Запуск

```bash
python main.py
```

## Использование

1. Для игроков:
   - Отправьте команду `/start` боту
   - Следуйте инструкциям для регистрации
   - Ожидайте начала розыгрыша

2. Для администратора:
   - Отправьте команду `/admin`
   - Используйте панель администратора для управления розыгрышем

## Призы

- 20 сертификатов на скидку 10%
- 5 кружек
- 5 блокнотов
- 5 ручек
- 5 шопперов 