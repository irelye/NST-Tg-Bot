from enum import Enum
import os
import asyncio
from aiogram.types.file import File
import sqlite3
from sqlite3 import Error as DBError
from nst_tg_bot.file_manager import FileManager
from nst_tg_bot.model.model import Model


class InputType(Enum):
	CONTENT = 0,
	STYLE = 1


class RequestHandler():
	"""
	Class for managing queries from bot.
	Uses MySQL DB for tracking current requests.
	"""

	def __init__(self,
		         file_manager: FileManager,
		         path_to_db: str,
		         waiting_time: int):
		"""
		:param file_manager: nst_tg_bot.file_manager.FileManager object.
		:param waiting_time: maximum time for user to send the second file. After that time handler may forget about already sent file.
		:param path_to_db: path to folder, where MySQL DB file will be stored.
		"""

		self.__file_manager = file_manager
		self.__model = Model()
		self.__path_to_db = path_to_db + "/queries.sqlite"

		if not os.path.exists(self.__path_to_db):
			try:
				connection = sqlite3.connect(self.__path_to_db)

				cursor = connection.cursor()
				cursor.execute(Queries.CREATE_TABLE)
				connection.commit()

				connection.close()
			except DBError as e:
				print(f"DB error occured: {e}")
				quit()

		self.__waiting_time = waiting_time

	async def remove_old_task(self):
		"""
		Coroutine that has an infinite cycle with forgetting marked queries, marking unmarked ones and sleeping for a specified time.
		"""

		await asyncio.sleep(self.__waiting_time)

		while True:
			try:
				connection = sqlite3.connect(self.__path_to_db)

				files_to_release = self.__get_marked(connection)

				for file1_path, file2_path in files_to_release:
					if file1_path is not None:
						self.__file_manager.release_file(file1_path)
					if file2_path is not None:
						self.__file_manager.release_file(file2_path)

				self.__delete_marked(connection)
				self.__mark(connection)

				connection.close()
			except DBError as e:
				print(f"DB error occured: {e}")

			await asyncio.sleep(self.__waiting_time)

	def __get_marked(self, connection):
		cursor = connection.cursor()
		cursor.execute(Queries.GET_MARKED)
		
		return cursor.fetchall()

	def __delete_marked(self, connection):
		cursor = connection.cursor()
		cursor.execute(Queries.DELETE_MARKED)
		connection.commit()

	def __mark(self, connection):
		cursor = connection.cursor()
		cursor.execute(Queries.MARK)
		connection.commit()

	async def set_input(self, in_type: InputType, file: File, chat_id: int):
		"""
		Attaches input file to the query.
		:param in_type: type of the file. Check nst_tg_bot.request_handler.InputType.
		:param file: the aiogram file object.
		:param chat_id: id of the telegram chat with that query. 
		"""

		file_path = await self.__file_manager.get_local_path(file)

		await asyncio.sleep(0.01)

		try:
			connection = sqlite3.connect(self.__path_to_db)

			if self.__is_new_query(chat_id, connection):
				self.__create_entry(chat_id, connection)

			await asyncio.sleep(0.01)

			if in_type is InputType.CONTENT:
				content_path, _ = self.__get_input(chat_id, connection)
				if content_path is not None:
					self.__file_manager.release_file(content_path)

				self.__set_content(chat_id, file_path, connection)

			if in_type is InputType.STYLE:
				_, style_path = self.__get_input(chat_id, connection)
				if style_path is not None:
					self.__file_manager.release_file(style_path)

				self.__set_style(chat_id, file_path, connection)

			connection.close()
		except DBError as e:
			print(f"DB error occured: {e}")

	def __is_new_query(self, chat_id: int, connection):
		cursor = connection.cursor()
		cursor.execute(Queries.GET_INPUT % chat_id)

		return len(cursor.fetchall()) == 0

	def __create_entry(self, chat_id: int, connection):
		cursor = connection.cursor()
		cursor.execute(Queries.CREATE_ENTRY % chat_id)
		connection.commit()

	def __get_input(self, chat_id: int, connection):
		cursor = connection.cursor()
		cursor.execute(Queries.GET_INPUT % chat_id)
		return cursor.fetchall()[0]

	def __set_content(self, chat_id: int, file_path: str, connection):
		cursor = connection.cursor()
		cursor.execute(Queries.SET_CONTENT % (file_path, chat_id))
		connection.commit()

	def __set_style(self, chat_id: int, file_path: str, connection):
		cursor = connection.cursor()
		cursor.execute(Queries.SET_STYLE % (file_path, chat_id))
		connection.commit()

	def ready_for_transfer(self, chat_id):
		"""
		:param chat_id: id of the chat with a query.
		:returns: True if all necessary input files are sent.
		"""

		try:
			connection = sqlite3.connect(self.__path_to_db)

			content_path, style_path = self.__get_input(chat_id, connection)

			if content_path is None or style_path is None:
				result = False
			else:
				result = True

			connection.close()
		except DBError as e:
			print(f"DB error occured: {e}")

		return result

	async def execute_query(self, chat_id: int):
		"""
		:param chat_id: id of the chat with a query.
		:returns: None if not all the inputs are sent, a tempfile with the result otherwise. This tempfile will be automatically deleted as soon as you close it.
		"""

		try:
			connection = sqlite3.connect(self.__path_to_db)

			content_path, style_path = self.__get_input(chat_id, connection)

			await asyncio.sleep(0.01)

			if content_path is None or style_path is None:
				result = None
			else:
				cursor = connection.cursor()
				cursor.execute(Queries.DELETE % chat_id)
				connection.commit()

				await asyncio.sleep(0.01)

				result = await self.__model.transfer_style(content_path, style_path)
				
				self.__file_manager.release_file(content_path)
				self.__file_manager.release_file(style_path)

			connection.close()
		except DBError as e:
			print(f"DB error occured: {e}")

		return result


class Queries():
	CREATE_TABLE = """
		CREATE TABLE IF NOT EXISTS queries (
  			chat_id INT PRIMARY KEY,
  			content TEXT,
  			style   TEXT,
  			marked  INTEGER NOT NULL
		);
	"""
	MARK          = "UPDATE queries SET marked=1 WHERE marked=0;"
	DELETE_MARKED = "DELETE FROM queries WHERE marked=1;"
	GET_MARKED    = "SELECT content, style FROM queries WHERE marked=1;"
	DELETE        = "DELETE FROM queries WHERE chat_id=%d;"
	GET_INPUT     = "SELECT content, style FROM queries WHERE chat_id=%d;"
	CREATE_ENTRY  = "INSERT INTO queries (chat_id, marked) VALUES (%d, 0);"
	SET_CONTENT   = "UPDATE queries SET content=\"%s\" WHERE chat_id=%d;"
	SET_STYLE     = "UPDATE queries SET style=\"%s\" WHERE chat_id=%d;"
