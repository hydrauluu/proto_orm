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

        private_slots = [f"_{field_name}" for field_name in fields]

        if not any("__dict__" in vars(b) for b in bases):
            private_slots.append("__dict__")

        attrs["__slots__"] = private_slots
        attrs["_fields"]   = fields

        return super().__new__(mcs, name, bases, attrs)

    def _get_manager(cls):
        return cls.manager_class(model_class=cls)

    @property
    def objects(cls):
        return cls._get_manager()


class BaseModel(metaclass=MetaModel):
    """Базовая модель. Наследуйтесь от неё и задайте table_name."""

    table_name    = ""
    manager_class = BaseManager

    def __init__(self, **row_data) -> None:
        for field_name, value in row_data.items():
            setattr(self, field_name, value)

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"<{self.__class__.__name__}: ({attrs})>"
