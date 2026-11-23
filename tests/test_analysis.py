"""Unit tests for src/analysis.py.

Synthetic frames pin the arithmetic exactly; the real-data checks use the
session ``df`` fixture and assert values measured against the bundled
100k-row sample — no fabricated expectations.
"""

import math

import pandas as pd
import pytest

from conftest import DELAY_CAUSE_COLS, EXPECTED_COLUMNS
from src import analysis as a


def make_frame(rows):
    """Build a minimal frame with every column the helpers read."""
    cols = [
        "Cancelled", "DelayMinutes", "IsDelayed", "UniqueCarrier", "Route",
        "TimeOfDay", "Year", "PrimaryDelayCause",
    ] + DELAY_CAUSE_COLS
    frame = pd.DataFrame(rows, columns=cols)
    return frame


def test_load_sample_shape(df):
    loaded = a.load_sample()
    assert len(loaded) == 100_000
    assert list(loaded.columns) == EXPECTED_COLUMNS


def test_delay_cause_totals_synthetic():
    frame = make_frame([
        # Cancelled, DelayMinutes, IsDelayed, Carrier, Route, TimeOfDay, Year, Cause, Weather, Carrier, NAS, Security, LateAircraft
        [0, 20, 1, "AA", "A-B", "Morning", 2023, "Carrier", 0, 20, 0, 0, 0],
        [0, 5, 0, "AA", "A-B", "Morning", 2023, None, 0, 0, 0, 0, 0],
        [0, 45, 1, "DL", "B-C", "Evening", 2023, "LateAircraft", 5, 0, 10, 0, 30],
    ])
    totals = a.delay_cause_totals(frame)
    assert totals["LateAircraftDelay"] == 30
    assert totals["CarrierDelay"] == 20
    assert totals["NASDelay"] == 10
    assert totals["WeatherDelay"] == 5
    assert totals["SecurityDelay"] == 0
    assert list(totals.index)[0] == "LateAircraftDelay"  # sorted, largest first


def test_delay_cause_totals_real(df):
    totals = a.delay_cause_totals(df)
    assert totals["LateAircraftDelay"] == 445653.0
    assert totals["CarrierDelay"] == 410012.0
    assert totals["NASDelay"] == 231360.0
    assert totals["WeatherDelay"] == 67379.0
    assert totals["SecurityDelay"] == 2261.0
    assert list(totals.index)[0] == "LateAircraftDelay"


def test_primary_cause_counts_real(df):
    counts = a.primary_cause_counts(df)
    assert counts["LateAircraft"] == 6537
    assert counts["Carrier"] == 5905
    assert counts["NAS"] == 4569
    assert counts["Weather"] == 696
    assert counts["Security"] == 52
    assert counts.sum() == 17759  # delayed flights with a named primary cause


def test_on_time_rate_synthetic():
    frame = make_frame([
        [0, 10, 0, "AA", "A-B", "Morning", 2023, None, 0, 0, 0, 0, 0],
        [0, 15, 1, "AA", "A-B", "Morning", 2023, "Carrier", 0, 15, 0, 0, 0],
        [0, -5, 0, "AA", "A-B", "Morning", 2023, None, 0, 0, 0, 0, 0],
        [1, None, 0, "AA", "A-B", "Morning", 2023, None, 0, 0, 0, 0, 0],
    ])
    # 2 of 3 operated flights under 15 minutes; the cancelled row is excluded.
    assert a.on_time_rate(frame) == pytest.approx(2 / 3)


def test_on_time_rate_real(df):
    assert a.on_time_rate(df) == pytest.approx(0.8154, rel=1e-3)


def test_on_time_rate_no_operated_flights():
    frame = make_frame([
        [1, None, 0, "AA", "A-B", "Morning", 2023, None, 0, 0, 0, 0, 0],
    ])
    assert math.isnan(a.on_time_rate(frame))


