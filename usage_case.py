from ORM import BaseManager, BaseModel


class Employee(BaseModel):
    manager_class = BaseManager
    table_name = "employees"


employees = Employee.objects.select("first_name", "grade")
print(employees)
