import argparse
import os
import sys
import json
from time import sleep
from urllib.parse import unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


BASE_URL = 'https://tululu.org'
SCIENCE_FICTION_URL = 'https://tululu.org/l55/'
IMAGES_DIR = 'images/'
BOOKS_DIR = 'books/'


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError('An unexpected redirect occurred')


def make_get_request(url, params={}):
    response = requests.get(url, params=params)
    response.raise_for_status()

    check_for_redirect(response)

    return response


def create_dir(relative_path):
    dir_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        relative_path,
    )

    os.makedirs(dir_path, exist_ok=True)

    return dir_path


def download_txt(url, filename, url_params={}, folder='books/'):
    response = make_get_request(url, url_params)

    dir_path = create_dir(folder)
    filepath = os.path.join(dir_path, f'{sanitize_filename(filename)}')

    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(response.text)

    return filepath


def download_image(url, filename, url_params={}, folder='images/'):
    response = make_get_request(url, url_params)

    dir_path = create_dir(folder)
    filepath = os.path.join(dir_path, f'{sanitize_filename(filename)}')

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return filepath


def parse_book_urls(page, page_url):
    soup = BeautifulSoup(page, 'lxml')
    main_content = soup.select_one('#content')

    book_cards = main_content.select('table.d_book')
    book_urls = []
    for book_card in book_cards:
        book_path = book_card.select_one('.bookimage a')['href']
        book_url = urljoin(page_url, book_path)
        book_urls.append(book_url)
    return book_urls


def parse_book_page(page, book_page_url):
    soup = BeautifulSoup(page, 'lxml')
    main_content = soup.select_one('#content')

    image_url = urljoin(
        book_page_url,
        main_content.select_one('.bookimage img')['src']
    )

    download_url = urljoin(
        book_page_url,
        main_content.find('a', text='сохранить txt')
    )

    title, author = list(
        map(
            lambda part_of_name: part_of_name.strip(),
            main_content.select_one('h1').text.split('::'),
        )
    )
    comments = list(
        map(
            lambda comment: comment.select_one('.black').text,
            main_content.select('.texts'),
        ),
    )
    genres = list(
        map(
            lambda genre: genre.text,
            main_content.select('span.d_book a')
        ),
    )

    return {
        'title': title,
        'author': author,
        'image_url': image_url,
        'comments': comments,
        'download_url': download_url,
        'genres': genres,
    }


def validate_args(start_page, end_page):
    if start_page <= 0:
        raise SystemExit('The start page must be greater than 0')
    elif end_page <= start_page:
        raise SystemExit('The end page must be greater than start page')


def init_parser():
    parser = argparse.ArgumentParser(
        description='The program allows you to download books \
            from https://tululu.org/\n'
    )
    parser.add_argument(
        'start_page',
        help='''
        The id of the book from which the download begins.\n
        This value must be greater than 0 and less than the id of the final
        book'
        ''',
        nargs='?',
        type=int,
        default=1,
    )
    parser.add_argument(
        'end_page',
        help='''
        The id of the book where the download ends. This value must be greater
        than the start book id
        ''',
        nargs='?',
        type=int,
        default=10,
    )
    return parser


def download_book_with_image(book_url):
    book_page_response = make_get_request(book_url)
    book = parse_book_page(book_page_response.text, book_url)
    filename = f'{book["title"]}.txt'
    # download_txt(book['download_url'], filename)

    image_url = book['image_url']
    image_filename = unquote(urlsplit(image_url).path.split('/')[-1])
    # download_image(image_url, image_filename)

    return {
        'title': book['title'],
        'author': book['author'],
        'img_src': f'{os.path.join(IMAGES_DIR, image_filename)}',
        'book_path': f'{os.path.join(BOOKS_DIR, filename)}',
        'comments':  book['comments'],
        'genres': book['genres']
    }


if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()
    start_page, end_page = args.start_page, args.end_page
    validate_args(start_page, end_page)

    start_page, end_page = args.start_page, args.end_page

    validate_args(start_page, end_page)

    connection_error_counter = 0

    book_urls = []
    current_page_number = start_page
    while current_page_number <= end_page:
        page_url = urljoin(SCIENCE_FICTION_URL, str(current_page_number))
        try:
            page_response = make_get_request(page_url)
        except requests.exceptions.HTTPError:
            print('PAGE ERROR')
            current_page_number += 1
            connection_error_counter = 0
            continue
        except requests.exceptions.ConnectionError:
            if connection_error_counter > 10:
                print(
                    'Internet connection problems. Please try again later',
                    file=sys.stderr,
                )
                break

            print(
                'Internet connection problems... Please wait...',
                file=sys.stderr,
            )
            sleep(5)
            connection_error_counter += 1

        connection_error_counter = 0
        current_page_number += 1
        book_urls.extend(parse_book_urls(page_response.text, page_url))
        # I sleep so I don't get banned by the server
        sleep(0.5)

    books = []
    current_books_url_index = 0
    while current_books_url_index < len(book_urls):
        book_url = book_urls[current_books_url_index]

        try:
            book = download_book_with_image(book_url)
        except requests.exceptions.HTTPError:
            current_books_url_index += 1
            connection_error_counter = 0
            continue
        except requests.exceptions.ConnectionError:
            if connection_error_counter > 10:
                print(
                    'Internet connection problems. Please try again later',
                    file=sys.stderr,
                )
                break

            print(
                'Internet connection problems... Please wait...',
                file=sys.stderr,
            )
            sleep(5)
            connection_error_counter += 1

        books.append(book)
        connection_error_counter = 0
        current_books_url_index += 1
        sleep(0.5)

    with open('books.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(books, jsonfile, ensure_ascii=False, indent=2)
