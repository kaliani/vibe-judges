import re

def split_name(full_name: str) -> dict:
    if not isinstance(full_name, str) or not full_name.strip():
        return {"last_name": "", "first_name": "", "patronymic": "", "initials": ""}

    parts = full_name.strip().split()
    if len(parts) < 2:
        return {"last_name": "", "first_name": "", "patronymic": "", "initials": ""}

    last_name = parts[0]
    first_name = parts[1] if len(parts) > 1 else ""
    patronymic = parts[2] if len(parts) > 2 else ""

    initials = ""
    if first_name:
        initials += first_name[0].upper() + "."
    if patronymic:
        initials += patronymic[0].upper() + "."

    return {
        "last_name": last_name,
        "first_name": first_name,
        "patronymic": patronymic,
        "short_name": last_name+ " " +initials,
    }