def test_carrier_stats_synthetic():
    frame = make_frame([
        [0, 20, 1, "AA", "A-B", "Morning", 2023, "Carrier", 0, 20, 0, 0, 0],
        [0, 0, 0, "AA", "A-B", "Morning", 2023, None, 0, 0, 0, 0, 0],
        [1, None, 0, "AA", "A-B", "Morning", 2023, None, 0, 0, 0, 0, 0],
        [0, 30, 1, "DL", "B-C", "Evening", 2023, "NAS", 0, 0, 30, 0, 0],
    ])
    stats = a.carrier_stats(frame)
    assert list(stats.index) == ["AA", "DL"]  # busiest first
    assert stats.loc["AA", "flights"] == 3
    assert stats.loc["AA", "cancelled_rate"] == pytest.approx(1 / 3)
    assert stats.loc["AA", "delayed_rate"] == pytest.approx(0.5)
    assert stats.loc["AA", "mean_delay_minutes"] == pytest.approx(10.0)
    assert stats.loc["DL", "flights"] == 1
    assert stats.loc["DL", "delayed_rate"] == pytest.approx(1.0)


def test_carrier_stats_real(df):
    stats = a.carrier_stats(df)
    assert len(stats) == 18
    assert stats["flights"].sum() == 100_000
    assert ((stats["cancelled_rate"] >= 0) & (stats["cancelled_rate"] <= 1)).all()
    assert ((stats["delayed_rate"] >= 0) & (stats["delayed_rate"] <= 1)).all()
    assert stats["flights"].is_monotonic_decreasing


def test_route_stats_synthetic():
    frame = make_frame([
        [0, 20, 1, "AA", "A-B", "Morning", 2023, "Carrier", 0, 20, 0, 0, 0],
        [0, 0, 0, "AA", "A-B", "Morning", 2023, None, 0, 0, 0, 0, 0],
        [0, 30, 1, "DL", "B-C", "Evening", 2023, "NAS", 0, 0, 30, 0, 0],
    ])
    stats = a.route_stats(frame, top_n=1)
    assert len(stats) == 1
    assert stats.index[0] == "A-B"
    assert stats.loc["A-B", "flights"] == 2
    assert stats.loc["A-B", "delayed_rate"] == pytest.approx(0.5)


def test_route_stats_real(df):
    stats = a.route_stats(df)
    assert len(stats) == 10
    assert stats.index[0] == "HNL-OGG"
    assert stats.loc["HNL-OGG", "flights"] == 179
    assert stats["flights"].is_monotonic_decreasing


def test_delayed_rate_by_time_of_day_real(df):
    rates = a.delayed_rate_by_time_of_day(df)
    assert set(rates.index) == {"Morning", "Afternoon", "Evening", "Night"}
    assert rates["Evening"] == pytest.approx(0.2511, rel=1e-3)  # worst time of day
    assert rates["Morning"] == pytest.approx(0.1277, rel=1e-3)  # best time of day
    assert rates["Evening"] > rates["Morning"]


def test_yearly_trend_real(df):
    trend = a.yearly_trend(df)
    assert list(trend.index) == [2019, 2020, 2021, 2022, 2023]
    assert trend["flights"].sum() == 100_000
    assert trend.loc[2020, "delayed_rate"] == pytest.approx(0.0974, rel=1e-3)
    assert trend["delayed_rate"].idxmin() == 2020  # pandemic year, fewest delays
    assert trend.loc[2023, "delayed_rate"] == pytest.approx(0.2281, rel=1e-3)


def test_operated_excludes_cancelled():
    frame = make_frame([
        [0, 0, 0, "AA", "A-B", "Morning", 2023, None, 0, 0, 0, 0, 0],
        [1, None, 0, "AA", "A-B", "Morning", 2023, None, 0, 0, 0, 0, 0],
    ])
    assert len(a.operated(frame)) == 1
    assert a.operated(frame)["Cancelled"].eq(0).all()
