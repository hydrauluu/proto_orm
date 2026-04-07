import sqlite3
import copy
from fields import BaseFieldDescriptor


class Q:
    """
    Узел дерева условий.

    Пример:
       Q(age__gate=18)
       Q(age__gte=18) & Q(activate=True)
       Q(grade="L1") | Q(grade="L2")
       -Q(activate=True)
    """

    AND = "AND"
    OR = "OR"
    XOR = "XOR"

    default = AND
    connectors = (None, AND, OR, XOR)

    def __init__(self, *args, _connector=None, _negated=False, **kwargs):
        if _connector not in self.connectors:
            valid = ", ".join(repr(c) for c in self.connectors[1:])
            raise ValueError(f"_connector должен быть одним из: {valid}")

        self.children = [*args, *sorted(kwargs.items())]
        self.connector = _connector or self.default
        self.negated = _negated

    def _combine(self, other: "Q", conn: str) -> "Q":
        """ 
         Строит новый узел с коннектором conn и двумя детьми: self и other.

         - если один из операнд пустой, то возвращает копию другого.
         - иначе создает новый Q-узел и добавляет обоих как детей.
        """

        if not isinstance(other, Q):
            raise TypeError(f"Q можно комбинировать только с Q, а получили {type(other)}!")
        
        if not self.children:
            return other.copy()
        if not other.children:
            return other.copy()

        obj = Q(_connector=conn)
        obj.children = [self, other]
        return obj

    def __and__(self, other: "Q") -> "Q":
        """Q(a=1) & Q(b=2) -> AND-узел с двумя детьми"""
        return self._combine(other, self.AND)

    def __or__(self, other: "Q") -> "Q":
        """Q(a=1) | Q(b=2) -> OR-узел с 2 детьми"""
        return self._combine(other, self.OR)

    def __xor__(self, other: "Q") -> "Q":
        """Q(a=1) ^ Q(b=2) -> XOR-узел"""
        return self._combine(other, self.XOR)

    def __invert__(self) -> "Q":
        """-Q(a=1) ->  копия с negated=True"""
        obj = self.copy()
        obj.negated = not self.negated
        return obj

    def copy(self) -> "Q":
        return copy.copy(self)

    def negate(self) -> None:
        """Инвертирует флаг negated на месте"""
        self.negated = not self.negated


    @property
    def identity(self) -> tuple:
        """Уникальный идентификатор Q - кортеж из всех данных"""
        return (self.connector, self.negated, * self._hashable_children())

    def _hashable_children(self):
        for child in self.children:
            if isinstance(child, tuple):
                field, value = child
                yield (field, tuple(value) if isinstance(value, list) else value)
            else:
                yield child.identity

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Q):
            return NotImplemented
        return self.identity == other.identity

    def __hash__(self) -> int:
        return hash(self.identity)
    

    def __bool__(self) -> bool:
        return bool(self.children)

    def __repr__(self) -> str:
        neg = "-" if self.negated else ""
        kids = ", ".join(repr(c) for c in self.children)
        return f"{neg}Q[{self.connector}]({kids})"






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

    def __init__(self, model_class):
        self.model_class = model_class

    def select(self, *fields_name, chunk_sizes=2000):

        fields_format = ", ".join(fields_name)
        query = f"SELECT {fields_format} FROM {self.model_class.table_name}"

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

        fields_names = new_data.keys()
        place_holder_format = ", ".join(
            [f"{field_name} = ?" for field_name in fields_names]
        )
        query = f"UPDATE {self.model_class.table_name} SET {place_holder_format}"
        params = list(new_data.values())

        self._execute_query(query, params)
        self._commit()

    def delete(self):
        query = f"DELETE FROM {self.model_class.table_name}"

        cursor = self._get_cursor()
        cursor.execute(query)
        self._commit()


class MetaModel(type):
    manager_class = BaseManager

    """Метакласс, который перехватывает создание класса в run-time."""

    def __new__(cls, name, bases, attrs):

        fields = {
            key: value
            for key, value in attrs.items()
            if isinstance(value, BaseFieldDescriptor)
        }

        private_slots = [f"_{field_name}" for field_name in fields]
        attrs["__slots__"] = private_slots
        attrs["_fields"] = fields

        cls = super().__new__(cls, name, bases, attrs)

        return cls

    def _get_manager(cls):
        return cls.manager_class(model_class=cls)

    @property
    def objects(cls):
        return cls._get_manager()


class BaseModel(metaclass=MetaModel):
    """Базовая Модель, которая наследуется от метакласса и в которой устанавливается название таблицы."""

    table_name = ""
    manager_class = BaseManager

    def __init__(self, **row_data) -> None:
        for fields_name, value in row_data.items():
            setattr(self, fields_name, value)

    def __repr__(self) -> str:
        attr_format = ", ".join(
            [f"{field}={value}" for field, value in self.__dict__.items()]
        )
        return f"<{self.__class__.__name__}: ({attr_format})>"
