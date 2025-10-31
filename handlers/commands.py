from aiogram import Router #роутер
from aiogram.types  import Message,InlineKeyboardButton,InlineKeyboardMarkup,BotCommand #инлаин кнопки и message
from aiogram.filters import Command #для создания команд
import os #для работы с файлами?
from sqlalchemy.orm import Session #для работы с sqlalchemy и импорт Session
from utils.zip_archiver import zip_archive #путь к файлу и импортируем функцию из файла
from sqlalchemy import create_engine
from models.memory import Memori #импорт бд 
from aiogram.types import BufferedInputFile
router = Router()


help_text = """Ваш архив с воспоминаниями готов! 💾

Чтобы гарантированно увидеть все фотографии и файлы в отчете, выполните 2 простых шага:

1.  Распакуйте архив (кликните правой кнопкой мыши и выберите «Извлечь все...» или «Распаковать»).
2.  Откройте файл memories_XX.html (где XX — ваш ID) из созданной папки.



❌ Внимание! Не открывайте HTML-файл прямо из ZIP-архива. В этом случае браузер не сможет найти картинки, и вы увидите пустые места."""

commands_for_menu = [
    BotCommand(command='/start', description='👋 Начать работу / Приветствие'),
    BotCommand(command='/help', description='❓ Показать помощь и инструкции'),
    BotCommand(command='/export', description='📂 Получить мой ZIP-архив с воспоминаниями'),
    BotCommand(command='/clear', description='❌ Удалить все из архива'),
]


@router.message(Command('start')) #команда старт для запуска бота
async def start(message:Message):
    await message.answer('Привет! Отправляй мне фото или файлы — я сохраню их как твои воспоминания. Используй /search для поиска и /export для экспорта всего архива.')#сообщение пользователю
@router.message(Command('help'))
async def help(message:Message):
    await message.answer('Отправь фото или файл. Используй /search <слово> для поиска по имени файла. /export — экспортировать полный архив в ZIP.')
@router.message(Command('search')) #для поиска фото/файла
async def search(message:Message):
    text = message.text.split(maxsplit=1)
    if len(text) <2:
        await message.answer('напишите так /search <название>')
        return
    searc = text[1].strip()
    engine = create_engine('sqlite:///memory.db')
    with Session(bind=engine) as db:
        memori = db.query(Memori).filter(Memori.user_id == message.from_user.id,
                                 Memori.original_name.ilike(f'%{searc}%')
                                 ).order_by(Memori.created_at.desc()).all()
    poisk = f'нашел{len(memori)}'
    for i,memor in enumerate(memori,1):
        if memor.type == 'photo':
            poisk += f'{i} {memor.original_name}'
        else:
            poisk += f'{i} {memor.original_name}'
    await message.answer(poisk)

@router.message(Command('export'))
async def export(message:Message):
    engine = create_engine('sqlite:///memory.db')
    with Session(bind=engine) as db:
        memories = db.query(Memori).filter(
            Memori.user_id == message.from_user.id
        ).all()

    zip_fl = zip_archive(message.from_user.id,memories)
    with open(zip_fl,'rb') as f:
        zip_data = f.read()
    document = BufferedInputFile(zip_data,filename='memories_arh.zip')
    await message.answer_document(document=document,caption='ваш архив')
    os.remove(zip_fl)
    await message.answer(f'{help_text}')
@router.message(Command('clear'))
async def clear(message:Message):
    id_use = message.from_user.id
    engine = create_engine('sqlite:///memory.db')
    with Session(bind=engine) as db:
        prove_id = db.query(Memori).filter(Memori.user_id == id_use).all
        if not prove_id:
            await message.answer('❌ у тебя нет файлов в архиве')
        else:
            for file in prove_id:
                db.delete(file)
                await message.answer('все файлы удалены')
            db.commit()