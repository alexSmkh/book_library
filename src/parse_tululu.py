import argparse
import json
import logging
import os
import sys
from pathlib import Path
from time import sleep
from urllib.parse import unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from tqdm import tqdm

MEDIA_PATH = (Path(__file__).parent / os.path.join('..', 'media')).resolve()


logger = logging.getLogger(__file__)


def log_error(err):
    logging.error(err, exc_info=True)


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


def download_txt(url, dest_folder, filename, url_params={}):
    response = make_get_request(url, url_params)

    dir_path = create_dir(os.path.join(f'{dest_folder}', 'books'))
    filepath = os.path.join(dir_path, f'{sanitize_filename(filename)}')

    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(response.text)

    return os.path.relpath(filepath, '.')


def download_image(url, dest_folder, filename, url_params={}):
    response = make_get_request(url, url_params)

    dir_path = create_dir(os.path.join(f'{dest_folder}', 'images'))
    filepath = os.path.join(dir_path, f'{sanitize_filename(filename)}')

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return os.path.relpath(filepath, '.')


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

    download_tag = main_content.find('a', string='скачать txt')
    download_url = urljoin(book_page_url, download_tag.get('href')) if download_tag else ''

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
    elif end_page < start_page:
        raise SystemExit('The end page must be greater than start page')


def init_parser():
    parser = argparse.ArgumentParser(
        description='The program allows you to download books \
            from https://tululu.org/\n'
    )
    parser.add_argument(
        '--start_page',
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
        '--end_page',
        help='''
        The id of the book where the download ends. This value must be greater
        than the start book id
        ''',
        nargs='?',
        type=int
    )
    parser.add_argument(
        '--skip_imgs',
        help="Don't download book covers",
        action='store_true'
    )
    parser.add_argument(
        '--skip_txt',
        help="Don't download books",
        action='store_true'
    )
    parser.add_argument(
        '--json_path',
        help='Specify the path to the file with information about books',
        type=str,
        default=MEDIA_PATH
    )
    parser.add_argument(
        '--dest_folder',
        help='''
        Path to the directory with parsing results: pictures, books, JSON.
        ''',
        type=str,
        default=MEDIA_PATH
    )

    return parser


def download_book_with_image(book_url, dest_folder, skip_imgs, skip_txt):
    book_page_response = make_get_request(book_url)
    book = parse_book_page(book_page_response.text, book_url)
    filename = f'{book["title"]}.txt'
    result = {}

    if not skip_txt and book['download_url']:
        result['book_path'] = download_txt(book['download_url'], dest_folder, filename)

    image_url = book['image_url']
    image_filename = unquote(urlsplit(image_url).path.split('/')[-1])

    if not skip_imgs:
        result['img_src'] = download_image(image_url, dest_folder, image_filename)

    result.update({
        'title': book['title'],
        'author': book['author'],
        'comments':  book['comments'],
        'genres': book['genres']
    })

    return result


def parse_last_page_number(page):
    soup = BeautifulSoup(page, 'lxml')
    return int(soup.select('.npage')[-1].text)


def make_request_safely(request_func):
    connection_error_counter = 0
    while connection_error_counter < 10:
        try:
            return request_func()
        except requests.exceptions.HTTPError as err:
            log_error(err)
            return None
        except requests.exceptions.ConnectionError as err:
            if connection_error_counter >= 10:
                print(
                    'Internet connection problems. Please try again later',
                    file=sys.stderr,
                )
                log_error(err)
                sys.exit()

            log_error(err)
            print(
                'Internet connection problems... Please wait...',
                file=sys.stderr,
            )
            connection_error_counter += 1
            sleep(5)


def main():
    logging.basicConfig(filename='logs.log', filemode='w')

    parser = init_parser()
    args = parser.parse_args()
    start_page, end_page, skip_imgs, skip_txt, json_path, dest_folder = (
        args.start_page,
        args.end_page,
        args.skip_imgs,
        args.skip_txt,
        args.json_path,
        args.dest_folder
    )

    science_fiction_url = 'https://tululu.org/l55/'

    if not end_page:
        page_url = urljoin(science_fiction_url, str(start_page))
        page_response = make_request_safely(
            lambda: make_get_request(page_url)
        )
        end_page = parse_last_page_number(page_response.text)

    validate_args(start_page, end_page)

    book_urls = []
    downloaded_pages = 0
    pages = tqdm(range(start_page, end_page + 1))
    for current_page_number in pages:
        pages.set_description(f'Download {current_page_number} page')
        page_url = urljoin(science_fiction_url, str(current_page_number))
        page_response = make_request_safely(lambda: make_get_request(page_url))

        if not page_response:
            print(
                f'An error occurred while downloading the page {current_page_number}',
                file=sys.stdout
            )
            continue

        book_urls.extend(parse_book_urls(page_response.text, page_url))
        downloaded_pages += 1
        sleep(0.5)

    print(
        f'{downloaded_pages} of {end_page - start_page + 1} pages has been downloaded'
    )

    books = []
    tqdm_book_urls = tqdm(book_urls)
    downloaded_books = 0
    for book_url in tqdm_book_urls:
        book = make_request_safely(
            lambda: download_book_with_image(
                book_url,
                dest_folder,
                skip_imgs,
                skip_txt
            )
        )
        tqdm_book_urls.set_description(f'Download the "{book["title"]}" book')

        if not book:
            print(
                f'An error occurred while downloading the book: {book_url}',
                file=sys.stdout
            )
            continue

        books.append(book)
        downloaded_books += 1
        sleep(0.5)

    print(f'{downloaded_books} books has been downloaded')

    create_dir(json_path)
    with open(
        os.path.join(json_path, 'books.json'),
        'w',
        encoding='utf-8'
    ) as jsonfile:
        json.dump(books, jsonfile, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
