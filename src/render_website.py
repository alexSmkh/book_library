import argparse
import json
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from more_itertools import chunked


SRC_PATH = Path(__file__).parent
PAGES_PATH = (SRC_PATH / os.path.join('..', 'pages')).resolve()
MEDIA_PATH = (SRC_PATH / os.path.join('..', 'media')).resolve()


def build_relative_path_to_file(path, from_path=PAGES_PATH):
    return os.path.relpath(path, from_path)


def init_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--books_path',
        help='Path to json file containing info about books',
        nargs='?',
        type=str,
        default=os.path.join(MEDIA_PATH, 'books.json')
    )
    return parser


def on_reload(books):
    env = Environment(
        loader=FileSystemLoader(os.path.join('src', 'templates')),
        autoescape=select_autoescape(['html'])
    )
    env.filters['build_relative_path_to_file'] = build_relative_path_to_file

    template = env.get_template('template.html')
    book_per_page = 10
    book_per_row = 2
    chunked_books_for_pages = list(chunked(books, book_per_page))
    page_count = len(chunked_books_for_pages)

    os.makedirs(PAGES_PATH, exist_ok=True)

    for page_number, books_for_current_page in enumerate(chunked_books_for_pages, start=1):
        chunked_books = list(chunked(books_for_current_page, book_per_row))
        rendered_page = template.render(
            chunked_books=chunked_books,
            previous_page=(page_number - 1 if page_number > 1 else None),
            next_page=(page_number + 1 if page_number < page_count else None),
            page_number=page_number,
            page_count=page_count
        )

        filename = f'index{page_number}.html'
        with open(os.path.join(PAGES_PATH, filename), 'w', encoding='utf8') as file:
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
