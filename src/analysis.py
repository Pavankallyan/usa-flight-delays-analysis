"""Reusable delay-analysis helpers for the bundled 100k-row sample.

Every function takes a DataFrame with the sample's schema (see
``tests/conftest.py``) and returns plain pandas objects, so the same code
powers the tests, the examples, and any notebook exploration. Delayed means
``DelayMinutes >= 15`` (the dataset's own ``IsDelayed`` definition); rates
are computed over operated (non-cancelled) flights unless noted.
"""

import io
import zipfile
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = REPO_ROOT / "DataSets" / "Pavan_Kalyan_MP4_Sample_100k.csv.zip"
CSV_NAME = "Pavan_Kalyan_MP4_Sample_100k.csv"

DELAY_CAUSE_COLS = [
    "WeatherDelay",
    "CarrierDelay",
    "NASDelay",
    "SecurityDelay",
    "LateAircraftDelay",
]
DELAY_THRESHOLD_MIN = 15


def load_sample() -> pd.DataFrame:
    """Read the 100k-row sample CSV straight out of the zip in ``DataSets/``."""
    with zipfile.ZipFile(ZIP_PATH) as zf:
        with zf.open(CSV_NAME) as fh:
            return pd.read_csv(io.BytesIO(fh.read()))


def operated(df: pd.DataFrame) -> pd.DataFrame:
    """Flights that were not cancelled (the population delay rates describe)."""
    return df[df["Cancelled"] == 0]


def delay_cause_totals(df: pd.DataFrame) -> pd.Series:
    """Total delay minutes per cause column, largest cause first."""
    totals = df[DELAY_CAUSE_COLS].sum(numeric_only=True)
    return totals.sort_values(ascending=False)


def primary_cause_counts(df: pd.DataFrame) -> pd.Series:
    """How many delayed flights name each primary cause (on-time rows excluded)."""
    return df["PrimaryDelayCause"].dropna().value_counts()


def on_time_rate(df: pd.DataFrame) -> float:
    """Share of operated flights arriving with less than 15 minutes of delay.

    Returns NaN when the frame holds no operated flights.
    """
    op = operated(df)
    if len(op) == 0:
        return float("nan")
    return float((op["DelayMinutes"] < DELAY_THRESHOLD_MIN).mean())


def carrier_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Per-carrier volume, cancellation rate, delay rate, mean delay minutes.

    Delay rate and mean delay are over operated flights only; rows are
    sorted by flight count, busiest carrier first.
    """
    op = operated(df)
    stats = pd.DataFrame(
        {
            "flights": df.groupby("UniqueCarrier").size(),
            "cancelled_rate": df.groupby("UniqueCarrier")["Cancelled"].mean(),
            "delayed_rate": op.groupby("UniqueCarrier")["IsDelayed"].mean(),
            "mean_delay_minutes": op.groupby("UniqueCarrier")["DelayMinutes"].mean(),
        }
    )
    return stats.sort_values("flights", ascending=False)


def route_stats(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Busiest routes with delay rate and mean delay minutes.

    Delay rate and mean delay are over operated flights only; rows are
    sorted by flight count, busiest route first, keeping the top ``top_n``.
    """
    op = operated(df)
    stats = pd.DataFrame(
        {
            "flights": df.groupby("Route").size(),
            "delayed_rate": op.groupby("Route")["IsDelayed"].mean(),
            "mean_delay_minutes": op.groupby("Route")["DelayMinutes"].mean(),
        }
    )
    return stats.sort_values("flights", ascending=False).head(top_n)


def delayed_rate_by_time_of_day(df: pd.DataFrame) -> pd.Series:
    """Delay rate (operated flights) for each part of the day."""
    return operated(df).groupby("TimeOfDay")["IsDelayed"].mean()


def yearly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Per-year volume, cancellation rate, delay rate, mean delay minutes.

    Delay rate and mean delay are over operated flights only.
    """
    op = operated(df)
    trend = pd.DataFrame(
        {
            "flights": df.groupby("Year").size(),
            "cancelled_rate": df.groupby("Year")["Cancelled"].mean(),
            "delayed_rate": op.groupby("Year")["IsDelayed"].mean(),
            "mean_delay_minutes": op.groupby("Year")["DelayMinutes"].mean(),
        }
    )
    return trend.sort_index()
