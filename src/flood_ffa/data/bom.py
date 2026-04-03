"""
Data loader for Bureau of Meteorology (BOM) annual maximum series (AMS) data.
"""

import pandas as pd
from pathlib import Path


def load_ams(filepath: str | Path) -> pd.DataFrame:
    """
    Load an annual maximum series (AMS) CSV file.

    Parameters
    ----------
    filepath : str or Path
        Path to the AMS CSV file. Expected columns:
        year, water_level_mAHD, flow_m3s

    Returns
    -------
    pd.DataFrame
        DataFrame indexed by year with columns:
        water_level_mAHD, flow_m3s
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()
    df["year"] = df["year"].astype(int)
    df = df.set_index("year")
    df = df.sort_index()
    return df


def get_flow_series(df: pd.DataFrame) -> pd.Series:
    """
    Extract the annual maximum flow series.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame returned by load_ams()

    Returns
    -------
    pd.Series
        Annual maximum flows in m3/s, indexed by year
    """
    return df["flow_m3s"]