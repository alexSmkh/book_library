from livereload import Server, shell


if __name__ == '__main__':
    server = Server()
    server.watch(
        'template.html',
        shell('poetry run python3 render_website.py', cwd='.')
    )
    server.serve(root='.')
