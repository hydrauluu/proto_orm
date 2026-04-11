import copy
from .Q import Q, build_order_by, build_where


class QuerySet:
    """Ленивый набор запросов. Не ходит в БД до момента итерации или вызова."""

    def __init__(self, model_class, connection):
        self.model_class = model_class
        self.connection = connection
        self._q: Q | None = None
        self._ordering: list[str] = []
        self._result_cahe = None

    def _clone(self) -> "QuerySet":
        qs = QuerySet(self.model_class, self.connection)
        qs._q = copy.copy(self._q)
        qs._ordering = self._ordering.copy()
        return qs

    def _add_q(self, q: Q) -> "QuerySet":
        qs = self._clone()
        qs._result_cahe = None
        qs._q = q if qs._q is None else qs._q & q
        return qs

    @staticmethod
    def _build_q(args, kwargs) -> Q:
        parts = list(args) + ([Q(**kwargs)] if kwargs else [])
        if not parts:
            raise ValueError("filter()/exclude() требует хотя бы одного условия")
        result = parts[0]
        for part in parts[1:]:
            result = result & part
        return result

    def filter(self, *args, **kwargs) -> "QuerySet":
        return self._add_q(self._build_q(args, kwargs))

    def exclude(self, *args, **kwargs) -> "QuerySet":
        return self._add_q(-self._build_q(args, kwargs))

    def order_by(self, *fields) -> "QuerySet":
        qs = self._clone()
        qs._ordering = list(fields)
        qs._result_cahe = None
        return qs

    def _build_select_sql(self) -> tuple[str, list]:
        where_sql, params = build_where(self._q)
        order_sql = build_order_by(self._ordering)
        query = " ".join(
            filter(
                None,
                [
                    f"SELECT * FROM {self.model_class.table_name}",
                    where_sql,
                    order_sql,
                ],
            )
        )
        return query, params

    def _fetch(self) -> list:
        if self._result_cahe is not None:
            return self._result_cahe

        query, params = self._build_select_sql()
        cursor = self.connection.cursor()
        cursor.execute(query, params)

        col_names = tuple(desc[0] for desc in cursor.description)
        self._result_cahe = [
            self.model_class(**dict(zip(col_names, row))) for row in cursor.fetchall()
        ]
        return self._result_cahe


LOOKUP_OPERATORS = {
    "exact": "+",
    "ne": "!=",
    "lt": "<",
    "lte": "<=",
    "gt": ">",
    "gte": ">=",
    "like": "LIKE",
    "in": "IN",
}


class QuerySet:
    """
    Лений набор запросов. Не ходит в БД до итерации или вызова метода.


    Employee.objects
        .filte(salary_gre=10000)
        .exclude(grade="L1")
        .filter(Q(first_name__like="A%") | Q(last_name__like="B%"))
        .order_by("-salary")
    """

    def __init__(self, model_class, connection):
        self.model_class = model_class
        self.connection = connection
        self._q: Q | None = None
        self.ordering: list[str] = []
        self._result_cahe = None

    def _clone(self) -> "QuerySet":
        qs = QuerySet(self.model_class, self.connection)
        qs._q = copy.copy(self._q)
        qs._ordering = self._ordering.copy()
        return qs

    def _add_q(self, q: Q) -> "QuerySet":
        qs = self._clone()
        qs._result_cahe = None
        qs._q = q if qs._q is None else qs._q & q
        return qs

    @staticmethod
    def _build_q(args, kwargs) -> Q:
        parts = list(args) + ([Q(**kwargs)] if kwargs else [])
        if not parts:
            raise ValueError("filter()/exlude() требуют хотя одного условия")
        result = parts[0]
        for part in parts[1:]:
            result = result & part
        return result

    def filter(self, *args, **kwargs) -> "QuerySet":
        """Добавляет AND-условие."""
        return self._add_q(self._build_q(args, kwargs))

    def exclude(self, *args, **kwargs) -> "QuerySet":
        """Добавляет NOT-условие."""
        return self._add_q(-self._build_q(args, kwargs))

    def order_by(self, *fields) -> "QuerySet":
        """.order_by('-salary', 'last_name')"""
        qs = self._clone()
        qs._ordering = list(fields)
        qs._result_cahe = None
        return qs

    def _build_select_sql(self) -> tuple[str, list]:
        where_sql, params = build_where(self._q)
        order_sql = build_where_by(self._ordering)
        query = " ".join(
            filter(
                None,
                [
                    f"SELECT * FROM {self.model_class.table_name}",
                    where_sql,
                    order_sql,
                ],
            )
        )
        return query, params

    def _fetch(self) -> list:
        """SELECT  c к"""
