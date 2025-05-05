import re
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional,TypeVar

from pydantic import BaseModel

_T = TypeVar("_T", bound=BaseModel)


def optional_datetime_from_string(str_time: str) -> Optional[datetime]:
    try:
        return datetime_from_string(str_time=str_time)
    except Exception:  # pylint: disable=broad-exception-caught
        return None


def datetime_from_string(str_time: str) -> datetime:
    formats = [
        "%Y-%m-%d %H:%M:%S",  # Example: 2024-05-12 15:30:00
        "%Y-%m-%d %I:%M %p",  # Example: 2024-05-12 3:30 PM
        "%Y-%m-%d",  # Example: 2024-05-12
        "%m/%d/%Y",  # Example: 05/12/2024
        "%m/%d/%y",  # Example: 05/12/24
        "%B %d, %Y",  # Example: May 12, 2024
        "%d %B %Y",  # Example: 12 May 2024
        "%d/%m/%Y",  # Example: 12/05/2024
        "%d/%m/%y",  # Example: 31/05/24
        "%d-%m-%y",  # Example: 31-05-24
        "%d-%m-%Y",  # Example: 31-05-2024
    ]

    # Try parsing the date string using each format
    for fmt in formats:
        try:
            return datetime.strptime(str_time, fmt).replace(
                tzinfo=timezone.utc,
            )
        except ValueError:
            pass
    raise ValueError(f"did not match any time format for {str_time}")


def is_string_in_enum(enum_type: type[Enum], value: str) -> bool:
    value_lower = value.lower()
    for item in enum_type:
        if item.value.lower() == value_lower:
            return True
    return False

def clean_alphanumeric(input_string: str) -> str:
    cleaned_string = re.sub(r"[^a-zA-Z0-9]", "", input_string)
    return cleaned_string.lower()


def clean_alpha(input_string: str) -> str:
    cleaned_string = re.sub(r"[^a-zA-Z]", "", input_string)
    return cleaned_string.lower()


def clean_struct(data: _T, cleaner_func: Callable[[str], str] = clean_alpha) -> _T:
    data_dict = data.model_dump()
    new_dict = {}
    for k, v in data_dict.items():
        new_value = v
        if isinstance(v, str):
            new_value = cleaner_func(v)

        new_dict[k] = new_value
    return data.model_validate(new_dict)


def empty(input_string: Optional[str]) -> bool:
    return input_string is None or input_string == ""


def time_ms() -> int:
    return int(time.time() * 1000)
