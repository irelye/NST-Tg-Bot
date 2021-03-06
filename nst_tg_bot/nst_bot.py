import os
import asyncio
from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message
from aiogram.types.file import File
from aiogram.types.message import ContentType as mctp
from aiogram.dispatcher import filters
import nst_tg_bot.text as text
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


@dp.message_handler(filters.Command(['start'], ignore_caption=False),
                    content_types=mctp.TEXT)
async def on_start_cmd(message: Message):
	await message.reply(text.START_MESSAGE)


@dp.message_handler(filters.Command(['help'], ignore_caption=False),
                    content_types=mctp.TEXT)
async def on_help_cmd(message: Message):
	await message.reply(text.HELP_MESSAGE, parse_mode='Markdown')


@dp.message_handler(filters.Command(['info'], ignore_caption=False),
                    content_types=mctp.TEXT)
async def on_info_cmd(message: Message):
	await message.reply(text.INFO_MESSAGE)


@dp.message_handler(filters.Command(['links'], ignore_caption=False),
                    content_types=mctp.TEXT)
async def on_links_cmd(message: Message):
	await message.reply(text.LINKS_MESSAGE, parse_mode='Markdown', disable_web_page_preview=True)


async def save_content_and_execute(file: File, message: Message):
	chat_id = message.chat['id']
	await handler.set_input(InputType.CONTENT, file, chat_id)

	if not handler.ready_for_transfer(chat_id):
		await message.reply(text.SEND_STYLE)
	else:
		await message.reply(text.QUERY_RECEIVED)
		result = await handler.execute_query(chat_id)
		await bot.send_photo(photo=open(result.name, 'rb'),
		                     chat_id=chat_id,
		                     reply_to_message_id=message.message_id)
		result.close()


@dp.message_handler(filters.Command(['content'], ignore_caption=False),
                    content_types=mctp.PHOTO)
async def on_content_image(message: Message):
	file = await bot.get_file(message.photo[-1]['file_id'])
	await save_content_and_execute(file, message)


@dp.message_handler(filters.Command(['content'], ignore_caption=False),
                    content_types=mctp.DOCUMENT)
async def on_content_file(message: Message):
	if 'image' not in message.document['mime_type']:
		await message.reply(text.WRONG_FILE_FORMAT)
	else:
		file = await bot.get_file(message.document['file_id'])
		await save_content_and_execute(file, message)


@dp.message_handler(filters.Command(['content']),
                    content_types=mctp.TEXT)
async def on_forwarded_content(message: Message):
	if message.reply_to_message is None:
		await message.reply(text.NO_CONTENT_IMAGE)
	elif not message.reply_to_message.photo and \
	     not message.reply_to_message.document:
		await message.reply(text.NO_CONTENT_IMAGE)
	elif not message.reply_to_message.photo:
		if 'image' not in message.reply_to_message.document['mime_type']:
			await message.reply(text.WRONG_FILE_FORMAT)
		else:
			file = await bot.get_file(message.reply_to_message.document['file_id'])
			await save_content_and_execute(file, message)
	else:
		file = await bot.get_file(message.reply_to_message.photo[-1]['file_id'])
		await save_content_and_execute(file, message)


async def save_style_and_execute(file: File, message: Message):
	chat_id = message.chat['id']
	await handler.set_input(InputType.STYLE, file, chat_id)
	
	if not handler.ready_for_transfer(chat_id):
		await message.reply(text.SEND_CONTENT)
	else:
		await message.reply(text.QUERY_RECEIVED)
		result = await handler.execute_query(chat_id)
		await bot.send_photo(photo=open(result.name, 'rb'),
		                     chat_id=chat_id,
		                     reply_to_message_id=message.message_id)
		result.close()


@dp.message_handler(filters.Command(['style'], ignore_caption=False),
                    content_types=mctp.PHOTO)
async def on_style_image(message: Message):
	file = await bot.get_file(message.photo[-1]['file_id'])
	await save_style_and_execute(file, message)


@dp.message_handler(filters.Command(['style'], ignore_caption=False),
                    content_types=mctp.DOCUMENT)
async def on_style_file(message: Message):
	if 'image' not in message.document['mime_type']:
		await message.reply(text.WRONG_FILE_FORMAT)
	else:
		file = await bot.get_file(message.document['file_id'])
		await save_style_and_execute(file, message)


@dp.message_handler(filters.Command(['style']),
                    content_types=mctp.TEXT)
async def on_forwarded_style_image(message: Message):
	if message.reply_to_message is None:
		await message.reply(text.NO_STYLE_IMAGE)
	elif not message.reply_to_message.photo and \
	     not message.reply_to_message.document:
		await message.reply(text.NO_STYLE_IMAGE)
	elif not message.reply_to_message.photo:
		if 'image' not in message.reply_to_message.document['mime_type']:
			await message.reply(text.WRONG_FILE_FORMAT)
		else:
			file = await bot.get_file(message.reply_to_message.document['file_id'])
			await save_style_and_execute(file, message)
	else:
		file = await bot.get_file(message.reply_to_message.photo[-1]['file_id'])
		await save_style_and_execute(file, message)


async def on_startup(arg):
	asyncio.create_task(fmanager.clear_cache_task())
	asyncio.create_task(handler.remove_old_task())


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
