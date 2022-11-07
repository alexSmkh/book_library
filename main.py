from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, unquote
from pathvalidate import sanitize_filename

import requests
import time

import os

BASE_BOOKS_URL = 'https://tululu.org/'


def check_for_redirect(response):
    if 400 > response.status_code >= 300:
        raise requests.exceptions.HTTPError('An unexpected redirect occurred')


def request_get(url, allow_redirects=True):
    response = requests.get(url, allow_redirects=allow_redirects)
    response.raise_for_status()

    if not allow_redirects:
        check_for_redirect(response)

    return response


def write_file(filepath, raw_data):
    with open(filepath, 'wb') as file:
        file.write(raw_data)


def create_dir(dir_path):
    dir_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        *dir_path,
    )

    if os.path.exists(dir_path):
        return dir_path

    os.makedirs(dir_path)

    return dir_path


def download_file(file_url, directory, filename):
    try:
        response = request_get(file_url, False)
    except requests.exceptions.HTTPError:
        return None

    dir_path = create_dir(directory)
    filepath = os.path.join(dir_path, f'{sanitize_filename(filename)}')

    write_file(filepath, response.content)

    return filepath


def download_image(image_url):
    filename = unquote(urlsplit(image_url).path.split('/')[-1])
    return download_file(image_url, ['books', 'images'], filename)


def download_txt(url, filename, folder='books'):
    return download_file(url, [folder], f'{filename}.txt')


def parse_book_page(page):
    soup = BeautifulSoup(page, 'lxml')
    main_content = soup.find('div', id='content')

    title_and_author = main_content.find('h1').text.split('::')
    image_url = urljoin(
        BASE_BOOKS_URL,
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


def fetch_book_info(book_page_url):
    try:
        response = request_get(book_page_url, False)
    except requests.exceptions.HTTPError:
        return None

    return parse_book_page(response.text)


def download_books():
    book_counter = 0
    book_id = 1

    while book_counter < 10:
        book_url = f'{BASE_BOOKS_URL}txt.php?id={book_id}'
        book_main_page_url = f'{BASE_BOOKS_URL}b{book_id}/'
        book_info = fetch_book_info(book_main_page_url)
        time.sleep(1)

        if not book_info:
            book_id += 1
            continue

        filename = f'{book_id}. {book_info["title"]}'
        book_filepath = download_txt(book_url, filename)
        download_image(book_info['image_url'])

        if book_filepath:
            book_counter += 1

        print(f'Заголовок: {book_info["title"]}')
        print(f'Жанры: {book_info["genres"]}')
        print(f'Комментарии: {book_info["comments"]}\n\n')

        book_id += 1


if __name__ == '__main__':
    download_books()
