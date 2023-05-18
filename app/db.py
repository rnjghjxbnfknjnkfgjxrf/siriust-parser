from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from app.entities import Base, User

class DBTool:
    """Класс, реализующий взаимодействие с БД."""
    __slots__ = ('_session')

    def __init__(self) -> None:
        """Инициализация объекта класса."""
        engine = create_engine('sqlite:///app.db')
        engine.connect()

        Session = sessionmaker()
        Session.configure(bind=engine)
        self._session = Session()

        Base.metadata.create_all(engine)
        self._session.execute(text('PRAGMA foreign_keys = ON;'))
        self._session.commit()

    def add_or_update_user(self, user: User) -> None:
        """
        Добавляет пользователя в БД или обновляет
        имеющиеся о нем данные.

        Args:
            user: User - пользователь, для добавления/
                         обновления в БД.
        """
        old_user_data = self._session.query(User).filter_by(email=user.email).first()
        if old_user_data:
            self._update_user(user, old_user_data)
        else:
            self._session.add(user)
            self._session.commit()

    def get_users(self) -> list[User]:
        """
        Получение списка всех пользовательских данных.

        Returns:
            Список объектов класса User.
        """
        return self._session.query(User).all()

    def _update_user(self, new_user_data: User, old_user_data: User) -> None:
        """
        Обновление данных о пользователе.

        Args:
            new_user_data: User - новые пользовательские данные.
            old_user_data: User - данные, которые нужно обновить.
        """
        old_user_data.copy_attrs(new_user_data)
        self._session.commit()
        self._session.execute(text((
            'DELETE FROM Items '
            'WHERE id NOT IN (SELECT item_id FROM user_to_item);'
        )))
        self._session.commit()
