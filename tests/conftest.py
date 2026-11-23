"""Shared fixtures for the flight-delays sample dataset tests.

Reads the bundled 100k-row sample CSV straight out of the zip in DataSets/
so no extracted files are left behind on disk.
"""
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))  # so tests can `import src.analysis`
ZIP_PATH = REPO_ROOT / "DataSets" / "Pavan_Kalyan_MP4_Sample_100k.csv.zip"
CSV_NAME = "Pavan_Kalyan_MP4_Sample_100k.csv"

EXPECTED_COLUMNS = [
    "FlightDate", "CRSDepTime", "ArrDelay", "Cancelled", "UniqueCarrier",
    "Origin", "Dest", "Distance", "WeatherDelay", "CarrierDelay", "NASDelay",
    "SecurityDelay", "LateAircraftDelay", "IsDelayed", "DelayMinutes",
    "HourOfDay", "TimeOfDay", "Season", "PrimaryDelayCause", "Route", "Year",
]

DELAY_CAUSE_COLS = [
    "WeatherDelay", "CarrierDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay",
]

PRIMARY_CAUSES = {"Carrier", "NAS", "LateAircraft", "Weather", "Security"}
TIME_OF_DAY = {"Morning", "Afternoon", "Evening", "Night"}


def load_sample() -> pd.DataFrame:
    with zipfile.ZipFile(ZIP_PATH) as zf:
        with zf.open(CSV_NAME) as fh:
            return pd.read_csv(io.BytesIO(fh.read()))


@pytest.fixture(scope="session")
def df() -> pd.DataFrame:
    return load_sample()
