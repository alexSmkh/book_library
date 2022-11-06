import requests
import os


def write_file(filepath, raw_data):
    with open(filepath, 'wb') as file:
        file.write(raw_data)


def create_dir(*args):
    dir_path = os.path.join(os.getcwd(), *args)

    if os.path.exists(dir_path):
        return dir_path

    os.makedirs(dir_path)

    return dir_path


def check_for_redirect(response):
    if 400 > response.status_code >= 300:
        raise requests.exceptions.HTTPError('An unexpected redirect occurred')


def download_book(book_id):
    url = f'https://tululu.org/txt.php?id={book_id}'

    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()

    try:
        check_for_redirect(response)
    except requests.exceptions.HTTPError:
        return None

    return response.content


def download_books(download_dir):
    book_counter = 0
    book_id = 1

    while book_counter < 10:
        book = download_book(book_id)

        if book:
            write_file(os.path.join(download_dir, f'book_{book_id}.txt'), book)
            book_counter += 1

        book_id += 1


if __name__ == '__main__':
    dir_path = create_dir('books')
    download_books(dir_path)
