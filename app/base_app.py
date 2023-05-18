from abc import ABC, abstractmethod
from app.db import DBTool
from app.parser import SiriustParser
from app.entities import User


class BaseApp(ABC):
    """Абстрактный класс, описывающий работу приложения"""
    def __init__(self, db:DBTool, parser: SiriustParser) -> None:
        """
        Инициализация экземпляра класса.

        Args:
            db: DBTool - объект, реализующий взаимодействие с БД.
            parser: SiriustParser - парсер сайта.
        """
        self._db = db
        self._parser = parser
        self._users = self.load_users()
        self._chosen_user = None

    @abstractmethod
    def run(self) -> None:
        """Запуск приложения."""

    @abstractmethod
    def log_in(self) -> None:
        """
        Авторизация на сайте и сохранение полученной информации
        о пользователе в _chosen_user.
        """

    def save_in_bd(self) -> None:
        """Сохранение пользовательских данных в БД."""
        self._db.add_or_update_user(self._chosen_user)

    def update_data(self) -> None:
        """
        Повторный парсинг сайта и сохранение полученной информации
        в _chosen_user.
        """
        self._parser.log_in(self._chosen_user.email, self._chosen_user.password)
        self._chosen_user =  self._parser.parse()

    def load_users(self) -> list[User]:
        """Получение списка пользовательских данных из БД."""
        return self._db.get_users()

    def save_to_file(self) -> None:
        """Сохранение пользовательских данных в файл."""
        with open('parser_result.txt', 'w') as f:
            f.write(str(self._chosen_user))
