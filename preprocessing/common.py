import re
import pandas as pd

def rm_spaces(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].str.replace(r"\s$", "", regex=True)
    return df

def fix_initials_spacing(text: str) -> str:
    if not isinstance(text, str):
        return text
    # replace "С. М." -> "С.М."
    return re.sub(r"([А-ЯІЇЄҐ])\.\s+([А-ЯІЇЄҐ])\.", r"\1.\2.", text)