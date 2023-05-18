import customtkinter as ctk
from functools import wraps
from tkinter import NORMAL, DISABLED
from app.db import DBTool
from app.parser import SiriustParser, AuthorizationError
from app.base_app import BaseApp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class GuiApp(BaseApp):
    """
    Реализация утилиты как приложение с графическим интерфейсом.
    """
    def __init__(self, db: DBTool, parser: SiriustParser) -> None:
        """
        Инициализация экземпляра класса.

        Args:
            db: DBTool - объект, реализующий взаимодействие с БД.
            parser: SiriustParser - парсер сайта.
        """
        super().__init__(db, parser)
        self._main_window = ctk.CTk()
        self._main_window.geometry('800x400')
        self.timer_id = None

        self._login_frame = ctk.CTkFrame(self._main_window)

        ctk.CTkLabel(master=self._login_frame, text='Авторизация на siriust').pack(pady=12,padx=10)

        self._email_entry = ctk.CTkEntry(master=self._login_frame, placeholder_text="Почта")
        self._email_entry.pack(pady=12,padx=10)

        self._password_entry = ctk.CTkEntry(master=self._login_frame,
                                            placeholder_text="Пароль",
                                            show="*")
        self._password_entry.pack(pady=12,padx=10)

        ctk.CTkButton(master=self._login_frame,text='Войти', command=self.log_in).pack(pady=12,padx=10)

        self._remember = ctk.CTkCheckBox(master=self._login_frame,text='Запомнить')
        self._remember.pack(pady=12, padx=10)

        self._remember.pack(pady=12, padx=10)
        self._users = {u.email: u for u in self.load_users()}
        self._user_option_menu = ctk.CTkOptionMenu(self._login_frame,
                        values=list(self._users.keys()),
                        width=300,
                        height=30,
                        command=self._fill_login_fields)
        
        ctk.CTkCheckBox(master=self._login_frame,
                    text='Выбрать пользователя из списка',
                    command=self._toggle_user_choice_visability,
                    state=NORMAL if self._users else DISABLED).pack(pady=12,padx=10)

        self._main_frame = ctk.CTkFrame(self._main_window)
        self._tabview = ctk.CTkTabview(self._main_frame, 750, 350)
        user_tab = self._tabview.add('Пользователь')
        favorite_tab = self._tabview.add('Избранное')
        tools_tab = self._tabview.add('Инструменты')
        self._tabview.pack(padx=10, pady=10)

        user_tab.grid_anchor('n')
        LabelWithBg(user_tab, 'Почта:').grid(row=0, column=0, padx=10, pady=10, sticky='ew')
        LabelWithBg(user_tab, text='Имя:').grid(row=1, column=0, padx=10, pady=10, sticky='ew')
        LabelWithBg(user_tab, text='Фамилия:').grid(row=2, column=0, padx=10, pady=10, sticky='ew')
        LabelWithBg(user_tab, text='Город:').grid(row=3, column=0, padx=10, pady=10, sticky='ew')
        self._email_label= LabelWithBg(user_tab, text='')
        self._email_label.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        self._first_name_label = LabelWithBg(user_tab, text='')
        self._first_name_label.grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        self._last_name_label = LabelWithBg(user_tab, text='')
        self._last_name_label.grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        self._city_label = LabelWithBg(user_tab, text='')
        self._city_label.grid(row=3, column=1, padx=10, pady=10, sticky='ew')
        ctk.CTkButton(user_tab, text='Скопировать данные в буффер обмена',
                      command=lambda:self._main_window.clipboard_append(str(self._chosen_user))
                      ).grid(row=4, column=0, padx=10, pady=20, columnspan = 2, sticky='we')

        self._scrollable_frame = ctk.CTkScrollableFrame(favorite_tab, 700, 300)

        ctk.CTkButton(tools_tab, text='Сохранить данные в БД', command=self.save_in_bd).pack(pady=10, side='top', fill='x')
        ctk.CTkButton(tools_tab, text='Сохранить данные в Файл', command=self.save_to_file).pack(pady=10, side='top', fill='x')
        ctk.CTkButton(tools_tab, text='Обновить данные', command=self.update_data).pack(pady=10, side='top', fill='x')
        ctk.CTkButton(tools_tab, text='Сменить пользователя', command=self._show_login_frame, fg_color='maroon').pack(pady=10, side='bottom', fill='x')

    def _log(message: str, title: str):
        """
        Декоратор для логирования выполнения метода, путем
        отрисовки окна с указанными сообщением и заголовком.

        Args:
            message: str - сообщение для отображение.
            title: str - заголовок окна.
        """
        def first_wrapper(method):
            @wraps(method)
            def second_wrapper(self, *args):
                method(self, *args)
                GuiApp.show_message(message, title)
                return method
            return second_wrapper
        return first_wrapper

    def _loading():
        """
        Декоратор, отражающий процесс выполнение метода путем
        изменения иконки курсора, пока метод не будет выполнен.
        """
        def first_wrapper(method):
            @wraps(method)
            def second_wrapper(self, *args):
                self._main_window.configure(cursor='exchange')
                self._main_window.update()
                method(self, *args)
                self._main_window.configure(cursor='')
                self._main_window.update()
                return method
            return second_wrapper
        return first_wrapper

    def _toggle_remember_activity(self) -> None:
        """
        Меняет активность кнопки запоминания входа в
        зависимости от того, выбрал ли пользоваель уже
        сохраненные данные из БД или нет.
        """
        if self._remember._state == NORMAL:
            self._remember.configure(state = DISABLED)
            self._remember.deselect()
        else:
            self._remember.configure(state = NORMAL)

    def _toggle_user_choice_visability(self) -> None:
        """
        Меняет видимость OptionMenu с выбором сохраненных
        пользовательских данных.
        """
        if self._user_option_menu.winfo_ismapped():
            self._user_option_menu.pack_forget()
            self._chosen_user = None
        else:
            self._fill_login_fields()
            self._user_option_menu.pack(pady=12,padx=10)
        self._toggle_remember_activity()


    def _fill_login_fields(self, event = None) -> None:
        """
        Заполняет поля для ввода почты и пароля данными, полученными
        из БД.
        """
        self._chosen_user = self._users[self._user_option_menu.get()]

        self._email_entry.delete(0, ctk.END)
        self._email_entry.insert(0, self._chosen_user.email)

        self._password_entry.delete(0, ctk.END)
        self._password_entry.insert(0, self._chosen_user.password)

    def _fill_main_frame(self) -> None:
        """
        Заполняет основную страницу программы текущими пользовательскими
        данными.
        """
        self._email_label.configure(text=self._chosen_user.email)
        self._first_name_label.configure(text=self._chosen_user.first_name)
        self._last_name_label.configure(text=self._chosen_user.last_name)
        self._city_label.configure(text=self._chosen_user.city)

        self._items = {item.name: item for item in self._chosen_user.favorite_items}
        for child in self._scrollable_frame.winfo_children():
            child.destroy()
        for item in self._items:
            ArgumentSendButton(self._scrollable_frame,
                          text=item,
                          font=ctk.CTkFont(size=12),
                          fg_color=("gray70", "gray30"),
                          command=self._show_item_info,
                          arg=item).pack()
        self._scrollable_frame.pack()

    def _show_item_info(self, item_name: str) -> None:
        """
        Отрисовывает окно с информацией о выбранном товаре.
        """
        item = self._items[item_name]
        window = ctk.CTkToplevel()
        window.title('Информация о выбранном товаре')
        window.geometry('800x600')
        window.grid_anchor('n')

        LabelWithBg(window, text='Название:',font=ctk.CTkFont(size=12)).grid(row=0, column=0, pady=10, sticky='ew')
        LabelWithBg(window, text='Розничная цена:',font=ctk.CTkFont(size=12)).grid(row=1, column=0, pady=10, sticky='ew')
        LabelWithBg(window, text='Оптовая цена:',font=ctk.CTkFont(size=12)).grid(row=2, column=0, pady=10, sticky='ew')
        LabelWithBg(window, text='Рейтинг:',font=ctk.CTkFont(size=12)).grid(row=3, column=0, pady=10, sticky='ew')
        LabelWithBg(window, text='Количество отзывов:',font=ctk.CTkFont(size=12)).grid(row=4, column=0, pady=10, sticky='ew')
        LabelWithBg(window, text='Количество магазин, в которых данный товар в наличии:',font=ctk.CTkFont(size=12)).grid(row=5, column=0, pady=10, sticky='ew')
        LabelWithBg(window, text='Отзывы:',font=ctk.CTkFont(size=12)).grid(row=6, column=0, pady=10, sticky='ew', columnspan=2)
        LabelWithBg(window, text=item.name,font=ctk.CTkFont(size=12)).grid(row=0, column=1, pady=10, sticky='ew')
        LabelWithBg(window, text=item.retail_price,font=ctk.CTkFont(size=12)).grid(row=1, column=1, pady=10, sticky='ew')
        LabelWithBg(window, text=item.wholesale_price,font=ctk.CTkFont(size=12)).grid(row=2, column=1, pady=10, sticky='ew')
        LabelWithBg(window, text=f'{item.rating}/5',font=ctk.CTkFont(size=12)).grid(row=3, column=1, pady=10, sticky='ew')
        LabelWithBg(window, text=str(len(item.reviews)),font=ctk.CTkFont(size=12)).grid(row=4, column=1, pady=10, sticky='ew')
        LabelWithBg(window, text=item.number_of_stores,font=ctk.CTkFont(size=12)).grid(row=5, column=1, pady=10, sticky='ew')

        reviews = ctk.CTkTextbox(window)
        reviews.insert('0.0', '\n---\n'.join(str(review) for review in item.reviews))
        reviews.grid(row=7, column=0, pady=10, sticky='ew', columnspan=2)

        ArgumentSendButton(window,
                           text='Сохранить товар в файл',
                           font=ctk.CTkFont(size=12),
                           arg=item.name,
                           command=self._save_item_to_file)\
                            .grid(row=8, column=0, pady=10, sticky='ew', columnspan=2)

    def _save_item_to_file(self, item_name: str) -> None:
        """Сохранение товара в файл."""
        item = self._items[item_name]
        file_name = item_name+'.txt'
        with open(file_name, 'w') as f:
            f.write(str(item))
        GuiApp.show_message(f'Файл успешно сохранен в ./{file_name}', 'Сохранение файла')

    @_log('Успешно сохранено в ./parser_result.txt', 'Сохранение в файл')
    def save_to_file(self) -> None:
        """Сохранение пользовательских данных в файл."""
        super().save_to_file()

    @_log('Успешно сохранено в БД', 'Сохранение в БД')
    def save_in_bd(self) -> None:
        """Сохранение пользовательских данных в БД."""
        super().save_in_bd()

    @_loading()
    @_log('Парсинг успешно завершен', 'Обновление данных')
    def update_data(self) -> None:
        """
        Повторный парсинг сайта и сохранение полученной информации
        в _chosen_user, после чего основная страница программы заново
        заполняется данными.
        """
        super().update_data()
        self._fill_main_frame()

    @_loading()
    def log_in(self) -> None:
        """
        Авторизация на сайте и сохранение полученной информации
        о пользователе в _chosen_user, после чего основная страница
        приложения заполняется данными и отображается.
        """
        email = self._email_entry.get()
        password = self._password_entry.get()
        remember = self._remember.get()

        if self._chosen_user is None:
            try:
                self._parser.log_in(email, password)
            except AuthorizationError as err:
                GuiApp.show_message(err, 'Ошибка авторизации')
            else:
                self._chosen_user = self._parser.parse()
                if remember:
                    self._db.add_or_update_user(self._chosen_user)
        else:
            self._parser.log_in(self._chosen_user.email, self._chosen_user.password)
        self._fill_main_frame()
        self._show_main_frame()

    @staticmethod
    def show_message(message: str, title: str) -> None:
        """
        Отрисовка окна с указанными сообщением и заголовком.

        Args:
            message: str - сообщение для отображение.
            title: str - заголовок окна.
        """
        window = ctk.CTkToplevel()
        window.title(title)
        window.geometry('600x150')
        ctk.CTkLabel(window, text=message).place(relx=0.5, rely=0.5, anchor='center')

    def _show_login_frame(self) -> None:
        """Отображает страницу авторизации."""
        self._chosen_user = None
        self._login_frame.pack(pady=20,padx=40,fill='both',expand=True)
        self._main_frame.pack_forget()

    def _show_main_frame(self) -> None:
        """Отображает основную страницу."""
        self._login_frame.pack_forget()
        self._main_frame.pack(pady=20,padx=40,fill='both',expand=True)

    def run(self) -> None:
        """Запуск приложения."""
        self._show_login_frame()
        self._main_window.mainloop()


class LabelWithBg(ctk.CTkLabel):
    """Класс текстовой метки с серым фоном."""
    def __init__(self, master, text: str, font: ctk.CTkFont = None) -> None:
        super().__init__(master,
                         text=text,
                         fg_color=("gray70", "gray30"),
                         corner_radius=7,
                         font=font if font is not None else ctk.CTkFont(size=20))


class ArgumentSendButton(ctk.CTkButton):
    """
    Класс кнопки, которая при вызове назначенной на
    нее функции, передает в эту функцию указанный при 
    инициализации аргумент.    """
    def __init__(self, master, text, command, font, arg, fg_color = None):
        super().__init__(master,
                         text=text,
                         fg_color=fg_color if fg_color is None else ("gray70", "gray30"),
                         font=font,
                         command=command)
        self._arg = arg

    def _clicked(self, event=None):
        if self._state != DISABLED:
            self._on_leave()
            self._click_animation_running = True
            self.after(100, self._click_animation)

            if self._command is not None:
                self._command(self._arg)