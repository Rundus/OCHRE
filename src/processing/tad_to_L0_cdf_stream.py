"""
tad_parser.py

Parser for ALTAIR Tarsus Archive Data (.tad) files.

FILE LAYOUT
-----------
[0 : 328]           Outer Dewesoft-style file header.
                     NOTE: the ASCII date string embedded at bytes[22:44] of
                     this header appears to be a static template value (not
                     the real acquisition date) -- do not trust it for the
                     year. Pass the correct year explicitly instead.

[328 : EOF]         Repeating minor frame records, each `rec_len` bytes
                     (auto-detected from the file, typically 252 bytes):

    bytes[0:4]    word0  - BCD time: 0000 + 100s/10s/1s day,
                            10s/1s hour, 10s/1s minute
    bytes[4:8]    word1  - BCD time: 10s/1s sec,
                            100s/10s/1s msec, 100s/10s/1s usec
    bytes[8:12]   word2  - minor frame count + status flags (see
                            decode_status_word for caveats)
    bytes[12:252] data   - 120 x 16-bit words. Packed as 32-bit words in the
                            file, each split into two 16-bit words (high 16
                            bits first). The first 32-bit word of this data
                            block is always the fixed frame sync pattern
                            (0xFE6B2840) -- it is data word[0]/word[1], not
                            separate overhead.

MAJOR FRAMES
------------
Each minor frame header's word2 encodes a minor_frame_count that cycles
0-9 and then resets, confirmed empirically on sample data (clean 10-record
cycle, no gaps). Ten consecutive minor frames (count 0..9) make up one
"major frame" -- a 10 x 120 matrix of 16-bit words. Use
`build_major_frames()` to assemble these into an N x 10 x 120 array.

USAGE
-----
    from tad_parser import parse_tad_file

    df = parse_tad_file("myfile.tad", year=2026)
    df.to_parquet("myfile.parquet")
"""
import os.path
import struct
import numpy as np
import pandas as pd
import spaceToolsLib as stl
import time
import glob
from src.processing.processing_classes import ProcessingClass
start_time = time.time()

# --- Pathing ---------------------------------------------------------------
justPrintFileNames = False
outputData = True
wFile = 4
wInstrs = ['CuEDI'] # Which instruments to strip the data from


# --- Datastream timing constants -------------------------------------------
# TODO: set these to the real values for this datastream. They control how
# each individual data word within a minor frame gets its own timestamp,
# offset from the minor frame header's decoded time (see
# `word_time_offset_sec` / `extract_instrument_stream` below).
BIT_RATE_BPS = 4_800_000     # datastream bit rate, in bits per second
WORD_BIT_SIZE_BITS = 16      # bits per data word (matches the 16-bit word
                              # split used throughout this parser)
TIME_PER_WORD_SEC = WORD_BIT_SIZE_BITS / BIT_RATE_BPS

FILE_HEADER_LEN = 328
MINOR_FRAME_HEADER_LEN = 12
SYNC_LEN = 4
DEFAULT_SYNC_WORD = bytes.fromhex("40286bfe")  # little-endian for 0xFE6B2840
DEFAULT_YEAR = 2026

# --- Datastream Instrument Word Definitions --------------------------------



def detect_record_length(data: bytes, sync_word: bytes,
                          search_start: int = FILE_HEADER_LEN) -> int:
    """
    Auto-detect the minor-frame record length by finding the most common
    (modal) spacing between successive occurrences of the frame sync word.
    """
    positions = []
    idx = search_start
    while True:
        idx = data.find(sync_word, idx)
        if idx == -1:
            break
        positions.append(idx)
        idx += 1
        if len(positions) > 500:
            break

    if len(positions) < 3:
        raise ValueError(
            "Could not find enough sync-word occurrences to detect the "
            "record length. Check that `sync_word` is correct for this file."
        )

    diffs = np.diff(positions)
    vals, counts = np.unique(diffs, return_counts=True)
    rec_len = int(vals[np.argmax(counts)])
    return rec_len


