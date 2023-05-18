import argparse
from app.db import DBTool
from app.parser import SiriustParser
from app.console_app import ConsoleApp
from app.gui_app import GuiApp


def main(args):
    db = DBTool()
    parser = SiriustParser()
    app = ConsoleApp(db, parser) if args.nogui else GuiApp(db, parser)
    app.run()


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Приложение для парсинга сайта siriust.ru',
                                         epilog=(
                                                'Приложение поддерживает работу как с графическим интерфейсом,'
                                                'так и без него.\n'
                                                'Установка зависимостей из noguirequirements.txt'
                                                ' позволяет запускать утилиту только с ключом --nogui.'
                                         ))
    arg_parser.add_argument('--nogui',
                            action='store_true',
                            help='Запуск приложения без графического интерфейса')
    args = arg_parser.parse_args()
    main(args)