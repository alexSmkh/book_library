import argparse
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape


def init_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--books_path',
        help='Path to json file containing info about books',
        nargs='?',
        type=str,
        default='books.json'
    )
    return parser


def on_reload(books):
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html'])
    )

    template = env.get_template('template.html')
    rendered_page = template.render(books=books)

    with open('index.html', 'w', encoding='utf8') as file:
        file.write(rendered_page)


def main():
    parser = init_parser()
    args = parser.parse_args()
    books_path = args.books_path

    with open(books_path) as file:
        books = json.load(file)

    on_reload(books)


if __name__ == '__main__':
    main()
