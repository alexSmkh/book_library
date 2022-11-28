# Book library
## A parser that allows you to download books from https://tululu.org/

![Demo](demo.gif)


### **What you need**
* Python >= 3.10
* [Poetry](https://python-poetry.org/docs/)

### **How to install**
```
poetry install
```

### **How to run**
```
poetry run python3 main.py [-h] [options]
```

* `start_id` - id of the book from which the download begins. This value must be greater than 0 and less than the id of the final book. `Default = 1`
* `end_id` - id of the book where the download ends. This value must be greater than the start book id. `Default = last page in the category`
* `skip_imgs` - don't download the book covers
* `skip_txt` - don't download the books
* `dest_folder` - the path to the directory with parsing results: covers, books, JSON.
* `json_path` - the path to the file with information about books
