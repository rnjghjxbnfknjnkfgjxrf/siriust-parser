"""Описание сущностей и структуры БД."""
from sqlalchemy import Table, Column, Text, Integer, ForeignKey, REAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column


Base = declarative_base()

"""
Здесь реализовано отношение "многие-ко-многим" для
таблиц пользователей и избранных товаров, но по факту,
в текущей реализации приложения используется отношение
'один-ко-многим', так как товар с уникальным id относится
только к одному пользователю.
"""
user_to_item = Table(
    'user_to_item',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('Users.id', ondelete='CASCADE')),
    Column('item_id', Integer, ForeignKey('Items.id', ondelete='CASCADE'))
)

class Item(Base):
    """
    Класс, хранящий данные о товаре и описание
    соотетствующей таблицы в БД.
    """
    __tablename__ = 'Items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    retail_price = Column(Text, nullable=False)
    wholesale_price = Column(Text, nullable=False)
    rating = Column(REAL, nullable=False)
    number_of_stores = Column(Integer, nullable=False)
    reviews = relationship(
        'Review',
        passive_deletes=True
    )

    def __str__(self) -> str:
        s = (
        f"Название - {self.name}\n"
        f"Розничая цена - {self.retail_price}\n"
        f"Оптовая цена - {self.wholesale_price}\n"
        f"Рейтинг - {self.rating}/5\n"
        f"Количество магазин, в которых данный товар в наличии: {self.number_of_stores}\n"
        f"Количество отзывов: {len(self.reviews)}\n")
        if self.reviews:
            s += "Отзывы:\n"
            for review in self.reviews:
                s += f'[{str(review)}]\n'
        return s


class Review(Base):
    """
    Класс, хранящий данные о отзыве и описание
    соотетствующей таблицы в БД.
    """
    __tablename__ = 'Reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_name = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    item_id = mapped_column(ForeignKey('Items.id', ondelete='CASCADE'))

    def __str__(self) -> str:
        return (
            f'Автор: {self.author_name}\n'
            f'Оценка: {self.score}/5\n'
            f'Текст:\n{self.text}'
        )


class User(Base):
    """
    Класс, хранящий пользовательские данные и 
    описание соответствующей таблицы.
    """
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(Text, nullable=False, unique=True)
    password = Column(Text, nullable=False)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    city = Column(Text, nullable=False)
    favorite_items = relationship(
        'Item',
        secondary=user_to_item,
        passive_deletes=True
    )
    
    def copy_attrs(self, new_user_data) -> None:
        """
        Копирование атрибутов указанного объекта.

        Args:
            new_user_data: User - объект у которого копируются
                                  атрибуты.
        """
        self.email = new_user_data.email
        self.password = new_user_data.password
        self.first_name = new_user_data.first_name
        self.last_name = new_user_data.last_name
        self.city = new_user_data.city
        self.favorite_items = new_user_data.favorite_items

    def __str__(self) -> str:
        return (
            'Пользователь:\n\n'
            f"Фамилия: {self.last_name if self.last_name else 'не указана'}\n"
            f"Имя: {self.first_name if self.first_name else 'не указано'}\n"
            f'Почта: {self.email}\n'
            f"Город: {self.city if self.city else 'не указан'}\n\n"
            "Избранные товары:\n\n"
            
        ) + '\n'.join(str(item) for item in self.favorite_items)
