class BaseFieldDescriptor:
    """Базовый дескриптор поля"""

    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, object_type=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        value = self.validate(value)
        setattr(obj, self.private_name, value)

    def validate(self, value):
        return value


class IntegerField(BaseFieldDescriptor):
    """Дескриптор поля типа int"""

    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value):
        if not isinstance(value, int):
            raise TypeError(f"{self.name} Ожидалось int, а получено {type(value)}")
        if self.min_value is not None and value < self.min_value:
            raise ValueError(
                f"{self.name} Ожидалось значение >= {self.min_value}, а получено {value}"
            )
        if self.max_value is not None and value > self.max_value:
            raise ValueError(
                f"{self.name} Ожидалось значение <= {self.max_value}, а получено {value}"
            )
        return value


class FloatField(BaseFieldDescriptor):
    """Дескриптор поля типа float"""

    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value):
        if not isinstance(value, float):
            raise TypeError(
                f"{self.name} Ожидается тип float, а получено {type(value)}"
            )
        if self.min_value is not None and value < self.min_value:
            raise ValueError(
                f"{self.name} Ожидалось значение >= {self.min_value}, а получено {value}"
            )
        if self.max_value is not None and value > self.max_value:
            raise ValueError(
                f"{self.name} Ожидалось значение <= {self.max_value}, а получено {value}"
            )
        return value


class CharField(BaseFieldDescriptor):
    """Дескриптор поля типа str"""

    def __init__(self, max_length=None):
        self.max_length = max_length

    def validate(self, value):
        if not isinstance(value, str):
            raise TypeError(f"{self.name} Ожидается тип str, а получено {type(value)}")
        if self.max_length is not None and len(value) > self.max_length:
            raise ValueError(
                f"{self.name} Ожидалось значение <= {self.max_length}, а получено {len(value)}"
            )
        return value