def decode_bcd_time(word0: int, word1: int):
    """Decode the BCD-packed timestamp from minor frame header words 0 and 1."""
    doy = (word0 >> 24 & 0xF) * 100 + (word0 >> 20 & 0xF) * 10 + (word0 >> 16 & 0xF)
    hour = (word0 >> 12 & 0xF) * 10 + (word0 >> 8 & 0xF)
    minute = (word0 >> 4 & 0xF) * 10 + (word0 & 0xF)
    sec = (word1 >> 28 & 0xF) * 10 + (word1 >> 24 & 0xF)
    msec = (word1 >> 20 & 0xF) * 100 + (word1 >> 16 & 0xF) * 10 + (word1 >> 12 & 0xF)
    usec = (word1 >> 8 & 0xF) * 100 + (word1 >> 4 & 0xF) * 10 + (word1 & 0xF)
    return doy, hour, minute, sec, msec, usec


def decode_status_word(word2: int) -> dict:
    """
    Decode Word 2: minor frame count (bits 16-31) + status flags (bits 0-15),
    per the confirmed ALTAIR Table 8 bit definitions:

        bits 0-2   Current Format # Indicator
        bits 3-4   Minor Frame Lock      (2=Lock, 1=Check, 0=Search)
        bits 5-6   Sub-Frame Lock        (2=Lock, 1=Check, 0=Search)
        bit  7     Bit Sync Loop Lock
        bits 8-11  # Sync Errors
        bit  12    Bit Slip              (1=yes, 0=no)
        bit  13    Bit Sync Source       (0=Internal, 1=External)
        bit  14    Time Code Flywheel Status Bit
        bit  15    Time Code Reader Status Bit
        bits 16-31 Minor Frame Count
    """
    return {
        "word2_raw": word2,
        "minor_frame_count": (word2 >> 16) & 0x7FFF,
        "bit31_flag": bool((word2 >> 31) & 1),  # constant 1 in observed
                                                 # sample data; meaning
                                                 # undocumented, excluded
                                                 # from minor_frame_count so
                                                 # the mfc==0 major-frame
                                                 # boundary check keeps working
        "current_format_indicator": word2 & 0b111,
        "minor_frame_lock": (word2 >> 3) & 0b11,
        "sub_frame_lock": (word2 >> 5) & 0b11,
        "bit_sync_loop_lock": bool((word2 >> 7) & 1),
        "sync_error_count": (word2 >> 8) & 0b1111,
        "bit_slip": bool((word2 >> 12) & 1),
        "bit_sync_source_external": bool((word2 >> 13) & 1),
        "tc_flywheel_status": bool((word2 >> 14) & 1),
        "tc_reader_status": bool((word2 >> 15) & 1),
    }

def parse_file_header(data: bytes):
    """Parse the 328-byte outer Dewesoft-style header. Returns the raw date
    string found in it (treat with suspicion -- see module docstring)."""
    if len(data) < FILE_HEADER_LEN:
        raise ValueError("File is smaller than the expected 328-byte header.")
    date_str = data[22:44].split(b"\x00")[0].decode("ascii", errors="replace")
    return {"date_str_raw": date_str}

