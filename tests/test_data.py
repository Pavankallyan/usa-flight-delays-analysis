"""Data-validation tests for the bundled 100k-row flight-delay sample.

Every assertion below was measured against the real
DataSets/Pavan_Kalyan_MP4_Sample_100k.csv — no fabricated expectations.
"""
import pandas as pd

from conftest import (
    DELAY_CAUSE_COLS,
    EXPECTED_COLUMNS,
    PRIMARY_CAUSES,
    TIME_OF_DAY,
)


def test_schema_columns(df):
    assert list(df.columns) == EXPECTED_COLUMNS


def test_row_count(df):
    assert len(df) == 100_000


def test_year_coverage(df):
    years = set(df["Year"].unique())
    assert years == {2019, 2020, 2021, 2022, 2023}


def test_binary_flags(df):
    assert set(df["Cancelled"].unique()) <= {0, 1}
    assert set(df["IsDelayed"].unique()) <= {0, 1}
    assert df["Cancelled"].notna().all()
    assert df["IsDelayed"].notna().all()


def test_cancelled_flights_have_no_arr_delay(df):
    cancelled = df[df["Cancelled"] == 1]
    assert len(cancelled) > 0  # 2,595 cancelled flights in the sample
    assert cancelled["ArrDelay"].isna().all()


def test_is_delayed_matches_delay_minutes_threshold(df):
    # The FAA convention: delayed = arrival delay of 15+ minutes.
    known = df[(df["Cancelled"] == 0) & df["DelayMinutes"].notna()]
    assert ((known["DelayMinutes"] >= 15).astype(int) == known["IsDelayed"]).all()


def test_delay_cause_columns_nonnegative(df):
    for col in DELAY_CAUSE_COLS:
        assert (df[col] >= 0).all(), f"{col} has negative values"


def test_iata_codes_and_route(df):
    assert (df["Origin"].str.len() == 3).all()
    assert (df["Dest"].str.len() == 3).all()
    assert (df["Route"] == df["Origin"] + "-" + df["Dest"]).all()


def test_hour_of_day_and_time_of_day(df):
    assert df["HourOfDay"].between(0, 23).all()
    assert set(df["TimeOfDay"].unique()) == TIME_OF_DAY


def test_distance_positive(df):
    assert (df["Distance"] > 0).all()


def test_carrier_column(df):
    assert df["UniqueCarrier"].notna().all()
    assert (df["UniqueCarrier"].str.strip() != "").all()


def test_primary_delay_cause_values(df):
    causes = df["PrimaryDelayCause"].dropna().unique()
    assert set(causes) <= PRIMARY_CAUSES


def test_flight_date_parses(df):
    dates = pd.to_datetime(df["FlightDate"], errors="coerce")
    assert dates.notna().all()
    assert dates.dt.year.between(2019, 2023).all()


def test_departure_time_hhmm(df):
    # CRSDepTime is HHMM military time, e.g. 805 -> 08:05.
    valid = ((df["CRSDepTime"] // 100).between(0, 23)) & (
        (df["CRSDepTime"] % 100).between(0, 59)
    )
    assert valid.all()
