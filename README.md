# Проект парсинга pep

## Описание проекта парсинга pep

«Парсинг pep»: приложение, с помощью которого пользователи могут парсить страницы документации сайта python.

## Запуск проекта
1. Клонирование репозитория
   ```
   git@github.com:slavdosya/bs4_parser_pep.git
   ```
3. Создание виртуального окружения и его запуска
   ```
   python3 -m venv venv
   ```
4. ```
   source /venv/bin/activate
   ```
5. Установка зависимостей
   ```
   pip install -r requirements.txt
   ```
### Команды для запуска

Запускать парсер необходимо из папки src. 
Команда для запуска:
```
python main.py mode flag
```
```
где, mode - режим работы парсера (обязательно)
     flag - выбор режима вывода (опционально)
```
