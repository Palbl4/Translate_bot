import json
from random import shuffle, choice

import peewee
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardMarkup

import os
import re

from models import User, WordTranslate, Word, Translate

token = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(token)
pattern = re.compile(r'/add[\s]([\w]+)[\s]([\w]+)')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    b1 = KeyboardButton('/start')
    b2 = KeyboardButton('/testing')
    b3 = KeyboardButton('/list')
    kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
    kb_client.row(b1, b2, b3)
    await token.send_message(message.from_user.id,
                             f'Hello {message.from_user.full_name}'
                             f', lets start learning!\n Что бы добавить слово '
                             f'введи команду "/add word слово".\n'
                             f'Что бы посмотрет список всех твоих слов нажми'
                             f'"/list".'
                             f'\n Для начала работы, добавь 4 слова и '
                             f'начинай тестирование \n"/testing".\nGood luck',
                             reply_markup=kb_client)


@dp.message_handler(commands='list')
async def full_list(message: types.Message):
    user = User.get(User.external_id == message.from_user.id)
    pairs = WordTranslate.select().where(WordTranslate.user == user)
    for row in pairs:
        await token.send_message(message.from_user.id,
                                 f'{row.word.word} - {row.translate.translate}')


@dp.message_handler(commands=['add'])
async def add_word(message: types.Message):
    user, __ = User.get_or_create(external_id=message.from_user.id,
                                  chat_id=message.chat.id)
    txt = message.text
    result = pattern.match(txt)
    raw_word, raw_translate = tuple(i.lower() for i in result.groups())
    word, _ = Word.get_or_create(word=raw_word, user=user)
    translate, _ = Translate.get_or_create(translate=raw_translate, user=user)
    WordTranslate.get_or_create(word=word, translate=translate, user=user)
    await token.send_message(message.from_user.id,
                             f'🆕 Добавлено слово "{raw_word}" с переводом "{raw_translate}"')


@dp.message_handler(commands=['testing'])
async def get_test(message, user=None):
    user = user or User.get(User.external_id == message.from_user.id)
    pairs = WordTranslate.select() \
        .where(WordTranslate.user == user) \
        .order_by(peewee.fn.Random()) \
        .limit(4)
    markup = InlineKeyboardMarkup()
    buttons = []
    answer = None
    for row in pairs:
        word = Word.get(Word.id == row.word.id, Word.user == row.user)
        if answer is None:
            answer = word
        translate = Translate.get(Translate.id == row.translate.id,
                                  Translate.user == row.user)
        btn = InlineKeyboardButton(
            text=f'{row.translate.translate}',
            callback_data=json.dumps(
                {"t": "a", "q": answer.id, "a": translate.id}
            )
        )
        buttons.append(btn)
    shuffle(buttons)
    markup.add(*buttons[:2])
    markup.add(*buttons[2:])
    await token.send_message(user.chat_id, f"❔🇺🇸 Слово {answer.word}",
                             reply_markup=markup)


@dp.callback_query_handler()
async def one_callback(callback):
    user = User.get(User.external_id == callback.from_user.id)
    if callback.message:
        msg = json.loads(callback.data)
        if msg['t'] == 'a':
            markup = InlineKeyboardMarkup()
            btn = InlineKeyboardButton(
                text=f'Еще?', callback_data=json.dumps({"t": "m"})
            )
            markup.add(btn)
            try:
                wt: WordTranslate = WordTranslate \
                    .get(WordTranslate.word_id == msg["q"],
                         WordTranslate.user == user,
                         WordTranslate.translate_id == msg['a'])
                await token.send_message(user.chat_id, f"✅ Правильный ответ",
                                         reply_markup=markup)
                await callback.answer()
            except peewee.DoesNotExist:
                _wt: WordTranslate = WordTranslate \
                    .get(WordTranslate.word_id == msg["q"],
                         WordTranslate.user == user)
                t = Translate.get(Translate.id == _wt.translate_id)
                await token.send_message(user.chat_id,
                                         f"❌ Ошибка, правильный ответ - {t.translate}",
                                         reply_markup=markup)
                await callback.answer()
        if msg["t"] == "m":
            await get_test(callback.message, user)
            await callback.answer()


executor.start_polling(dp, skip_updates=True)