def parse_tad_file(path, year: int = DEFAULT_YEAR,
                    sync_word: bytes = DEFAULT_SYNC_WORD,
                    rec_len: int = None,
                    progress: bool = True) -> pd.DataFrame:
    """
    Parse a .tad file into a pandas DataFrame, one row per minor frame.

    Parameters
    ----------
    path : str or Path
        Path to the .tad file.
    year : int
        Acquisition year, used with the header's day-of-year to build a
        real timestamp. Defaults to 2026. The file's own embedded date
        string is NOT used for this -- see module docstring.
    sync_word : bytes
        4-byte little-endian frame sync pattern. Defaults to 0xFE6B2840.
    rec_len : int, optional
        Minor frame record length in bytes. Auto-detected if not given.
    progress : bool
        Show a tqdm progress bar if tqdm is installed.

    Returns
    -------
    pd.DataFrame with columns:
        timestamp, doy, hour, minute, sec, msec, usec,
        minor_frame_count, word2_raw, current_format_indicator,
        minor_frame_lock, sub_frame_lock, bit_sync_loop_lock,
        sync_error_count, bit_slip, bit_sync_source_external,
        tc_flywheel_status, tc_reader_status, sync_ok,
        data (object column, each entry a uint16 numpy array)
    """
    with open(path, "rb") as f:
        data = f.read()

    header_info = parse_file_header(data)

    if rec_len is None:
        rec_len = detect_record_length(data, sync_word)

    # Data block = everything after the 12-byte header (sync word included
    # as the first 32-bit entry of this block, not separate overhead).
    n_data_words32 = (rec_len - MINOR_FRAME_HEADER_LEN) // 4
    n_data_words16 = n_data_words32 * 2

    body = data[FILE_HEADER_LEN:]
    n_records = len(body) // rec_len
    if n_records == 0:
        raise ValueError("No complete minor frame records found in file.")

    doy = np.zeros(n_records, dtype=np.int16)
    hour = np.zeros(n_records, dtype=np.int8)
    minute = np.zeros(n_records, dtype=np.int8)
    sec = np.zeros(n_records, dtype=np.int8)
    msec = np.zeros(n_records, dtype=np.int16)
    usec = np.zeros(n_records, dtype=np.int16)
    mfc = np.zeros(n_records, dtype=np.int32)
    w2raw = np.zeros(n_records, dtype=np.uint32)
    bit31_flag = np.zeros(n_records, dtype=bool)
    current_format = np.zeros(n_records, dtype=np.uint8)
    minor_frame_lock = np.zeros(n_records, dtype=np.uint8)
    sub_frame_lock = np.zeros(n_records, dtype=np.uint8)
    bsll = np.zeros(n_records, dtype=bool)
    sync_error_count = np.zeros(n_records, dtype=np.uint8)
    bit_slip = np.zeros(n_records, dtype=bool)
    bit_sync_source_ext = np.zeros(n_records, dtype=bool)
    tc_flywheel = np.zeros(n_records, dtype=bool)
    tc_reader = np.zeros(n_records, dtype=bool)
    sync_ok = np.zeros(n_records, dtype=bool)
    dataw = np.zeros((n_records, n_data_words16), dtype=np.uint16)

    iterator = range(n_records)
    if progress:
        try:
            from tqdm import tqdm
            iterator = tqdm(iterator, desc="Parsing minor frames")
        except ImportError:
            pass

    for i in iterator:
        off = i * rec_len
        rec = body[off:off + rec_len]
        if len(rec) < rec_len:
            break  # trailing partial record

        w0, w1, w2 = struct.unpack("<3I", rec[0:12])
        # Sync check: the first 4 bytes of the data block should equal the
        # fixed sync pattern (it's data word[0:2], not separate overhead).
        sync_ok[i] = (rec[12:16] == sync_word)

        d, h, m, s, ms, us = decode_bcd_time(w0, w1)
        doy[i], hour[i], minute[i], sec[i], msec[i], usec[i] = d, h, m, s, ms, us

        status = decode_status_word(w2)
        mfc[i] = status["minor_frame_count"]
        w2raw[i] = status["word2_raw"]
        bit31_flag[i] = status["bit31_flag"]
        current_format[i] = status["current_format_indicator"]
        minor_frame_lock[i] = status["minor_frame_lock"]
        sub_frame_lock[i] = status["sub_frame_lock"]
        bsll[i] = status["bit_sync_loop_lock"]
        sync_error_count[i] = status["sync_error_count"]
        bit_slip[i] = status["bit_slip"]
        bit_sync_source_ext[i] = status["bit_sync_source_external"]
        tc_flywheel[i] = status["tc_flywheel_status"]
        tc_reader[i] = status["tc_reader_status"]

        raw32 = np.frombuffer(rec[12:12 + n_data_words32 * 4], dtype="<u4")
        dataw[i, 0::2] = (raw32 >> 16).astype(np.uint16)
        dataw[i, 1::2] = (raw32 & 0xFFFF).astype(np.uint16)

    # Trim in case the loop broke early on a trailing partial record
    n_valid = i if len(rec) < rec_len else n_records

    base = pd.Timestamp(year=year, month=1, day=1)
    timestamps = base \
      + pd.to_timedelta(doy[:n_valid].astype("int64") - 1, unit="D") \
      + pd.to_timedelta(hour[:n_valid].astype("int64"), unit="h") \
      + pd.to_timedelta(minute[:n_valid].astype("int64"), unit="min") \
      + pd.to_timedelta(sec[:n_valid].astype("int64"), unit="s") \
      + pd.to_timedelta(msec[:n_valid].astype("int64"), unit="ms") \
      + pd.to_timedelta(usec[:n_valid].astype("int64"), unit="us")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "doy": doy[:n_valid],
        "hour": hour[:n_valid],
        "minute": minute[:n_valid],
        "sec": sec[:n_valid],
        "msec": msec[:n_valid],
        "usec": usec[:n_valid],
        "minor_frame_count": mfc[:n_valid],
        "word2_raw": w2raw[:n_valid],
        "bit31_flag": bit31_flag[:n_valid],
        "current_format_indicator": current_format[:n_valid],
        "minor_frame_lock": minor_frame_lock[:n_valid],
        "sub_frame_lock": sub_frame_lock[:n_valid],
        "bit_sync_loop_lock": bsll[:n_valid],
        "sync_error_count": sync_error_count[:n_valid],
        "bit_slip": bit_slip[:n_valid],
        "bit_sync_source_external": bit_sync_source_ext[:n_valid],
        "tc_flywheel_status": tc_flywheel[:n_valid],
        "tc_reader_status": tc_reader[:n_valid],
        "sync_ok": sync_ok[:n_valid],
    })
    df["data"] = list(dataw[:n_valid])

    df.attrs["source_file"] = str(path)
    df.attrs["rec_len"] = rec_len
    df.attrs["n_data_words16"] = n_data_words16
    df.attrs["header_date_str_raw"] = header_info["date_str_raw"]
    df.attrs["sync_word"] = sync_word.hex()

    return df


