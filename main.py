import argparse
import os
import time
from urllib.parse import unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


BASE_URL = 'https://tululu.org/'


def check_for_redirect(response):
    if 400 > response.status_code >= 300:
        raise requests.exceptions.HTTPError('An unexpected redirect occurred')


def request_get(url, allow_redirects=False):
    response = requests.get(url, allow_redirects=allow_redirects)
    response.raise_for_status()

    if not allow_redirects:
        check_for_redirect(response)

    return response


def create_dir(relative_path):
    dir_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        relative_path,
    )

    if os.path.exists(dir_path):
        return dir_path

    os.makedirs(dir_path)

    return dir_path


def download_txt(url, filename, folder='books/'):
    response = request_get(url)

    dir_path = create_dir(folder)
    filepath = os.path.join(dir_path, f'{sanitize_filename(filename)}')

    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(response.text)

    return filepath


def download_image(url, filename, folder='images/'):
    response = request_get(url)

    dir_path = create_dir(folder)
    filepath = os.path.join(dir_path, f'{sanitize_filename(filename)}')

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return filepath


def parse_book_page(page):
    soup = BeautifulSoup(page, 'lxml')
    main_content = soup.find('div', id='content')

    title_and_author = main_content.find('h1').text.split('::')
    image_url = urljoin(
        BASE_URL,
        main_content.find('div', class_='bookimage').find('img')['src'],
    )
    comments = list(
        map(
            lambda comment: comment.find('span', class_='black').text,
            main_content.find_all('div', class_='texts'),
        ),
    )
    genres = list(
        map(
            lambda genre: genre.text,
            main_content.find('span', class_='d_book').find_all('a'),
        ),
    )

    return {
        'title': title_and_author[0].strip(),
        'author': title_and_author[1].strip(),
        'image_url': image_url,
        'comments': comments,
        'genres': genres,
    }


def print_book_info(title, author):
    print(f'Название: {title}\nАвтор: {author}\n\n')


def validate_args(start_id, end_id):
    if start_id <= 0:
        raise SystemExit('The start book id must be greater than 0')
    elif end_id <= start_id:
        raise SystemExit('The end book id must be greater than start book id')


def init_parser():
    parser = argparse.ArgumentParser(
        description='The program allows you to download books \
            from https://tululu.org/\n'
    )
    parser.add_argument(
        'start_id',
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
        'end_id',
        help='''
        The id of the book where the download ends. This value must be greater
        than the start book id
        ''',
        nargs='?',
        type=int,
        default=10,
    )
    return parser


if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()
    start_book_id, end_book_id = args.start_id, args.end_id

    validate_args(start_book_id, end_book_id)

    for current_book_id in range(start_book_id, end_book_id + 1):
        download_book_url = f'{BASE_URL}txt.php?id={current_book_id}'
        book_page_url = f'{BASE_URL}b{current_book_id}/'

        try:
            book_page_response = request_get(book_page_url)
        except requests.exceptions.HTTPError:
            continue

        time.sleep(0.5)

        book_info = parse_book_page(book_page_response.text)

        filename = f'{current_book_id}. {book_info["title"]}.txt'
        try:
            download_txt(download_book_url, filename)
        except requests.exceptions.HTTPError:
            continue

        image_url = book_info['image_url']
        image_filename = unquote(urlsplit(image_url).path.split('/')[-1])
        try:
            download_image(image_url, image_filename)
        except requests.exceptions.HTTPError:
            print(f'Не удалось загружить изображения для {book_info["title"]}')
            continue

        print_book_info(book_info['title'], book_info['author'])
