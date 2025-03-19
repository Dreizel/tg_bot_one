import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database import (
    load_data, add_announcement, delete_announcement,
    get_announcements_by_user, get_announcements_by_city, get_announcements_by_district
)


router = Router()

main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='🏠 Сдать квартиру', callback_data='rent_out'),
            InlineKeyboardButton(text='🔍 Снять квартиру', callback_data='rent')
        ]
    ]
)

out_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='➕ Добавить объявление', callback_data='add_ad'),
            InlineKeyboardButton(text='📋 Мои объявления', callback_data='my_advertisements')
        ]
    ]
)


class AnnouncementStates(StatesGroup):
    price = State()
    district = State()
    photo = State()
    city = State()
    address = State()


class SearchStates(StatesGroup):
    city = State()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    await message.answer('🏠 **Добро пожаловать в бота для аренды жилья!**\n\n'
                         'Выберите действие:',
                         reply_markup=main_keyboard)


@router.callback_query(F.data == 'rent_out')
async def handle_rent_out(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🏠 **Вы выбрали 'Сдать квартиру'.**\n\n"
                                  "Выберите следующие действие:",
                                  reply_markup=out_keyboard)
    await callback.answer()


@router.callback_query(F.data == 'add_ad')
async def handle_add_ad(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('💰 **Введите цену:**')
    await state.set_state(AnnouncementStates.price)
    await callback.answer()


@router.message(AnnouncementStates.price)
async def process_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('❌ **Цена должна быть числом.** Попробуйте еще раз.')
        return
    await state.update_data(price=message.text)
    await message.answer('📍 **Введите район:**')
    await state.set_state(AnnouncementStates.district)


@router.message(AnnouncementStates.district)
async def process_district(message: Message, state: FSMContext):
    if not message.text:
        await message.answer('❌ **Район не может быть пустым.** Попробуйте еще раз.')
        return
    await state.update_data(district=message.text)
    await message.answer('📷 **Отправьте фото квартиры:**')
    await state.set_state(AnnouncementStates.photo)


@router.message(AnnouncementStates.photo)
async def process_photo(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(photo=message.photo[-1].file_id)
        await message.answer('📍 **Введите город:**')
        await state.set_state(AnnouncementStates.city)
    else:
        await message.answer('❌ **Пожалуйста, отправьте фото.**')


@router.message(AnnouncementStates.city)
async def process_city(message: Message, state: FSMContext):
    if not message.text:
        await message.answer('❌ **Город не может быть пустым.** Попробуйте еще раз.')
        return
    await state.update_data(city=message.text)
    await message.answer('🏠 **Введите адрес квартиры:**')
    await state.set_state(AnnouncementStates.address)


@router.message(AnnouncementStates.address)
async def process_address(message: Message, state: FSMContext):
    if not message.text:
        await message.answer('❌ **Адрес не может быть пустым.** Попробуйте еще раз.')
        return

    await state.update_data(address=message.text)

    data = await state.get_data()

    data['user_id'] = message.from_user.id

    try:
        add_announcement(data)
        await message.answer('✅ **Объявление успешно добавлено!**')
    except ValueError as e:
        await message.answer(f"❌ **Ошибка:** {e}")
    finally:
        await state.clear()


@router.callback_query(F.data == 'rent')
async def handle_rent(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('🔍 **Введите город для поиска:**')
    await state.set_state(SearchStates.city)
    await callback.answer()


@router.message(SearchStates.city)
async def filter_by_city(message: Message, state: FSMContext):
    city = message.text
    announcements = get_announcements_by_city(city.title())
    if not announcements:
        await message.answer('❌ **Нет объявлений в этом городе.**')
    else:
        for announcement in announcements:
            await message.answer_photo(
                        announcement['photo'],
                        caption=(
                            f"🏠 **Объявление:**\n\n"
                            f"💰 **Цена:** {announcement['price']}\n"
                            f"📍 **Район:** {announcement['district']}\n"
                            f"🌆 **Город:** {announcement['city']}"
                            f"🏡 **Адрес:** {announcement['address']}"
                        )
                    )
    await state.clear()


@router.callback_query(F.data == 'my_advertisements')
async def handle_my_advertisements(callback: CallbackQuery):
    user_id = callback.from_user.id
    announcements = get_announcements_by_user(user_id)
    if not announcements:
        await callback.message.answer('❌ **У вас нет объявлений.**')
    else:
        for announcement in announcements:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text='🗑️ Удалить', callback_data=f'delete_{announcement['id']}'))
            await callback.message.answer_photo(
                announcement['photo'],
                caption=(
                    f"🏠 **Ваше объявление:**\n\n"
                    f"💰 **Цена:** {announcement['price']}\n"
                    f"📍 **Район:** {announcement['district']}\n"
                    f"🌆 **Город:** {announcement['city']}"
                    f"🏡 **Адрес:** {announcement['address']}"
                ),
                reply_markup=builder.as_markup()
            )


@router.callback_query(F.data.startswith('delete_'))
async def delete_announcement_handler(callback: CallbackQuery):
    announcement_id = callback.data.split('_')[1]
    delete_announcement(announcement_id)
    await callback.message.answer('✅ **Объявление удалено.**')
    await callback.answer()
