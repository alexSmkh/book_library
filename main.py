from bs4 import BeautifulSoup
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


def create_dir(*args):
    dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    if os.path.exists(dir_path):
        return dir_path

    os.makedirs(dir_path)

    return dir_path


def download_txt(url, filename, folder='books/'):
    try:
        response = request_get(url, False)
    except requests.exceptions.HTTPError:
        return None

    dir_path = create_dir(folder)
    filepath = os.path.join(dir_path, f'{sanitize_filename(filename)}.txt')

    write_file(filepath, response.content)

    return filepath


def scrape_book_info(book_page_url):
    try:
        response = request_get(book_page_url, False)
    except requests.exceptions.HTTPError:
        return None

    soup = BeautifulSoup(response.text, 'lxml')
    title_and_author = soup.find('h1').text.split('::')

    return {
        'title': title_and_author[0].strip(),
        'author': title_and_author[1].strip(),
    }


def download_books():
    book_counter = 0
    book_id = 1

    while book_counter < 10:
        book_url = f'{BASE_BOOKS_URL}txt.php?id={book_id}'
        book_main_page_url = f'{BASE_BOOKS_URL}b{book_id}/'
        book_info = scrape_book_info(book_main_page_url)
        time.sleep(0.5)

        if not book_info:
            book_id += 1
            continue

        filename = f'{book_id}. {book_info["title"]}'
        book_filepath = download_txt(book_url, filename)

        if book_filepath:
            book_counter += 1

        book_id += 1


if __name__ == '__main__':
    download_books()
