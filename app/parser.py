import requests
from bs4 import BeautifulSoup
from app.entities import Item, User, Review

class SiriustParser:
    """
    Класс парсера, разбирающего сайт siriust.ru.
    """
    __slots__ = ('_headers', '_session', '_password')

    def __init__(self, headers: dict = None) -> None:
        """
        Инициализация объекта класса.

        Args:
            headers: dict - заголовки отправляемых парсером
                            запросов.
        """
        if headers is None:
            headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'accept': '*/*'
            }
        self._headers = headers

    def _parse_item(self, url: str) -> Item:
        """
        Парсит страницу товара.

        Args:
            url: str - ссылка на страницу товара.

        Returns:
            Объект класса Item с данными, полученными в ходе парсинга
            страница товара.
        """
        response = self._session.get(url)
        html = BeautifulSoup(response.content, 'html.parser')

        name_tag = html.find('h1', class_='ty-product-block-title')
        prices_tags = html.find('div', class_='col')\
                          .find_all('span', class_='ty-price-num', id=True)

        rating_tag = html.find('div', class_='ty-discussion__rating-wrapper')
        full_score_stars = rating_tag.find_all('i', class_='ty-stars__icon ty-icon-star')
        half_score_star = rating_tag.find('i', class_='ty-stars__icon ty-icon-star-half')

        review_tags = html.find_all('div', class_='ty-discussion-post__content ty-mb-l')
        reviews = []
        for review_tag in review_tags:
            reviews.append(
                Review(
                    author_name = review_tag.find('span', class_='ty-discussion-post__author').text,
                    score = len(review_tag.find_all('i', class_='ty-stars__icon ty-icon-star')),
                    text = review_tag.find('div', class_='ty-discussion-post__message').text
                )
            )

        list_of_stores = [x for x in html.find_all('div', class_='ty-product-feature')\
                            if 'отсутствует' not in x.find('div', class_='ty-product-feature__value').text]

        return Item(
            name = name_tag.text,
            retail_price = prices_tags[0].text,
            wholesale_price = prices_tags[1].text,
            rating = len(full_score_stars) + 0.5 if half_score_star else len(full_score_stars),
            number_of_stores = len(list_of_stores) - 1,
            reviews = reviews)

    def _get_favorite_items(self) -> list[Item]:
        """
        Получение списка избранных товаров пользователя.

        Returns:
            Список объектов класса Item.
        """
        response = self._session.get('https://siriust.ru/wishlist/', headers=self._headers)
        html = BeautifulSoup(response.content, 'html.parser')
        items = []
        for item in html.find_all('div', class_='ty-grid-list__item-name'):
            items.append(self._parse_item(item.a['href']))
        return items

    def log_in(self, email: str, password: str) -> None:
        """
        Авторизация на сайте и сохранение сессии.

        Args:
            email: str - электронная почта пользователя.
            password: str - пароль пользователя.

        Raises:
            AuthorizationError, если авторизация не
            завершилась успехом.
        """
        payload = {
            'user_login': email,
            'password': password,
            'return_url': 'index.php?dispatch=auth.login_form',
            'redirect_url': 'index.php?dispatch=auth.login_form',
            'dispatch[auth.login]':''
        }
        session = requests.Session()
        session.post('https://siriust.ru/', data=payload, headers=self._headers)
        if 'cp_email' not in session.cookies:
            raise AuthorizationError
        self._session = session
        self._password = password

    def parse(self) -> User:
        """
        Сбор пользовательских данных и их упаковка
        в объект класса User.

        Returns:
            Объект класса User с полученными данными.
        """
        response = self._session.get('https://siriust.ru/profiles-update/', headers=self._headers)
        html = BeautifulSoup(response.content, 'html.parser')

        email = html.find('input', {'name':'user_data[email]'})['value']
        name = html.find('input', {'name': 'user_data[s_firstname]'})['value']
        last_name = html.find('input', {'name':'user_data[s_lastname]'})['value']
        city = html.find('input', {'name': 'user_data[s_city]'})['value']

        return User(
            email=email,
            password= self._password,
            first_name=name,
            last_name=last_name,
            city=city,
            favorite_items=self._get_favorite_items()
        )

class AuthorizationError(Exception):
    """Исключение описывающее ошибку при авторизации."""
    def __init__(self) -> None:
        super().__init__('Не получилось авторизоваться.')