def _find_major_frame_start(mfc: np.ndarray, minor_frames_per_major_frame: int) -> int:
    """Return the index of the first minor_frame_count == 0, used as the
    start of the first complete major frame. Shared by build_major_frames()
    and build_major_frame_timestamps() so their trimming always matches."""
    start_candidates = np.nonzero(mfc == 0)[0]
    if len(start_candidates) == 0:
        raise ValueError("No minor frame with count == 0 found; cannot "
                          "determine major frame boundaries.")
    return int(start_candidates[0])


def build_major_frames(df: pd.DataFrame, words_per_minor_frame: int = 120,
                        minor_frames_per_major_frame: int = 10) -> np.ndarray:
    """
    Reassemble parsed minor frames into major frame matrices.

    Finds the first minor frame with minor_frame_count == 0 and, from there,
    groups every `minor_frames_per_major_frame` consecutive rows into one
    major frame matrix, dropping any leading rows before the first count==0
    and any trailing rows that don't complete a full group.

    Parameters
    ----------
    df : pd.DataFrame
        Output of parse_tad_file().
    words_per_minor_frame : int
        Expected number of 16-bit words per minor frame (columns). Default 120.
    minor_frames_per_major_frame : int
        Expected number of minor frames per major frame (rows). Default 10.

    Returns
    -------
    np.ndarray of shape (N, minor_frames_per_major_frame, words_per_minor_frame),
    dtype uint16, where N is the number of complete major frames found.
    """
    data = np.stack(df["data"].to_numpy())  # (n_records, words_per_minor_frame)
    if data.shape[1] != words_per_minor_frame:
        raise ValueError(
            f"Each minor frame has {data.shape[1]} words, expected "
            f"{words_per_minor_frame}. Check rec_len / header parsing."
        )

    mfc = df["minor_frame_count"].to_numpy()
    start = _find_major_frame_start(mfc, minor_frames_per_major_frame)

    trimmed = data[start:]
    n_major = trimmed.shape[0] // minor_frames_per_major_frame
    trimmed = trimmed[: n_major * minor_frames_per_major_frame]

    major_frames = trimmed.reshape(
        n_major, minor_frames_per_major_frame, words_per_minor_frame
    )

    # Sanity-check: within each major frame, minor_frame_count should run 0..9
    mfc_trimmed = mfc[start: start + n_major * minor_frames_per_major_frame]
    mfc_grid = mfc_trimmed.reshape(n_major, minor_frames_per_major_frame)
    expected_row = np.arange(minor_frames_per_major_frame)
    bad_rows = np.nonzero(~np.all(mfc_grid == expected_row, axis=1))[0]
    if len(bad_rows) > 0:
        print(f"WARNING: {len(bad_rows)} of {n_major} major frames have a "
              f"non-sequential minor_frame_count (e.g. a dropped/duplicated "
              f"minor frame). Indices: {bad_rows[:10]}"
              f"{'...' if len(bad_rows) > 10 else ''}")

    return major_frames


