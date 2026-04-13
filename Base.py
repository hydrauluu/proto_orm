from fields import BaseFieldDescriptor
from Manager import BaseManager


class MetaModel(type):
    """Метакласс — перехватывает создание класса модели."""

    manager_class = BaseManager

    def __new__(mcs, name, bases, attrs):
        fields = {
            key: val
            for key, val in attrs.items()
            if isinstance(val, BaseFieldDescriptor)
        }

        declared_slots = [f"_{field_name}" for field_name in fields]
        if "_id" not in declared_slots:
            declared_slots.append("_id")
        declared_slots.append("extra")

        attrs["__slots__"] = declared_slots
        attrs["_fields"] = fields

        return super().__new__(mcs, name, bases, attrs)

    def _get_manager(cls):
        return cls.manager_class(model_class=cls)

    @property
    def objects(cls):
        return cls._get_manager()


class BaseModel(metaclass=MetaModel):
    """Базовая модель. Наследуйтесь от неё и задайте table_name."""

    table_name = ""
    manager_class = BaseManager
    _fields: dict = {}

    def __init__(self, **row_data) -> None:
        object.__setattr__(self, "_extra", {})
        for field_name, value in row_data.items():
            if (
                f"_{field_name}" in self.__class__.__slots__
                or field_name in self.__class__._fields
            ):
                object.__setattr__(self, f"_{field_name}", value)
            else:
                self._extra[field_name] = value

    def __getattr__(self, name):
        extra = object.__getattribute__(self, "_extra")
        if name in extra:
            return extra[name]
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __repr__(self) -> str:
        extra = object.__getattribute__(self, "_extra")
        parts = {**extra}
        for k in self.__class__._fields:
            parts[k] = getattr(self, k, None)
        attrs = ", ".join(f"{k}={v}" for k, v in parts.items())
        return f"<{self.__class__.__name__}: ({attrs})>"

    class DoesNotExist(Exception):
        pass

    class MultipleObjectsReturned(Exception):
        pass
