"""
Load 52012_SCM_Handshake_8-14-26.csv into individual numpy arrays, one per
column, and convert the Time column into Python datetime objects.

The Time column in the source file looks like:
    226 21:23:12.89864
where "226" is the day-of-year and the rest is HH:MM:SS.ffffff. The day of
year is resolved against the year given in the filename (2026).

Usage:
    python csv_to_arrays.py /path/to/52012_SCM_Handshake_8-14-26.csv
"""

import csv
import sys
import datetime as dt
import numpy as np
import spaceToolsLib as stl

# Year the day-of-year values are relative to (from the filename: 8-14-26 = 2026-08-14)
YEAR = 2026
CSV_PATH = 'C:/Users/cfelt/OneDrive - University of Iowa/rockets/OCHRE/data/INT/SCM/52012_SCM_Handshake_8-14-26.csv'

def parse_time(value: str) -> dt.datetime:
    """Convert 'DDD HH:MM:SS.ffffff' -> datetime.datetime."""
    day_str, clock_str = value.split(" ", 1)
    day_of_year = int(day_str)
    base_date = dt.date(YEAR, 1, 1) + dt.timedelta(days=day_of_year - 1)

    h, m, s = clock_str.split(":")
    sec = float(s)
    whole_sec = int(sec)
    microsec = round((sec - whole_sec) * 1_000_000)

    return dt.datetime(
        base_date.year, base_date.month, base_date.day,
        int(h), int(m), whole_sec, microsec,
    )

def load_csv_to_arrays(path: str) -> dict:
    """Read the CSV and return {column_name: np.ndarray} for every column."""
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    n_rows = len(rows)
    n_cols = len(header)

    # Time column -> array of datetime objects (dtype=object)
    time_col = header[0]
    times = np.empty(n_rows, dtype=object)

    # Remaining columns -> float arrays (NaN where the CSV cell is blank,
    # since this is a sparse, one-value-updates-at-a-time log)
    data_cols = {name: np.full(n_rows, np.nan, dtype=np.float64) for name in header[1:]}

    for i, row in enumerate(rows):
        times[i] = parse_time(row[0])
        for j, name in enumerate(header[1:], start=1):
            cell = row[j]
            if cell:  # non-empty string
                data_cols[name][i] = float(cell)

    arrays = {time_col: times}
    arrays.update(data_cols)
    return arrays


def main():

    csv_path = CSV_PATH
    arrays = load_csv_to_arrays(csv_path)

    print(f"Loaded {len(arrays)} columns:")
    for name, arr in arrays.items():
        print(f"  {name!r}: shape={arr.shape}, dtype={arr.dtype}")

    data_dict_output = {
        key.replace(' [-]',''):[np.array(val),{'DEPEND_0':'Time'}] for key, val in arrays.items()
    }

    outputPath = 'C:/Users/cfelt/Desktop/SCM_test.cdf'
    stl.outputDataDict(outputPath=outputPath,
                       data_dict=data_dict_output)



def _sanitize(name: str) -> str:
    """npz keys can't contain '/', so make column names filesystem-safe."""
    return name.replace("/", "_").replace(" ", "_").replace("[", "").replace("]", "")


if __name__ == "__main__":
    main()