from getpass import getpass
from typing import Optional
from functools import wraps
from app.base_app import BaseApp
from app.parser import SiriustParser, AuthorizationError
from app.db import DBTool
from app.entities import User


class ConsoleApp(BaseApp):
    """
    Реализация утилиты как консольное приложение.
    """
    def __init__(self, db: DBTool, parser: SiriustParser) -> None:
        """
        Инициализация экземпляра класса.

        Args:
            db: DBTool - объект, реализующий взаимодействие с БД.
            parser: SiriustParser - парсер сайта.
        """
        super().__init__(db, parser)

    def _log(first_message: str = '', second_message: str = ''):
        """
        Декоратор для логирования выполнения метода, путем
        вывода двух сообщений - перед выполнений метода и после.

        Args:
            first_message: str - сообщение перед выполнением метода
                                 (default: '').
            second_message: str - сообщение после выполнение метода
                                 (default: '').
        """
        def first_wrapper(method):
            @wraps(method)
            def second_wrapper(self):
                if first_message:
                    print(first_message)
                method(self)
                if second_message:
                    print(second_message)
                return method
            return second_wrapper
        return first_wrapper

    def _choose_user(self) -> Optional[User]:
        """
        Выбор пользовательских данных из БД.

        Returns:
            Объект класса User, если пользователь выбран,
            иначе - None.
        """
        while True:
            answer = input('Найдены сохраненные данные. Использовать их? (y/n) ').strip().lower()
            if answer == 'n':
                return None
            elif answer == 'y':
                break
            else:
                print('Неправильный формат ответа.')
                continue

        print('Выберите пользователя:')
        for i in range(len(self._users)):
            print(f'{i+1}: {self._users[i].email}')
        while True:
            try:
                answer = int(input())
                if answer < 1 or answer > len(self._users):
                    raise ValueError
            except ValueError:
                print('Неправильный формат ответа.')
            else:
                break
        return self._users[answer - 1]

    @_log(second_message='Вход успешно выполнен.')
    def log_in(self) -> None:
        """
        Авторизация на сайте и сохранение полученной информации
        о пользователе в _chosen_user.
        """
        if self._chosen_user is None:
            while True:
                try:
                    email = input('Введите почту: ')
                    password = getpass('Введите пароль: ')
                    self._parser.log_in(email, password)
                except AuthorizationError as err:
                    print(err)
                else:
                    print('Парсинг данных...')
                    self._chosen_user = self._parser.parse()
                    print('Парсинг успешно завершен.')
                    break
        else:
            self._parser.log_in(self._chosen_user.email, self._chosen_user.password)

    @_log(second_message='Данные успешно сохранены в БД')
    def save_in_bd(self) -> None:
        """Сохранение пользовательских данных в БД."""
        super().save_in_bd()

    @_log(second_message='Данные успешно сохранены в ./parser_result.txt')
    def save_to_file(self) -> None:
        """Сохранение пользовательских данных в файл."""
        super().save_to_file()

    @_log('Парсинг данных...', 'Парсинг успешно завершен')
    def update_data(self) -> User:
        """
        Повторный парсинг сайта и сохранение полученной информации
        в _chosen_user.
        """
        super().update_data()

    def _print_data(self) -> None:
        """
        Вывод пользовательских данных на экран.
        """
        print(self._chosen_user)

    def run(self) -> None:
        """Запуск приложения."""
        if self._users:
            self._chosen_user = self._choose_user()
        self.log_in()

        options = [
            self._print_data,
            self.update_data,
            self.save_in_bd,
            self.save_to_file,
        ]

        while True:
            try:
                option = int(input((
                'Выберите действие:\n'
                '1) Вывести данные на экран\n'
                '2) Обновить данные\n'
                '3) Сохранить данные в БД\n'
                '4) Сохранить данные в файл\n'
                '0) Выйти из приложения\n'
            )))
                if option < 0 or option > 4:
                    raise ValueError
                elif option == 0:
                    break
                else:
                    options[option-1]()
            except ValueError:
                print('Неправильный формат ответа.')
