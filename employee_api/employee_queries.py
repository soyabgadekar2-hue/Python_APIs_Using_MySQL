from database import get_connection


def _close_resources(connection, cursor):
    try:
        if cursor is not None:
            cursor.close()
    finally:
        connection.close()


def get_all_employees():
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, email, department, salary "
            "FROM employees ORDER BY id"
        )
        return cursor.fetchall()
    finally:
        _close_resources(connection, cursor)


def get_employee_by_id(employee_id):
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, email, department, salary "
            "FROM employees WHERE id = %s",
            (employee_id,),
        )
        return cursor.fetchone()
    finally:
        _close_resources(connection, cursor)


def create_employee(employee):
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "INSERT INTO employees (name, email, department, salary) "
            "VALUES (%s, %s, %s, %s)",
            (
                employee["name"],
                employee["email"],
                employee["department"],
                employee["salary"],
            ),
        )
        employee_id = cursor.lastrowid
        connection.commit()
        cursor.execute(
            "SELECT id, name, email, department, salary "
            "FROM employees WHERE id = %s",
            (employee_id,),
        )
        return cursor.fetchone()
    except Exception:
        connection.rollback()
        raise
    finally:
        _close_resources(connection, cursor)


def update_employee(employee_id, employee):
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "UPDATE employees "
            "SET name = %s, email = %s, department = %s, salary = %s "
            "WHERE id = %s",
            (
                employee["name"],
                employee["email"],
                employee["department"],
                employee["salary"],
                employee_id,
            ),
        )
        connection.commit()
        cursor.execute(
            "SELECT id, name, email, department, salary "
            "FROM employees WHERE id = %s",
            (employee_id,),
        )
        return cursor.fetchone()
    except Exception:
        connection.rollback()
        raise
    finally:
        _close_resources(connection, cursor)


def delete_employee(employee_id):
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
        deleted = cursor.rowcount > 0
        connection.commit()
        return deleted
    except Exception:
        connection.rollback()
        raise
    finally:
        _close_resources(connection, cursor)


def import_employees(employees):
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.executemany(
            "INSERT INTO employees (name, email, department, salary) "
            "VALUES (%s, %s, %s, %s)",
            [
                (employee["name"], employee["email"], employee["department"], employee["salary"])
                for employee in employees
            ],
        )
        imported_count = cursor.rowcount
        connection.commit()
        return imported_count
    except Exception:
        connection.rollback()
        raise
    finally:
        _close_resources(connection, cursor)