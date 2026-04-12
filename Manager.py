import sqlite3

from queryset import QuerySet


class BaseManager:
    """Точка входа: Model.objects — возвращает QuerySet."""

    connection = sqlite3.connect("my_database.db")

    def __init__(self, model_class):
        self.model_class = model_class

    def get_queryset(self) -> QuerySet:
        return QuerySet(self.model_class, self.connection)

    # -- Прокси на QuerySet --------------------------------------------------

    def all(self) -> QuerySet:
        return self.get_queryset()

    def filter(self, *args, **kwargs) -> QuerySet:
        return self.get_queryset().filter(*args, **kwargs)

    def exclude(self, *args, **kwargs) -> QuerySet:
        return self.get_queryset().exclude(*args, **kwargs)

    def order_by(self, *fields) -> QuerySet:
        return self.get_queryset().order_by(*fields)

    def first(self):
        return self.get_queryset().first()

    def count(self) -> int:
        return self.get_queryset().count()

    # -- Операции записи -----------------------------------------------------

    def bulk_insert(self, rows: list[dict]) -> None:
        if not rows:
            raise ValueError("Нельзя вставить пустой список строк")

        field_names   = list(rows[0].keys())
        fields_format = ", ".join(field_names)
        row_ph        = f"({', '.join(['?'] * len(field_names))})"
        values_format = ", ".join([row_ph] * len(rows))

        query  = (
            f"INSERT INTO {self.model_class.table_name} ({fields_format}) "
            f"VALUES {values_format}"
        )
        params = [v for row in rows for v in row.values()]

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()

    def select(self, *fields_name, chunk_sizes=2000) -> list:
        """Старый метод — оставлен для обратной совместимости."""
        fields_format = ", ".join(fields_name)
        query  = f"SELECT {fields_format} FROM {self.model_class.table_name}"
        cursor = self.connection.cursor()
        cursor.execute(query)

        result = []
        while True:
            rows = cursor.fetchmany(size=chunk_sizes)
            if not rows:
                break
            for row_values in rows:
                result.append(self.model_class(**dict(zip(fields_name, row_values))))
        return result
