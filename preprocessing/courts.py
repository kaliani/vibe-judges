import pandas as pd

def drop_last_two_words(text: str) -> str:
    if not isinstance(text, str):
        return text
    parts = text.strip().split()
    if len(parts) < 2:
        return text
    
    last_two = " ".join(parts[-2:])
    if "області" in last_two.lower():
        return " ".join(parts[:-2])
    return text

def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:

    duplicated_code = df["id"].value_counts().reset_index().query("count > 1")["id"].to_list()
    df.loc[df["id"].isin(duplicated_code), "court_code"] = pd.NA
    df = df.drop_duplicates(subset=["id"])

    return df

def fix_court_names(judges, courts):
    def fix_name(name):
        if pd.isna(name):
            return name
        name = name.replace(" міста", " м.")
        return drop_last_two_words(name)

    temp = judges.merge(courts, left_on="court_name", right_on="name", how="left")

    ### duplicates by court_name
    temp = drop_duplicates(temp)
    problem_names = temp.loc[temp.court_code.isna(), "court_name"].unique()

    judges.loc[judges["court_name"].isin(problem_names), "court_name"] = (
        judges.loc[judges["court_name"].isin(problem_names), "court_name"].map(fix_name)
    )

    new_judges = (
        judges.merge(courts[["court_code", "name"]], left_on="court_name", right_on="name", how="left")
              .drop(columns="name")
    )
    return new_judges
