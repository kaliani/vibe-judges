import re
import pandas as pd
import numpy as np

def detect_name_type(name: str) -> str:

    full_pattern = re.compile(
        r"^[\s]*[А-ЯІЇЄҐ][а-яіїєґ’'\-]+(?:-[А-ЯІЇЄҐ][а-яіїєґ’'\-]+)?\s+[А-ЯІЇЄҐ][а-яіїєґ’'\-]+\s+[А-ЯІЇЄҐ][а-яіїєґ’'\-]+\s*$"
    )

    initials_pattern = re.compile(
        r"^[\s]*[А-ЯІЇЄҐ][а-яіїєґ’'\-]+(?:-[А-ЯІЇЄҐ][а-яіїєґ’'\-]+)?\s+(?:[А-ЯІЇЄҐ]\.\s*){1,2}\s*$"
    )
    
    if full_pattern.match(name):
        return "full"
    elif initials_pattern.match(name):
        return "initials"
    else:
        return "other"
    
def mark_record_type(df: pd.DataFrame, duplicates_doc: list) -> pd.DataFrame:
    df = df.copy()

    conditions = [
        # all_matching
        ((~df["id"].isna()) & (df["court_code_documents"] == df["court_code_judges"])),
        # not_courts_matching
        ((~df["id"].isna()) & (df["court_code_documents"] != df["court_code_judges"])),
        # initials_not_matching
        ((df["id"].isna()) & (~df["doc_id"].isin(duplicates_doc))),
        # duplicates_doc
        (df["doc_id"].isin(duplicates_doc))
    ]

    choices = [
        "all_matching",
        "not_courts_matching",
        "initials_not_matching",
        "duplicates_doc"
    ]

    df["record_type"] = np.select(conditions, choices, default="unknown")

    return df

from typing import Optional
import pandas as pd


def create_clean_documents(
    documents: pd.DataFrame,
    new_judges: pd.DataFrame,
    *,
    judge_col_initials: str = "judge",      # column in documents that holds judge name
    judge_col_full: str = "judge",          # same column used for 'full' type
    doc_type_col: str = "type_name",
    doc_id_col: str = "doc_id",
    judges_short_col: str = "short_name",
    judges_full_col: str = "full_name",
    judges_court_col: str = "court_code",
) -> pd.DataFrame:

    temp_doc = (
        documents[documents[doc_type_col] == "initials"]
        .merge(
            new_judges[["id", judges_short_col, judges_court_col]],
            left_on=[judge_col_initials],
            right_on=[judges_short_col],
            how="left",
        )
        .copy()
    )
    temp_doc.rename(
        columns={
            f"{judges_court_col}_x": "court_code_documents",
            f"{judges_court_col}_y": "court_code_judges",
        },
        inplace=True,
    )

    # find duplicates among initials-matched docs by doc_id
    duplicates_doc = (
        temp_doc[doc_id_col]
        .value_counts()
        .reset_index(name="count")
        .query("count > 1")[doc_id_col]
        .unique()
    )

    # keep only non-duplicate initials for the main concat (duplicates will be added as a separate bucket)
    temp_doc = temp_doc[~temp_doc[doc_id_col].isin(duplicates_doc)].copy()

    # --- full-name docs ---
    full_doc = (
        documents[documents[doc_type_col] == "full"]
        .merge(
            new_judges[["id", judges_full_col, judges_court_col]],
            left_on=[judge_col_full],
            right_on=[judges_full_col],
            how="left",
        )
        .copy()
    )
    full_doc.rename(
        columns={
            f"{judges_court_col}_x": "court_code_documents",
            f"{judges_court_col}_y": "court_code_judges",
        },
        inplace=True,
    )

    # --- other docs (no join) ---
    other_doc = (
        documents[documents[doc_type_col] == "other"]
        .rename(columns={judges_court_col: "court_code_documents"})
        .copy()
    )
    if "court_code_judges" not in other_doc.columns:
        other_doc["court_code_judges"] = pd.NA
    if "id" not in other_doc.columns:
        other_doc["id"] = pd.NA  # to make mark_record_type conditions work uniformly

    # --- duplicate docs bucket (as-is from documents) ---
    dup_bucket = (
        documents[documents[doc_id_col].isin(duplicates_doc)]
        .rename(columns={judges_court_col: "court_code_documents"})
        .copy()
    )
    if "court_code_judges" not in dup_bucket.columns:
        dup_bucket["court_code_judges"] = pd.NA
    if "id" not in dup_bucket.columns:
        dup_bucket["id"] = pd.NA

    # unify columns before concat (ensure required columns exist)
    required_cols = {
        doc_id_col,
        "id",
        "court_code_documents",
        "court_code_judges",
    }
    def _ensure_cols(df: pd.DataFrame) -> pd.DataFrame:
        for c in required_cols:
            if c not in df.columns:
                df[c] = pd.NA
        return df

    temp_doc = _ensure_cols(temp_doc)
    full_doc = _ensure_cols(full_doc)
    other_doc = _ensure_cols(other_doc)
    dup_bucket = _ensure_cols(dup_bucket)

    # --- concat all parts ---
    new_documents = pd.concat([temp_doc, full_doc, other_doc, dup_bucket], ignore_index=True)

    # --- label records ---
    new_documents = mark_record_type(new_documents, list(duplicates_doc))

    new_documents = new_documents.rename(columns={"judge": "short_name_documents", 
                              "short_name": "short_name_judges",
                              "id": "judge_id"}).drop(columns=["full_name", "type_name"])

    return new_documents