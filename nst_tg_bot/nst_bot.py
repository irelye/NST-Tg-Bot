from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message
from aiogram.types.file import File
from aiogram.types.message import ContentType as mctp
from aiogram.dispatcher import filters
from nst_tg_bot.text import Strings
import nst_tg_bot.config as config
from nst_tg_bot.file_manager import FileManager
from nst_tg_bot.request_handler import RequestHandler, InputType


bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)
fmanager = FileManager(bot,
	                   config.DOWNLOADS,
	                   config.CLEARING_TIME,
	                   config.DATABASES)
handler = RequestHandler(fmanager,
                         config.DATABASES,
                         config.WAITING_TIME)


@dp.message_handler(filters.Command(['start']))
async def on_start_cmd(message: Message):
	await message.reply(Strings.START_MESSAGE)

@dp.message_handler(filters.Command(['help']))
async def on_help_cmd(message: Message):
	await message.reply(Strings.HELP_MESSAGE)

@dp.message_handler(filters.Command(['info']))
async def on_info_cmd(message: Message):
	await message.reply(message)

@dp.message_handler(filters.Command(['links']))
async def on_links_cmd(message: Message):
	await message.reply(Strings.LINKS_MESSAGE)

async def save_content(file: File, chat_id: int):
	await handler.set_input(InputType.CONTENT, file, chat_id)

@dp.message_handler(filters.Command(['content'], ignore_caption=False),
	                content_types=mctp.PHOTO)
async def on_content_image(message: Message):
	file = await bot.get_file(message.photo[-1]['file_id'])
	chat_id = message.chat['id']
	await save_content(file)

@dp.message_handler(filters.Command(['content']),
				    content_types=mctp.TEXT)
async def on_forwarded_content_image(message: Message):
	if message.reply_to_message is None:
		await message.reply(Strings.NO_CONTENT_IMAGE)
	elif not message.reply_to_message.photo:
		await message.reply(Strings.NO_CONTENT_IMAGE)
	else:
		file = await bot.get_file(message.reply_to_message.photo[-1]['file_id'])
		chat_id = message.chat['id']
		await save_content(file, chat_id)

async def save_style(file: File, chat_id: int):
	await handler.set_input(InputType.STYLE, file, chat_id)

@dp.message_handler(filters.Command(['style'], ignore_caption=False),
	                content_types=mctp.PHOTO)
async def on_style_image(message: Message):
	file = await bot.get_file(message.photo[-1]['file_id'])
	chat_id = message.chat['id']
	await save_style(file)

@dp.message_handler(filters.Command(['style']),
				    content_types=mctp.TEXT)
async def on_forwarded_style_image(message: Message):
	if message.reply_to_message is None:
		await message.reply(Strings.NO_STYLE_IMAGE)
	elif not message.reply_to_message.photo:
		await message.reply(Strings.NO_STYLE_IMAGE)
	else:
		file = await bot.get_file(message.reply_to_message.photo[-1]['file_id'])
		chat_id = message.chat['id']
		await save_style(file, chat_id)


if __name__ == '__main__':
    executor.start_polling(dp)