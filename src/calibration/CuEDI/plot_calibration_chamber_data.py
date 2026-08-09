

"""
plot_eepaa_csv.py

Loads .csv files in the same format as the UIOWA_OCHRE_CuEDI_calChamber
data files and plots a specified variable (column) against time using matplotlib.

Note on file format: these files have one extra trailing comma per data row
compared to the header row (an extra empty field at the end of each line).
If read with plain pandas defaults, this causes pandas to silently treat the
first column as an index and shift every other column over by one. This
script uses index_col=False to avoid that.

Usage examples:
    python plot_eepaa_csv.py data.csv eepaa_word07
    python plot_eepaa_csv.py data.csv eepaa_word06 eepaa_word07 --out plot.png
    python plot_eepaa_csv.py data.csv eepaa_word07 --list-columns
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt

TIME_COL = "IRIG ddd:hh:mm:ss.ffffff"

# ---------------------------------------------------------------------------
# EDIT THESE TWO VALUES
# ---------------------------------------------------------------------------
DATA_FILE = "/home/connor/Desktop/UIOWA_OCHRE_CuEDI_calChamber_20260803_test7_bais2100_mcp3500.csv"  # path to the .csv file
VARIABLE = "eepaa_word09"  # column/keyname to plot
# ---------------------------------------------------------------------------


def load_csv(path: str) -> pd.DataFrame:
    """Load a CSV in the eepaa/OCHRE format.

    These files have a ragged trailing field: most data rows have one more
    comma-separated field than the header row (an extra empty field at the
    end of the line). pandas' parser handles this inconsistently across
    versions/engines (sometimes silently shifting columns via an implicit
    index, sometimes raising a ParserError), so this reads the file manually
    line-by-line and truncates/pads each row to match the header length
    before handing it to pandas.
    """
    with open(path, "r") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split(",")
    ncols = len(header)

    rows = []
    for line in lines[1:]:
        line = line.rstrip("\n")
        if not line:
            continue
        fields = line.split(",")
        if len(fields) > ncols:
            fields = fields[:ncols]  # drop extra trailing (empty) field(s)
        elif len(fields) < ncols:
            fields = fields + [""] * (ncols - len(fields))  # pad short rows
        rows.append(fields)

    df = pd.DataFrame(rows, columns=header)

    # Convert everything possible to numeric; leave non-numeric columns
    # (e.g. the IRIG timestamp string) as-is.
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass  # leave non-numeric columns (e.g. IRIG timestamp) as strings

    return df


def plot_variable(df: pd.DataFrame, column: str, time_col: str = TIME_COL,
                   out_path: str = None):
    if column not in df.columns:
        raise ValueError(
            f"Column '{column}' not found.\n"
            f"Available columns: {list(df.columns)}"
        )

    fig, ax = plt.subplots(figsize=(12, 6))

    if time_col in df.columns:
        x = range(len(df))  # IRIG timestamps are strings; plot by sample index
        ax.set_xlabel(f"Sample index (time col: {time_col})")
    else:
        x = df.index
        ax.set_xlabel("Sample index")

    ax.plot(x, df[column], linewidth=1)
    ax.set_ylabel(column)
    ax.set_title(f"{column} vs. sample index")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if out_path:
        fig.savefig(out_path, dpi=150)
        print(f"Saved plot to {out_path}")
    else:
        plt.show()


def main():
    df = load_csv(DATA_FILE)

    if VARIABLE not in df.columns:
        print(f"'{VARIABLE}' not found in {DATA_FILE}.")
        print("Available columns:")
        for c in df.columns:
            print(f"  {c}")
        sys.exit(1)

    plot_variable(df, VARIABLE)


if __name__ == "__main__":
    main()