def build_major_frame_timestamps(df: pd.DataFrame,
                                  minor_frames_per_major_frame: int = 10) -> np.ndarray:
    """
    Companion to build_major_frames(): returns each minor frame's own decoded
    header timestamp (word0/word1), trimmed and reshaped with EXACTLY the
    same alignment as build_major_frames() so major_frame_timestamps[i, r]
    corresponds to major_frames[i, r, :].

    Returns
    -------
    np.ndarray of shape (N, minor_frames_per_major_frame), dtype datetime64.
    """
    mfc = df["minor_frame_count"].to_numpy()
    ts = df["timestamp"].to_numpy()
    start = _find_major_frame_start(mfc, minor_frames_per_major_frame)

    n_major = (len(mfc) - start) // minor_frames_per_major_frame
    trimmed = ts[start: start + n_major * minor_frames_per_major_frame]
    return trimmed.reshape(n_major, minor_frames_per_major_frame)


def word_time_offset_sec(col: int) -> float:
    """
    Seconds after a minor frame's header timestamp that word `col` (0-indexed
    within the 120-word data block) would occur, ASSUMING a fixed word rate
    derived from BIT_RATE_BPS. Kept for reference/fallback use, but
    extract_instrument_stream() no longer uses this directly -- see
    compute_row_periods_sec() below for why.
    """
    return col * TIME_PER_WORD_SEC


def compute_row_periods_sec(major_frame_timestamps: np.ndarray) -> np.ndarray:
    """
    For each (major_frame, row) minor frame, compute the REAL observed
    duration until the next minor frame's header timestamp -- using the
    actual decoded timestamps rather than an assumed constant bit rate.

    Why this matters: real hardware timing has jitter (clock jitter, and
    +/-1us quantization from the microsecond-only BCD timestamp
    resolution). If word-level offsets within a row are computed from a
    fixed nominal period (col * TIME_PER_WORD_SEC), a late-column word's
    synthetic offset can exceed the row's REAL duration whenever jitter
    makes that particular gap shorter than nominal -- causing its
    timestamp to land after the next row's real start time ("temporal
    overlap"). Scaling each word's offset to that row's own real duration
    instead makes this impossible by construction: the last word's offset
    is always strictly less than the real gap to the next row.

    Returns
    -------
    np.ndarray, same shape as major_frame_timestamps (N, minor_frames_per_major_frame),
    dtype float64, seconds until the NEXT minor frame in the real
    chronological sequence (wrapping across major-frame boundaries). The
    very last entry in the whole array (which has no "next" frame) reuses
    the previous gap as an estimate.
    """
    flat = major_frame_timestamps.reshape(-1)
    diffs = np.diff(flat) / np.timedelta64(1, "s")
    periods = np.empty(flat.shape[0], dtype=np.float64)
    periods[:-1] = diffs
    periods[-1] = diffs[-1] if len(diffs) > 0 else (120 * TIME_PER_WORD_SEC)
    return periods.reshape(major_frame_timestamps.shape)


