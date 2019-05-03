import os
from typing import Dict

from .database import Database
from ..errors import DatabaseNotFound
from ..table import PersistentTable
from ..utils.path import load_tables


class DiskDatabase(Database):

    def __init__(self, directory: str):
        self.tables: Dict[object, PersistentTable] = {}
        self.directory = directory
        if not os.path.exists(directory):
            os.mkdir(directory)
        if os.path.exists(directory):
            try:
                for table in load_tables(directory):
                    table = PersistentTable.from_file(table)
                    self.tables.update({table.table_type: table})
            except DatabaseNotFound:
                pass

    def __len__(self):
        return sum(len(table) for table in self.tables.values())

    def __repr__(self):
        return f"DiskDatabase(directory={self.directory})"

    def __iter__(self):
        return iter(self.tables.values())

    def insert(self, item: object) -> None:
        """Inserts an arbitrary Python object into the database. Do not use this
        database to store raw types."""
        cls = type(item)
        try:
            self.tables[cls].insert(item)
        except KeyError:
            self.tables.update(
                {cls: PersistentTable.new(os.path.join(self.directory, hex(abs(hash(cls)))),
                                          table_type=cls)})
            self.tables[cls].insert(item)

    def batch_insert(self, items: list) -> None:
        """Inserts a list of similar Python objects into the database."""
        if len(items) == 0:
            return
        else:
            first_item_type = type(items[0])
            if any((type(x) != first_item_type for x in items)):
                raise ValueError("Batch insert requires all elements to be of the same type!")
            try:
                self.tables[first_item_type].batch_insert(items)
            except KeyError:
                self.tables.update(
                    {first_item_type: PersistentTable.new(os.path.join(self.directory, hex(abs(hash(first_item_type)))),
                                                          table_type=first_item_type)})
                self.tables[first_item_type].batch_insert(items)

    def retrieve(self, cls, **kwargs):
        try:
            return self.tables[cls].retrieve(**kwargs)
        except KeyError:
            raise KeyError("No objects of this type were ever stored in this database!")

    def delete(self, cls, **kwargs):
        try:
            return self.tables[cls].delete(**kwargs)
        except KeyError:
            raise KeyError("No objects of this type were ever stored in this database!")
