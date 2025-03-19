import os
import uuid
import json
import logging

from datetime import datetime
from typing import List, Dict


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data() -> List[Dict]:
    if not os.path.exists('data.json'):
        with open('data.json', 'w', encoding='utf-8') as file:
            json.dump([], file)
        return []
    with open('data.json', 'r', encoding='utf-8') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            logger.error('Ошибка при чтении JSON-файла. Возвращаем пустой список.')
            return []


def save_data(data: List[Dict]):
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def create_backup():
    if os.path.exists('data.json'):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f'data_backup_{timestamp}.json'
        with open('data.json', 'r', encoding='utf-8') as original, open(backup_filename, 'w', encoding='utf-8') as backup:
            backup.write(original.read())
        logger.info(f'Создана резервная копия: {backup_filename}')


def add_announcement(announcement: Dict):
    if not all(key in announcement for key in ['price', 'district', 'photo', 'city', 'address', 'user_id']):
        raise ValueError("Объявление должно содержать все обязательные поля: price, district, photo, city, user_id")

    announcement['id'] = str(uuid.uuid4())

    data = load_data()
    data.append(announcement)
    save_data(data)
    create_backup()

    logger.info(f"Добавлено объявление: {announcement}")


def delete_announcement(announcement_id: str):
    data = load_data()
    data = [i for i in data if i['id'] != announcement_id]
    save_data(data)
    create_backup()


def get_announcements_by_user(user_id: int) -> List[Dict]:
    data = load_data()

    logger.info(f"Запрошены объявления для user_id: {user_id}")
    logger.info(f"Все объявления: {data}")

    return [i for i in data if i['user_id'] == user_id]


def get_announcements_by_city(city: str) -> List[Dict]:
    data = load_data()
    return [i for i in data if i['city'] == city]


def get_announcements_by_district(district: str) -> List[Dict]:
    data = load_data()
    return [i for i in data if i['district'] == district]
