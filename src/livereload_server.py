import os

from livereload import Server, shell

if __name__ == '__main__':
    server = Server()
    server.watch(
        os.path.join('src', 'templates', 'template.html'),
        shell('poetry run python3 src/render_website.py', cwd='.')
    )
    server.serve(root='.')
