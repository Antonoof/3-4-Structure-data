import json
from collections import defaultdict
from sortedcontainers import SortedDict


class Library:
    def __init__(self):
        self.books = []
        self.title_map = {}
        self.author_map = defaultdict(list)
        self.genre_map = defaultdict(list)
        self.author_genre_map = defaultdict(SortedDict)

    def add_book(self, title, author, genre, copies=1):
        book = (title, author, genre, copies)
        self.books.append(book)

        self.title_map[title] = book
        self.author_map[author].append(book)
        self.genre_map[genre].append(book)

        if genre not in self.author_genre_map[author]:
            self.author_genre_map[author][genre] = []
        self.author_genre_map[author][genre].append(book)

    def remove_book(self, title):
        book = self.title_map.get(title)
        if book:
            self.books.remove(book)
            self.author_map[book[1]].remove(book)
            self.genre_map[book[2]].remove(book)
            self.author_genre_map[book[1]][book[2]].remove(book)

            del self.title_map[title]
            if not self.author_map[book[1]]:
                del self.author_map[book[1]]
            if not self.genre_map[book[2]]:
                del self.genre_map[book[2]]
            if not self.author_genre_map[book[1]][book[2]]:
                del self.author_genre_map[book[1]][book[2]]

    def borrow_book(self, title):
        book = self.title_map.get(title)
        if book and book[3] > 0:
            new_book = (book[0], book[1], book[2], book[3] - 1)
            self.books[self.books.index(book)] = new_book
            self.title_map[title] = new_book

            self.author_map[book[1]][self.author_map[book[1]].index(book)] = (
                new_book
            )
            self.genre_map[book[2]][self.genre_map[book[2]].index(book)] = (
                new_book
            )
            self.author_genre_map[book[1]][book[2]][
                self.author_genre_map[book[1]][book[2]].index(book)
            ] = new_book
            return new_book
        else:
            return None

    def search_book(self, **kwargs):
        if len(kwargs) == 1:
            key, value = next(iter(kwargs.items()))
            if key == "title":
                return [self.title_map.get(value)]
            elif key == "author":
                return self.author_map.get(value, [])
            elif key == "genre":
                return self.genre_map.get(value, [])
        elif len(kwargs) == 2:
            if "author" in kwargs and "genre" in kwargs:
                author = kwargs["author"]
                genre = kwargs["genre"]
                author_books = set(self.author_map.get(author, []))
                genre_books = set(self.genre_map.get(genre, []))
                return list(author_books.intersection(genre_books))
        return []

    def list_books(self):
        return self.books

    def analyze_data(self):
        popular_author = max(
            self.author_map, key=lambda author: len(self.author_map[author])
        )
        popular_genre = max(
            self.genre_map, key=lambda genre: len(self.genre_map[genre])
        )
        max_copies_book = max(self.books, key=lambda book: book[3])
        min_copies_book = min(self.books, key=lambda book: book[3])

        return {
            "Популярный автор": popular_author,
            "Популярный жанр": popular_genre,
            "Максимальное количество копий": max_copies_book,
            "Минимальное количество копий": min_copies_book,
        }

    def save_to_file(self, filename):
        with open(filename, "w") as file:
            json.dump(self.books, file)

    def load_from_file(self, filename):
        with open(filename, "r") as file:
            self.books = json.load(file)
            self.title_map = {}
            self.author_map = defaultdict(list)
            self.genre_map = defaultdict(list)
            self.author_genre_map = defaultdict(SortedDict)
            for book in self.books:
                self.title_map[book[0]] = book
                self.author_map[book[1]].append(book)
                self.genre_map[book[2]].append(book)
                if book[2] not in self.author_genre_map[book[1]]:
                    self.author_genre_map[book[1]][book[2]] = []
                self.author_genre_map[book[1]][book[2]].append(book)


library = Library()
library.add_book("Война и мир", "Толстой", "Роман", 4)
library.add_book("Преступление и наказание", "Достоевский", "Роман")

print(library.borrow_book("Война и мир"))
print(library.search_book(author="Толстой"))
print(library.search_book(author="Толстой", genre="Роман"))
print(library.analyze_data())

library.save_to_file("library.json")
library.load_from_file("library.json")
