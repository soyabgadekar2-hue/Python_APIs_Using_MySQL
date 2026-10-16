import csv
import json
import re
import shutil
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent
REPORTS_DIRECTORY = PROJECT_DIRECTORY / "reports"
MAX_TEXT_LENGTH = 1_000_000
MAX_CSV_BYTES = 2_000_000
MAX_CSV_ROWS = 5_000
MAX_JSON_BYTES = 2_000_000
CSV_IMPORT_FIELDS = ("name", "email", "department", "salary")
CSV_EXPORT_FIELDS = ("id", "name", "email", "department", "salary")


def _get_reports_directory():
    REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    resolved_directory = REPORTS_DIRECTORY.resolve()
    if resolved_directory.parent != PROJECT_DIRECTORY:
        raise ValueError("The reports folder must stay inside the project folder.")
    return REPORTS_DIRECTORY


def _get_text_path(filename):
    valid_name = re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,95}\.txt", filename)
    if valid_name is None:
        raise ValueError("Use a simple filename ending in .txt; folder paths are not allowed.")

    reports_directory = _get_reports_directory()
    file_path = reports_directory / filename
    if file_path.is_symlink():
        raise ValueError("Symbolic links cannot be used for text-file operations.")
    if file_path.resolve(strict=False).parent != reports_directory.resolve():
        raise ValueError("The file must stay inside the reports folder.")
    return file_path


def _get_existing_text_path(filename):
    file_path = _get_text_path(filename)
    if not file_path.is_file():
        raise FileNotFoundError("The text file does not exist.")
    return file_path


def create_text_file(filename):
    file_path = _get_text_path(filename)
    with file_path.open("x", encoding="utf-8"):
        pass


def write_text_file(filename, content):
    if len(content) > MAX_TEXT_LENGTH:
        raise ValueError("Text content must not exceed 1,000,000 characters.")
    file_path = _get_text_path(filename)
    file_path.write_text(content, encoding="utf-8")


def append_text_file(filename, content):
    if len(content) > MAX_TEXT_LENGTH:
        raise ValueError("Text content must not exceed 1,000,000 characters.")
    file_path = _get_text_path(filename)
    with file_path.open("a", encoding="utf-8") as text_file:
        text_file.write(content)


def read_text_file(filename):
    return _get_existing_text_path(filename).read_text(encoding="utf-8")


def read_text_file_lines(filename):
    content = _get_existing_text_path(filename).read_text(encoding="utf-8")
    return content.splitlines()


def text_file_exists(filename):
    return _get_text_path(filename).is_file()


def rename_text_file(filename, new_filename):
    source_path = _get_existing_text_path(filename)
    destination_path = _get_text_path(new_filename)
    if destination_path.exists():
        raise FileExistsError("A file with the new name already exists.")
    source_path.rename(destination_path)


def copy_text_file(filename, new_filename):
    source_path = _get_existing_text_path(filename)
    destination_path = _get_text_path(new_filename)
    if destination_path.exists():
        raise FileExistsError("A file with the new name already exists.")

    destination_file = destination_path.open("xb")
    try:
        with source_path.open("rb") as source_file, destination_file:
            shutil.copyfileobj(source_file, destination_file)
    except OSError:
        try:
            destination_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def delete_text_file(filename):
    _get_existing_text_path(filename).unlink()


def get_text_file_size(filename):
    return _get_existing_text_path(filename).stat().st_size


def _get_csv_path(filename, directory):
    valid_name = re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,95}\.csv", filename)
    if valid_name is None:
        raise ValueError("Use a simple filename ending in .csv; folder paths are not allowed.")

    directory.mkdir(parents=True, exist_ok=True)
    resolved_directory = directory.resolve()
    if resolved_directory.parent != PROJECT_DIRECTORY:
        raise ValueError("The CSV folder must stay inside the project folder.")

    file_path = directory / filename
    if file_path.is_symlink():
        raise ValueError("Symbolic links cannot be used for CSV operations.")
    if file_path.resolve(strict=False).parent != resolved_directory:
        raise ValueError("The CSV file must stay inside its designated folder.")
    return file_path


def read_employee_csv(filename):
    uploads_directory = PROJECT_DIRECTORY / "uploads"
    file_path = _get_csv_path(filename, uploads_directory)
    if not file_path.is_file():
        raise FileNotFoundError("The CSV file does not exist in the uploads folder.")
    if file_path.stat().st_size > MAX_CSV_BYTES:
        raise ValueError("CSV files must not exceed 2,000,000 bytes.")

    employee_rows = []
    try:
        with file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file, strict=True)
            if reader.fieldnames != list(CSV_IMPORT_FIELDS):
                expected_fields = ", ".join(CSV_IMPORT_FIELDS)
                raise ValueError(f"CSV header must be exactly: {expected_fields}.")

            for row_number, row in enumerate(reader, start=2):
                if None in row:
                    raise ValueError(f"CSV row {row_number} has more values than headers.")
                employee_rows.append((row_number, row))
                if len(employee_rows) > MAX_CSV_ROWS:
                    raise ValueError("CSV files must not contain more than 5,000 employee rows.")
    except csv.Error:
        raise ValueError("CSV formatting is invalid.") from None

    if not employee_rows:
        raise ValueError("The CSV file must contain at least one employee row.")
    return employee_rows


def write_employee_csv(filename, employees):
    file_path = _get_csv_path(filename, REPORTS_DIRECTORY)
    created_file = False
    try:
        with file_path.open("x", encoding="utf-8", newline="") as csv_file:
            created_file = True
            writer = csv.DictWriter(
                csv_file,
                fieldnames=CSV_EXPORT_FIELDS,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(employees)
    except Exception:
        if created_file:
            file_path.unlink(missing_ok=True)
        raise
    return file_path


def _get_json_path(filename):
    valid_name = re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,95}\.json", filename)
    if valid_name is None:
        raise ValueError("Use a simple filename ending in .json; folder paths are not allowed.")

    reports_directory = _get_reports_directory()
    file_path = reports_directory / filename
    if file_path.is_symlink():
        raise ValueError("Symbolic links cannot be used for JSON operations.")
    if file_path.resolve(strict=False).parent != reports_directory.resolve():
        raise ValueError("The JSON file must stay inside the reports folder.")
    return file_path


def read_json_file(filename):
    file_path = _get_json_path(filename)
    if not file_path.is_file():
        raise FileNotFoundError("The JSON file does not exist in the reports folder.")
    if file_path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("JSON files must not exceed 2,000,000 bytes.")

    try:
        with file_path.open("r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("The JSON file contains invalid JSON or text encoding.") from None


def write_json_file(filename, data):
    file_path = _get_json_path(filename)
    try:
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        raise ValueError("The supplied data cannot be represented as JSON.") from None
    if len(json_content.encode("utf-8")) > MAX_JSON_BYTES:
        raise ValueError("JSON files must not exceed 2,000,000 bytes.")

    with file_path.open("x", encoding="utf-8") as json_file:
        json_file.write(json_content)
    return file_path