import sqlite3


class BaseManager:
    """Создание базового Менеджера, в котором определен метод select и insert для выборки в БД.
    Далее будут определены оставшиеся методы."""

    connection = sqlite3.connect("my_database.db")

    @classmethod
    def _commit(cls):
        cls.connection.commit()

    @classmethod
    def _get_cursor(cls):
        return cls.connection.cursor()

    @classmethod
    def _execute_query(cls, query, params):
        cursor = cls._get_cursor()
        cursor.execute(query, params)

    def __init__(self, model_class) -> None:
        self.model_class = model_class

    def select(self, *fields_name, chunk_sizes=2000):
        # SELECT query
        fields_format = ", ".join(fields_name)
        query = f"SELECT {fields_format} FROM {self.model_class.table_name}"

        # Execute query
        cursor = self._get_cursor()
        cursor.execute(query)

        model_objects = list()
        is_fetching_completed = False
        while not is_fetching_completed:
            result = cursor.fetchmany(size=chunk_sizes)
            for row_values in result:
                keys, values = fields_name, row_values
                row_data = dict(zip(keys, values))
                model_objects.append(self.model_class(**row_data))
            is_fetching_completed = len(result) < chunk_sizes

        return model_objects

    def bulk_insert(self, rows: list[dict]):
        field_names = rows[0].keys()
        assert all(row.keys() == field_names for row in rows[1:])

        fields_format = ", ".join(field_names)
        values_placeholder_format = ", ".join(
            [f"({', '.join(['?'] * len(field_names))})"] * len(rows)
        )
        query = (
            f"INSERT INTO {self.model_class.table_name} ({fields_format}) "
            f"VALUES {values_placeholder_format}"
        )

        params = list()
        for row in rows:
            row_values = [row[field_name] for field_name in field_names]
            params += row_values

        self._execute_query(query, params)
        self._commit()

    def update(self, new_data: dict):
        pass

    def delete(self):
        pass


class MetaModel(type):
    """Метакласс, который перехватывает создание класса в run-time."""

    manager_class = BaseManager

    def _get_manager(cls):
        return cls.manager_class(model_class=cls)

    @property
    def objects(cls):
        return cls._get_manager()


class BaseModel(metaclass=MetaModel):
    """Базовая Модель, которая наследуется от метакласса и в которой устанавливается название таблицы."""

    table_name = ""

    def __init__(self, **row_data) -> None:
        for fields_name, value in row_data.items():
            setattr(self, fields_name, value)

    def __repr__(self) -> str:
        attr_format = ", ".join(
            [f"{field}={value}" for field, value in self.__dict__.items()]
        )
        return f"<{self.__class__.__name__}: ({attr_format})>"