def extract_instrument_stream(major_frames: np.ndarray,
                               major_frame_timestamps: np.ndarray,
                               column, rows=None) -> pd.DataFrame:
    """
    Pull a subcommutated instrument's samples out of major_frames and give
    each sample its own precisely computed timestamp.

    Word-level timestamps are computed as a FRACTION of each row's REAL
    observed duration (col / words_per_minor_frame * real_row_period), not
    a fixed nominal word period -- see compute_row_periods_sec() for why.
    This guarantees a word can never be timestamped past its own row's
    real time window, avoiding overlap with the next minor frame even in
    the presence of timing jitter.

    In OCHRE, instrument identity is fixed by COLUMN alone: whatever
    instrument lives at column c within a minor frame lives there in every
    minor frame, forever. Subcommutation means that instrument's data is
    only valid on certain minor-frame rows (0-9) within each 10-row major
    frame cycle -- other rows at that column belong to other instruments
    that share the slot on a rotating basis.

    Parameters
    ----------
    major_frames : np.ndarray, shape (N, minor_frames_per_major_frame, words_per_minor_frame)
        Output of build_major_frames().
    major_frame_timestamps : np.ndarray, shape (N, minor_frames_per_major_frame)
        Output of build_major_frame_timestamps(), from the SAME df/call so
        the two arrays line up row-for-row.
    column : int or list[int]
        Word column(s) (0-119) that belong to this instrument. Pass a list
        if the instrument spans multiple word columns (e.g. a multi-word
        value); their samples are merged into one time-ordered series.
    rows : None, list[int], or list[list[int]], optional
        Which minor-frame rows (0-9) this instrument's column is valid on.
        - None (default): assume the column is valid on every row (fully
          commutated, not subcommutated).
        - list[int]: the same set of valid rows applies to every column
          given.
        - list[list[int]]: one row-list per column, same order as `column`,
          for instruments whose different word columns are subcommutated
          on different row schedules.

    Returns
    -------
    pd.DataFrame with columns:
        timestamp, value, column, row, major_frame_index
        sorted by timestamp.
    """
    n_major, rows_per_major, cols = major_frames.shape
    if major_frame_timestamps.shape != (n_major, rows_per_major):
        raise ValueError(
            "major_frame_timestamps shape must match major_frames' first "
            "two dimensions -- make sure both came from the same df."
        )

    row_periods = compute_row_periods_sec(major_frame_timestamps)  # (N, rows_per_major)

    columns = [column] if isinstance(column, int) else list(column)

    if rows is None:
        row_sets = [list(range(rows_per_major))] * len(columns)
    elif len(rows) > 0 and isinstance(rows[0], int):
        row_sets = [list(rows)] * len(columns)
    else:
        row_sets = list(rows)
        if len(row_sets) != len(columns):
            raise ValueError("When `rows` is a list of lists, it must have "
                              "one entry per entry in `column`.")

    frames = []
    for col, valid_rows in zip(columns, row_sets):
        if not (0 <= col < cols):
            raise ValueError(f"column {col} out of range 0-{cols - 1}")
        frac = col / cols  # fraction of the row's real duration

        for row in valid_rows:
            if not (0 <= row < rows_per_major):
                raise ValueError(f"row {row} out of range 0-{rows_per_major - 1}")

            values = major_frames[:, row, col]            # (N,)
            base_times = major_frame_timestamps[:, row]   # (N,) datetime64
            offset_sec = frac * row_periods[:, row]        # (N,) -- real, per-row
            offset = pd.to_timedelta(offset_sec, unit="s")
            times = base_times + offset

            frames.append(pd.DataFrame({
                "timestamp": times,
                "value": values,
                "column": col,
                "row": row,
                "major_frame_index": np.arange(n_major),
            }))

    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values("timestamp", kind="stable").reset_index(drop=True)
    return out


if __name__ == "__main__":

    files = glob.glob(ProcessingClass.DIR +'/tad/' + ProcessingClass.SOURCE + '/*.tad*')

    if justPrintFileNames:
        if len(files) == 0:
            raise Exception(f"There are no files in the directory ({ProcessingClass.DIR+ProcessingClass.SOURCE})")
        else:
            for idx, thing in enumerate(files):
                print(f'[{idx}] {os.path.basename(thing)}')
    else:

        import sys
        tad_path = files[wFile]
        yr = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_YEAR

        df = parse_tad_file(tad_path, year=yr) # run the main function to get the data
        major_frames = build_major_frames(df)
        major_frame_ts = build_major_frame_timestamps(df)  # (N, 10) array, aligned
                                                             # with major_frames --
                                                             # NOT the same as
                                                             # df['timestamp']

        instr_dict = {instr: ProcessingClass.instr_dict[instr] for instr in wInstrs}


        # print out some status words
        print(f"\nParsed {len(df)} minor frames from {tad_path}")
        print(f"Record length: {df.attrs['rec_len']} bytes  "
              f"| Data words/frame: {df.attrs['n_data_words16']}  "
              f"| Sync word: {df.attrs['sync_word']}")
        print(f"Header date string (unreliable, see docstring): "
              f"{df.attrs['header_date_str_raw']!r}")
        print(f"Sync errors: {(~df['sync_ok']).sum()} / {len(df)}")
        print(f"Time range: {df['timestamp'].iloc[0]} -> {df['timestamp'].iloc[-1]}")
        # print(df.drop(columns=["data"]).head())
        print(f"\nMajor frames array shape: {major_frames.shape}  dtype={major_frames.dtype}")

        # --- Rip out individual instrument data ---
        for instr,words_dict in instr_dict.items():

            stl.prgMsg(f'Extracting {instr} data')

            # --- get the raw instrument data ---
            data = extract_instrument_stream(major_frames=major_frames,
                                      major_frame_timestamps=major_frame_ts,
                                      rows=words_dict['rows'],
                                      column=np.array(words_dict['cols'])+1
                                             )

            # store result as .cdf file
            data['timestamp'] = pd.to_datetime(data['timestamp'])  # parses the ISO strings
            epoch_pydt = data['timestamp'].dt.to_pydatetime()  # -> array of datetime.datetime
            epoch_pydt = np.asarray(epoch_pydt, dtype=object)  # plain object ndarray


            data_dict_output = {
                'epoch':[epoch_pydt,{'VAR_TYPE':'support_data'}],
                f'{instr}_all_words': [data['value'].to_numpy(),{'DEPEND_0':'epoch','VAR_TYPE':'data'}] ,
                'major_frame_idx':[data['major_frame_index'].to_numpy(),{'DEPEND_0':'epoch','VAR_TYPE':'support_data'}],
                'minor_frame_idx': [data['row'].to_numpy(), {'DEPEND_0': 'epoch', 'VAR_TYPE': 'support_data'}],
            }

            file_tag = os.path.basename(tad_path).replace(".tad","").replace('OCHRE_','')
            file_name = f'OCHRE_52012_{instr}_l0_{file_tag}.cdf'
            outputFilePath = f'C:/Users/cfelt/OneDrive - University of Iowa/rockets/OCHRE/data/INT/L0/{instr}/{file_name}'
            if outputData:
                stl.outputDataDict(outputPath=outputFilePath,
                                   data_dict=data_dict_output)
            stl.Done(start_time)