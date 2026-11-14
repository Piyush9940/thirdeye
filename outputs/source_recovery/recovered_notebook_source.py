# RECOVERED SOURCE ARCHIVE
# Source: model.ipynb
# This is an archival export, not a standalone executable script.
# Jupyter magics and notebook-dependent variables may remain.
# Review credentials and paths before sharing or committing.


# ============================================================
# ORIGINAL NOTEBOOK CELL 0
# Execution count: 1
# ============================================================

%pip install -q numpy pandas requests xarray netCDF4 scipy scikit-learn matplotlib seaborn pyarrow joblib tqdm statsmodels


# ============================================================
# ORIGINAL NOTEBOOK CELL 1
# Execution count: 2
# ============================================================


from pathlib import Path
from io import BytesIO
import json
import time
import random
import warnings
import zipfile

import requests
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

from scipy.stats import kendalltau, theilslopes
from sklearn.neighbors import BallTree
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.stats.multitest import multipletests

import torch
import torch.nn as nn
import torch.nn.functional as F

from torch.utils.data import Dataset, DataLoader
from tqdm.auto import tqdm
import joblib

warnings.filterwarnings("ignore")

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

PROJECT_ROOT = Path.cwd()

if PROJECT_ROOT.name.lower() == "notebooks":
    PROJECT_ROOT = PROJECT_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "nasa_power"
PROCESSED_DIR = DATA_DIR / "processed"

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "model_training"
MODEL_DIR = OUTPUT_DIR / "models"
PREDICTION_DIR = OUTPUT_DIR / "predictions"
REPORT_DIR = OUTPUT_DIR / "reports"

for folder in [
    RAW_DIR, PROCESSED_DIR, MODEL_DIR,
    PREDICTION_DIR, REPORT_DIR
]:
    folder.mkdir(parents=True, exist_ok=True)

print("Project:", PROJECT_ROOT)
print("Device:", DEVICE)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))


# ============================================================
# ORIGINAL NOTEBOOK CELL 2
# Execution count: 5
# ============================================================


# ============================================================
# CELL 3: NASA POWER DATASET CONFIGURATION
# Earth Systems Trend Detective
# ============================================================

from pathlib import Path

# NASA POWER Monthly Regional API
NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/monthly/regional"
)

# ------------------------------------------------------------
# GEOGRAPHICAL REGION: INDIA
# ------------------------------------------------------------

LAT_MIN = 6
LAT_MAX = 38

LON_MIN = 68
LON_MAX = 98

# ------------------------------------------------------------
# TEMPORAL CONFIGURATION
# ------------------------------------------------------------

START_YEAR = 2015
END_YEAR = 2024

# ------------------------------------------------------------
# NASA POWER COMMUNITY
# ------------------------------------------------------------

COMMUNITY = "AG"

# ------------------------------------------------------------
# PARAMETERS TO DOWNLOAD
# ------------------------------------------------------------

PARAMETERS = [
    "T2M",           # Temperature at 2 meters (°C)
    "PRECTOTCORR",   # Corrected precipitation (mm/day)
    "RH2M",          # Relative humidity (%)
    "WS10M"          # Wind speed at 10 meters (m/s)
]

# ------------------------------------------------------------
# PROJECT DIRECTORIES
# ------------------------------------------------------------

PROJECT_ROOT = Path.cwd()

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "nasa_power"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "model_training"

# Create directories
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# DISPLAY CONFIGURATION
# ------------------------------------------------------------

print("=" * 65)
print("NASA POWER DATASET CONFIGURATION")
print("=" * 65)

print(f"Project root : {PROJECT_ROOT}")
print(f"Raw data     : {RAW_DIR}")
print(f"Processed    : {PROCESSED_DIR}")
print(f"Output       : {OUTPUT_DIR}")

print("\nGeographical region:")
print(f"Latitude     : {LAT_MIN} to {LAT_MAX}")
print(f"Longitude    : {LON_MIN} to {LON_MAX}")

print("\nTemporal range:")
print(f"Start year   : {START_YEAR}")
print(f"End year     : {END_YEAR}")

print("\nParameters:")
for parameter in PARAMETERS:
    print(" -", parameter)

print("\nConfiguration completed successfully.")


# ============================================================
# ORIGINAL NOTEBOOK CELL 3
# Execution count: 7
# ============================================================

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "nasa_power"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "model_training"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ORIGINAL NOTEBOOK CELL 4
# Execution count: 8
# ============================================================


# ============================================================
# CELL 4A: NASA POWER API DIAGNOSTIC TEST
# ============================================================

import requests

test_params = {
    "latitude-min": 12,
    "latitude-max": 16,
    "longitude-min": 76,
    "longitude-max": 80,
    "parameters": "T2M",
    "community": "AG",
    "start": 2015,
    "end": 2024,
    "format": "NetCDF"
}

try:
    response = requests.get(
        NASA_POWER_URL,
        params=test_params,
        headers={
            "User-Agent": "Earth-Systems-Trend-Detective/1.0"
        },
        timeout=180
    )

    print("HTTP Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print("Response size:", len(response.content), "bytes")
    print("\nResponse preview:")

    if response.ok:
        print("Request successful.")
        print("First 16 bytes:", response.content[:16])
    else:
        print(response.text[:3000])

except requests.RequestException as error:
    print("Connection error:", error)


# ============================================================
# ORIGINAL NOTEBOOK CELL 5
# Execution count: 10
# ============================================================


import requests

url = "https://power.larc.nasa.gov/api/temporal/monthly/regional"

test_cases = [
    {
        "name": "AG community",
        "community": "AG"
    },
    {
        "name": "RE community",
        "community": "RE"
    }
]

for test in test_cases:

    params = {
        "latitude-min": 12,
        "latitude-max": 16,
        "longitude-min": 76,
        "longitude-max": 80,
        "parameters": "T2M",
        "community": test["community"],
        "start": 2015,
        "end": 2024,
        "format": "JSON"
    }

    print("\n" + "=" * 65)
    print("TEST:", test["name"])
    print("=" * 65)

    try:
        response = requests.get(
            url,
            params=params,
            timeout=120
        )

        print("Status:", response.status_code)
        print("URL:", response.url)
        print("Content-Type:", response.headers.get("Content-Type"))
        print("Response:")
        print(response.text[:4000])

    except Exception as error:
        print("Request failed:", repr(error))


# ============================================================
# ORIGINAL NOTEBOOK CELL 6
# Execution count: 11
# ============================================================


# ============================================================
# CELL 4B: TEST NASA POWER OUTPUT FORMATS
# ============================================================

import requests

url = "https://power.larc.nasa.gov/api/temporal/monthly/regional"

base_params = {
    "latitude-min": 12,
    "latitude-max": 16,
    "longitude-min": 76,
    "longitude-max": 80,
    "parameters": "T2M",
    "community": "AG",
    "start": 2015,
    "end": 2024
}

for output_format in ["JSON", "NetCDF", "CSV"]:

    params = {
        **base_params,
        "format": output_format
    }

    print("\n" + "=" * 60)
    print("TESTING FORMAT:", output_format)
    print("=" * 60)

    try:
        response = requests.get(
            url,
            params=params,
            timeout=180
        )

        print("HTTP Status:", response.status_code)
        print("Content-Type:", response.headers.get("Content-Type"))
        print("File size:", len(response.content), "bytes")

        if response.status_code == 200:
            print("SUCCESS")

            if output_format == "JSON":
                print(response.text[:300])

            else:
                print("First 16 bytes:", response.content[:16])

        else:
            print("ERROR RESPONSE:")
            print(response.text[:2000])

    except Exception as error:
        print("Request error:", repr(error))


# ============================================================
# ORIGINAL NOTEBOOK CELL 7
# Execution count: 12
# ============================================================


# ============================================================
# CELL 4: INDIA-WIDE NASA POWER TILED NETCDF DOWNLOADER
# Earth Systems Trend Detective
# ============================================================

import requests
import time
import zipfile
import xarray as xr
import numpy as np

from io import BytesIO
from pathlib import Path

# ------------------------------------------------------------
# VERIFY PROJECT DIRECTORIES
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "nasa_power"
TILE_DIR = RAW_DIR / "tiles"

RAW_DIR.mkdir(parents=True, exist_ok=True)
TILE_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# API CONFIGURATION
# ------------------------------------------------------------

NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/monthly/regional"
)

# Tile size kept below the commonly documented
# approximate 4.5 degree regional area limit.
TILE_SIZE = 4.0

MAX_RETRIES = 3
REQUEST_TIMEOUT = 180

# ------------------------------------------------------------
# GENERATE GEOGRAPHICAL TILES
# ------------------------------------------------------------

def generate_tiles():

    tiles = []

    lat_edges = np.arange(
        LAT_MIN,
        LAT_MAX,
        TILE_SIZE
    )

    lon_edges = np.arange(
        LON_MIN,
        LON_MAX,
        TILE_SIZE
    )

    for lat_min in lat_edges:

        lat_max = min(
            lat_min + TILE_SIZE,
            LAT_MAX
        )

        for lon_min in lon_edges:

            lon_max = min(
                lon_min + TILE_SIZE,
                LON_MAX
            )

            tiles.append({
                "lat_min": float(lat_min),
                "lat_max": float(lat_max),
                "lon_min": float(lon_min),
                "lon_max": float(lon_max)
            })

    return tiles


tiles = generate_tiles()

print("=" * 65)
print("NASA POWER TILED DOWNLOAD")
print("=" * 65)

print("Number of geographical tiles:", len(tiles))
print("Tile size:", TILE_SIZE, "degrees")
print("Parameters:", PARAMETERS)

# ------------------------------------------------------------
# NETCDF RESPONSE VALIDATION
# ------------------------------------------------------------

def extract_netcdf(content):

    if zipfile.is_zipfile(BytesIO(content)):

        with zipfile.ZipFile(BytesIO(content)) as archive:

            nc_files = [
                name for name in archive.namelist()
                if name.lower().endswith((".nc", ".nc4"))
            ]

            if not nc_files:
                raise ValueError(
                    "ZIP response contains no NetCDF file."
                )

            content = archive.read(nc_files[0])

    valid_signature = (
        content.startswith(b"CDF")
        or content.startswith(b"\x89HDF\r\n\x1a\n")
    )

    if not valid_signature:

        preview = content[:1000].decode(
            "utf-8",
            errors="replace"
        )

        raise ValueError(
            "Invalid NetCDF response: " + preview
        )

    return content


# ------------------------------------------------------------
# DOWNLOAD ONE TILE
# ------------------------------------------------------------

def download_one_tile(parameter, tile, tile_number):

    params = {
        "latitude-min": tile["lat_min"],
        "latitude-max": tile["lat_max"],
        "longitude-min": tile["lon_min"],
        "longitude-max": tile["lon_max"],
        "parameters": parameter,
        "community": COMMUNITY,
        "start": START_YEAR,
        "end": END_YEAR,
        "format": "NetCDF"
    }

    filename = (
        f"{parameter}_tile_{tile_number:03d}.nc"
    )

    output_path = TILE_DIR / filename

    # Reuse existing validated tile files.
    if output_path.exists():

        try:
            with xr.open_dataset(output_path) as ds:
                ds.load()

            print("Using cached tile:", filename)
            return output_path

        except Exception:
            output_path.unlink()

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = requests.get(
                NASA_POWER_URL,
                params=params,
                headers={
                    "User-Agent": "Earth-Systems-Trend-Detective/1.0"
                },
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 422:

                raise ValueError(
                    "NASA POWER rejected tile. "
                    "HTTP 422 response: "
                    + response.text[:1500]
                )

            response.raise_for_status()

            content = extract_netcdf(response.content)

            output_path.write_bytes(content)

            # Confirm the file can be opened.
            with xr.open_dataset(output_path) as ds:
                ds.load()

            print(
                f"Downloaded {parameter} "
                f"tile {tile_number}/{len(tiles)} "
                f"({len(content) / 1024:.1f} KB)"
            )

            time.sleep(0.5)

            return output_path

        except Exception as error:

            print(
                f"Failed {parameter}, tile {tile_number}, "
                f"attempt {attempt}/{MAX_RETRIES}: {error}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(attempt * 5)

    raise RuntimeError(
        f"Could not download {parameter}, tile {tile_number}"
    )


# ------------------------------------------------------------
# MERGE NETCDF TILES
# ------------------------------------------------------------

def merge_tiles(parameter, tile_paths):

    datasets = []

    try:

        for path in tile_paths:

            ds = xr.open_dataset(path)
            ds.load()
            datasets.append(ds)

        print(
            f"\nMerging {len(datasets)} tiles for {parameter}..."
        )

        combined = xr.combine_by_coords(
            datasets,
            combine_attrs="drop_conflicts"
        )

        # Remove duplicate coordinate values if any occur.
        for coord in ["lat", "latitude", "lon", "longitude"]:

            if coord in combined.coords:

                values = combined[coord].values

                if len(np.unique(values)) != len(values):

                    _, unique_indices = np.unique(
                        values,
                        return_index=True
                    )

                    combined = combined.isel({
                        coord: np.sort(unique_indices)
                    })

        output_path = RAW_DIR / (
            f"{parameter}_{START_YEAR}_{END_YEAR}.nc"
        )

        encoding = {}

        for variable in combined.data_vars:

            if np.issubdtype(
                combined[variable].dtype,
                np.floating
            ):

                encoding[variable] = {
                    "zlib": True,
                    "complevel": 4
                }

        combined.to_netcdf(
            output_path,
            encoding=encoding
        )

        print("Merged file saved:", output_path)

        print("Dimensions:", dict(combined.sizes))

        return output_path

    finally:

        for ds in datasets:
            ds.close()


# ------------------------------------------------------------
# DOWNLOAD ALL PARAMETERS
# ------------------------------------------------------------

downloaded_files = {}

for parameter in PARAMETERS:

    print("\n" + "=" * 65)
    print("PROCESSING PARAMETER:", parameter)
    print("=" * 65)

    parameter_tile_paths = []

    for tile_number, tile in enumerate(tiles, start=1):

        path = download_one_tile(
            parameter,
            tile,
            tile_number
        )

        parameter_tile_paths.append(path)

    merged_path = merge_tiles(
        parameter,
        parameter_tile_paths
    )

    downloaded_files[parameter] = merged_path


# ------------------------------------------------------------
# FINAL DOWNLOAD SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 65)
print("NASA POWER DOWNLOAD COMPLETED")
print("=" * 65)

for parameter, path in downloaded_files.items():

    print(
        parameter,
        "->",
        path,
        f"({path.stat().st_size / (1024 * 1024):.2f} MB)"
    )

print("\nAll parameter files are ready.")


# ============================================================
# ORIGINAL NOTEBOOK CELL 8
# Execution count: 13
# ============================================================


# ============================================================
# CELL 5: NETCDF INSPECTION AND DATAFRAME CONVERSION
# Earth Systems Trend Detective
# ============================================================

import xarray as xr
import pandas as pd
import numpy as np

from pathlib import Path

# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "nasa_power"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# CHECK DOWNLOADED FILES
# ------------------------------------------------------------

print("=" * 70)
print("NASA POWER NETCDF FILE INSPECTION")
print("=" * 70)

for parameter in PARAMETERS:

    file_path = RAW_DIR / (
        f"{parameter}_{START_YEAR}_{END_YEAR}.nc"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Missing dataset: {file_path}"
        )

    print(
        f"{parameter}: "
        f"{file_path.stat().st_size / (1024 * 1024):.2f} MB"
    )


# ------------------------------------------------------------
# DETECT COORDINATE NAMES
# ------------------------------------------------------------

def find_coordinate(dataset, possible_names):

    for name in possible_names:

        if name in dataset.coords:
            return name

        if name in dataset.dims:
            return name

    return None


# ------------------------------------------------------------
# CONVERT TIME VALUES
# ------------------------------------------------------------

def normalize_time_column(df):

    if "time" not in df.columns:
        raise ValueError(
            "No time column found in the NetCDF dataset."
        )

    original = df["time"]

    # Already datetime
    if pd.api.types.is_datetime64_any_dtype(original):

        df["time"] = pd.to_datetime(
            original,
            errors="coerce"
        )

    else:

        # Handle numeric or string YYYYMM values.
        values = original.astype(str).str.strip()

        parsed = pd.to_datetime(
            values,
            format="%Y%m",
            errors="coerce"
        )

        # Handle standard date strings.
        if parsed.notna().sum() == 0:

            parsed = pd.to_datetime(
                values,
                errors="coerce"
            )

        df["time"] = parsed

    # Remove unparseable dates.
    df = df.dropna(subset=["time"]).copy()

    # Keep monthly records only.
    df = df[df["time"].dt.month.between(1, 12)].copy()

    return df


# ------------------------------------------------------------
# CONVERT ONE NETCDF FILE TO DATAFRAME
# ------------------------------------------------------------

def netcdf_to_dataframe(parameter):

    file_path = RAW_DIR / (
        f"{parameter}_{START_YEAR}_{END_YEAR}.nc"
    )

    print("\n" + "=" * 70)
    print("PROCESSING:", parameter)
    print("=" * 70)

    # Open NetCDF
    try:
        dataset = xr.open_dataset(file_path)

    except Exception as error:
        raise RuntimeError(
            f"Could not open {file_path}: {error}"
        )

    print("\nDataset metadata:")
    print(dataset)

    print("\nCoordinates:", list(dataset.coords))
    print("Dimensions:", list(dataset.dims))
    print("Data variables:", list(dataset.data_vars))

    # Detect coordinate names
    latitude_name = find_coordinate(
        dataset,
        ["lat", "latitude", "y"]
    )

    longitude_name = find_coordinate(
        dataset,
        ["lon", "longitude", "x"]
    )

    time_name = find_coordinate(
        dataset,
        ["time", "date", "datetime"]
    )

    if not latitude_name:
        raise ValueError(
            f"Latitude coordinate not found in {parameter}"
        )

    if not longitude_name:
        raise ValueError(
            f"Longitude coordinate not found in {parameter}"
        )

    if not time_name:
        raise ValueError(
            f"Time coordinate not found in {parameter}"
        )

    # Find parameter variable
    if parameter in dataset.data_vars:
        variable_name = parameter

    elif len(dataset.data_vars) == 1:
        variable_name = list(dataset.data_vars)[0]

    else:
        raise ValueError(
            f"Could not identify {parameter} data variable. "
            f"Available: {list(dataset.data_vars)}"
        )

    print("\nSelected variable:", variable_name)
    print("Latitude coordinate:", latitude_name)
    print("Longitude coordinate:", longitude_name)
    print("Time coordinate:", time_name)

    # Convert selected variable to DataFrame
    variable = dataset[variable_name]

    dataframe = variable.to_dataframe(
        name=parameter
    ).reset_index()

    # Normalize column names
    dataframe = dataframe.rename(
        columns={
            latitude_name: "latitude",
            longitude_name: "longitude",
            time_name: "time"
        }
    )

    # Normalize time
    dataframe = normalize_time_column(dataframe)

    # Ensure numeric coordinates and values
    dataframe["latitude"] = pd.to_numeric(
        dataframe["latitude"],
        errors="coerce"
    )

    dataframe["longitude"] = pd.to_numeric(
        dataframe["longitude"],
        errors="coerce"
    )

    dataframe[parameter] = pd.to_numeric(
        dataframe[parameter],
        errors="coerce"
    )

    dataframe = dataframe.dropna(
        subset=[
            "latitude",
            "longitude",
            "time"
        ]
    )

    # Restrict to requested geographical region
    dataframe = dataframe[
        dataframe["latitude"].between(LAT_MIN, LAT_MAX)
        & dataframe["longitude"].between(LON_MIN, LON_MAX)
    ].copy()

    # Remove duplicate spatial-temporal records
    dataframe = dataframe.drop_duplicates(
        subset=[
            "time",
            "latitude",
            "longitude"
        ]
    )

    dataframe = dataframe.sort_values(
        ["time", "latitude", "longitude"]
    ).reset_index(drop=True)

    dataset.close()

    print("\nConverted DataFrame:")
    print("Rows:", len(dataframe))
    print("Columns:", list(dataframe.columns))
    print("Time range:", dataframe["time"].min(),
          "to", dataframe["time"].max())

    print("\nSample records:")
    print(dataframe.head())

    return dataframe


# ------------------------------------------------------------
# CONVERT ALL PARAMETERS
# ------------------------------------------------------------

parameter_dataframes = {}

for parameter in PARAMETERS:

    parameter_dataframes[parameter] = (
        netcdf_to_dataframe(parameter)
    )


# ------------------------------------------------------------
# MERGE ALL PARAMETERS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("MERGING NASA POWER PARAMETERS")
print("=" * 70)

model_dataset = parameter_dataframes[PARAMETERS[0]].copy()

for parameter in PARAMETERS[1:]:

    model_dataset = model_dataset.merge(
        parameter_dataframes[parameter],
        on=[
            "time",
            "latitude",
            "longitude"
        ],
        how="outer"
    )


# ------------------------------------------------------------
# SORT AND SAVE
# ------------------------------------------------------------

model_dataset = model_dataset.sort_values(
    ["time", "latitude", "longitude"]
).reset_index(drop=True)

output_path = (
    PROCESSED_DIR / "nasa_power_merged.parquet"
)

model_dataset.to_parquet(
    output_path,
    index=False
)

print("\n" + "=" * 70)
print("NASA POWER CONVERSION COMPLETED")
print("=" * 70)

print("Final shape:", model_dataset.shape)
print("Parameters:", PARAMETERS)
print("Unique timestamps:", model_dataset["time"].nunique())
print("Unique locations:", model_dataset[
    ["latitude", "longitude"]
].drop_duplicates().shape[0])

print("\nMissing values:")
print(model_dataset.isna().sum())

print("\nFinal sample:")
print(model_dataset.head(10))

print("\nSaved:", output_path)


# ============================================================
# ORIGINAL NOTEBOOK CELL 9
# Execution count: 14
# ============================================================


# ============================================================
# CELL 6: SPATIAL GRID AGGREGATION (2° x 2°)
# Earth Systems Trend Detective
# ============================================================

import pandas as pd
import numpy as np
from pathlib import Path

# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = PROCESSED_DIR / "nasa_power_merged.parquet"

OUTPUT_FILE = (
    PROCESSED_DIR / "nasa_power_grid_2deg.parquet"
)

GRID_SIZE = 2.0

FEATURES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

# ------------------------------------------------------------
# 2. LOAD MERGED DATASET
# ------------------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Cell 5 output not found: {INPUT_FILE}"
    )

df = pd.read_parquet(INPUT_FILE)

print("=" * 70)
print("SPATIAL GRID AGGREGATION")
print("=" * 70)

print("Original shape:", df.shape)
print("Available columns:", list(df.columns))

# ------------------------------------------------------------
# 3. VALIDATE REQUIRED COLUMNS
# ------------------------------------------------------------

required_columns = [
    "time",
    "latitude",
    "longitude"
] + FEATURES

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

df["time"] = pd.to_datetime(
    df["time"],
    errors="coerce"
)

for column in ["latitude", "longitude"] + FEATURES:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

df = df.dropna(
    subset=["time", "latitude", "longitude"]
).copy()

# ------------------------------------------------------------
# 4. FILTER GEOGRAPHICAL REGION
# ------------------------------------------------------------

df = df[
    df["latitude"].between(LAT_MIN, LAT_MAX)
    & df["longitude"].between(LON_MIN, LON_MAX)
].copy()

if df.empty:
    raise ValueError(
        "No observations found inside the configured region."
    )

print("\nObservations after geographic filtering:", len(df))

# ------------------------------------------------------------
# 5. ASSIGN SPATIAL GRID INDICES
# ------------------------------------------------------------

df["grid_lat"] = np.floor(
    (df["latitude"] - LAT_MIN) / GRID_SIZE
).astype(int)

df["grid_lon"] = np.floor(
    (df["longitude"] - LON_MIN) / GRID_SIZE
).astype(int)

# Calculate center coordinates for each grid cell.
df["grid_latitude"] = (
    LAT_MIN
    + df["grid_lat"] * GRID_SIZE
    + GRID_SIZE / 2
)

df["grid_longitude"] = (
    LON_MIN
    + df["grid_lon"] * GRID_SIZE
    + GRID_SIZE / 2
)

# ------------------------------------------------------------
# 6. AGGREGATE MONTHLY OBSERVATIONS
# ------------------------------------------------------------

group_columns = [
    "time",
    "grid_lat",
    "grid_lon",
    "grid_latitude",
    "grid_longitude"
]

grid_dataset = (
    df.groupby(group_columns, as_index=False)[FEATURES]
    .mean()
)

# ------------------------------------------------------------
# 7. CREATE UNIQUE SPATIAL NODE IDs
# ------------------------------------------------------------

grid_dataset["node_id"] = (
    grid_dataset["grid_lat"].astype(str)
    + "_"
    + grid_dataset["grid_lon"].astype(str)
)

# Sort observations.
grid_dataset = grid_dataset.sort_values(
    ["time", "node_id"]
).reset_index(drop=True)

# ------------------------------------------------------------
# 8. DATA QUALITY REPORT
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("GRID AGGREGATION REPORT")
print("=" * 70)

print("Original observations:", len(df))
print("Aggregated observations:", len(grid_dataset))

print(
    "Unique spatial cells:",
    grid_dataset["node_id"].nunique()
)

print(
    "Unique months:",
    grid_dataset["time"].nunique()
)

print(
    "Date range:",
    grid_dataset["time"].min(),
    "to",
    grid_dataset["time"].max()
)

print("\nMissing values:")
print(grid_dataset[FEATURES].isna().sum())

print("\nFeature statistics:")
print(grid_dataset[FEATURES].describe())

# ------------------------------------------------------------
# 9. SAVE GRID DATASET
# ------------------------------------------------------------

grid_dataset.to_parquet(
    OUTPUT_FILE,
    index=False
)

print("\nSaved successfully:")
print(OUTPUT_FILE)

print("\nSample records:")
print(grid_dataset.head(10))

print("\nCell 6 completed successfully.")


# ============================================================
# ORIGINAL NOTEBOOK CELL 10
# Execution count: 15
# ============================================================


# ============================================================
# CELL 7: SPATIAL AND TEMPORAL DATA QUALITY VALIDATION
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ------------------------------------------------------------
# 1. PATHS AND CONFIGURATION
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "nasa_power_grid_2deg.parquet"
)

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "data_quality"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

# ------------------------------------------------------------
# 2. LOAD AGGREGATED DATA
# ------------------------------------------------------------

df = pd.read_parquet(INPUT_FILE)

df["time"] = pd.to_datetime(df["time"])

print("=" * 70)
print("CELL 7: DATA QUALITY VALIDATION")
print("=" * 70)

print("\nDataset shape:", df.shape)
print("\nColumns:", df.columns.tolist())

# ------------------------------------------------------------
# 3. CHECK DUPLICATE RECORDS
# ------------------------------------------------------------

duplicate_count = df.duplicated(
    subset=["time", "node_id"]
).sum()

print("\nDuplicate time-node records:", duplicate_count)

# ------------------------------------------------------------
# 4. CHECK MONTHLY COVERAGE
# ------------------------------------------------------------

expected_months = pd.date_range(
    start="2015-01-01",
    end="2024-12-01",
    freq="MS"
)

actual_months = pd.DatetimeIndex(
    sorted(df["time"].dropna().unique())
)

missing_months = expected_months.difference(actual_months)

print("\nExpected months:", len(expected_months))
print("Available months:", len(actual_months))
print("Missing months:", len(missing_months))

if len(missing_months) > 0:
    print("Missing month values:", missing_months.tolist())

# ------------------------------------------------------------
# 5. CHECK MONTHLY COVERAGE FOR EACH SPATIAL CELL
# ------------------------------------------------------------

coverage = (
    df.groupby("node_id")["time"]
    .nunique()
    .rename("available_months")
    .reset_index()
)

coverage["missing_months"] = (
    len(expected_months) - coverage["available_months"]
)

print("\nSpatial cell coverage:")
print(coverage["available_months"].describe())

incomplete_nodes = coverage[
    coverage["available_months"] != len(expected_months)
]

print("\nTotal spatial cells:", len(coverage))
print("Complete spatial cells:", len(coverage) - len(incomplete_nodes))
print("Incomplete spatial cells:", len(incomplete_nodes))

# ------------------------------------------------------------
# 6. CHECK FEATURE MISSINGNESS
# ------------------------------------------------------------

missing_report = pd.DataFrame({
    "missing_count": df[FEATURES].isna().sum(),
    "missing_percentage": (
        df[FEATURES].isna().mean() * 100
    )
})

print("\nFeature missingness:")
print(missing_report)

# ------------------------------------------------------------
# 7. FEATURE STATISTICS
# ------------------------------------------------------------

print("\nFeature statistics:")
print(df[FEATURES].describe().round(3))

# ------------------------------------------------------------
# 8. CHECK INVALID VALUES
# ------------------------------------------------------------

invalid_report = {}

for feature in FEATURES:
    invalid_report[feature] = int(
        (~np.isfinite(df[feature].dropna())).sum()
    )

print("\nNon-finite values:")
print(pd.Series(invalid_report))

# ------------------------------------------------------------
# 9. SPATIAL COVERAGE MAP
# ------------------------------------------------------------

spatial_cells = (
    df[["node_id", "grid_latitude", "grid_longitude"]]
    .drop_duplicates()
)

plt.figure(figsize=(10, 8))

plt.scatter(
    spatial_cells["grid_longitude"],
    spatial_cells["grid_latitude"],
    s=35,
    alpha=0.8
)

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("NASA POWER Spatial Grid Coverage — India")
plt.grid(True, alpha=0.3)

plt.savefig(
    OUTPUT_DIR / "spatial_grid_coverage.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# ------------------------------------------------------------
# 10. MONTHLY OBSERVATION COVERAGE
# ------------------------------------------------------------

monthly_coverage = (
    df.groupby("time")["node_id"]
    .nunique()
)

plt.figure(figsize=(14, 5))

plt.plot(
    monthly_coverage.index,
    monthly_coverage.values,
    marker="o",
    markersize=3
)

plt.xlabel("Month")
plt.ylabel("Number of spatial cells")
plt.title("Monthly Spatial Coverage — 2015 to 2024")
plt.grid(True, alpha=0.3)

plt.savefig(
    OUTPUT_DIR / "monthly_spatial_coverage.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# ------------------------------------------------------------
# 11. SAVE QUALITY REPORTS
# ------------------------------------------------------------

coverage.to_csv(
    OUTPUT_DIR / "spatial_cell_coverage.csv",
    index=False
)

missing_report.to_csv(
    OUTPUT_DIR / "feature_missingness.csv"
)

monthly_coverage.rename(
    "available_spatial_cells"
).to_csv(
    OUTPUT_DIR / "monthly_coverage.csv"
)

# ------------------------------------------------------------
# 12. FINAL REPORT
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("CELL 7 COMPLETED")
print("=" * 70)

print("Dataset rows:", len(df))
print("Spatial cells:", df["node_id"].nunique())
print("Monthly observations:", df["time"].nunique())
print("Duplicate records:", duplicate_count)
print("Incomplete spatial cells:", len(incomplete_nodes))
print("Missing feature values:", int(df[FEATURES].isna().sum().sum()))

print("\nSaved reports to:")
print(OUTPUT_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 11
# Execution count: 16
# ============================================================


# ============================================================
# CELL 8: CREATE SPATIOTEMPORAL TENSOR
# ============================================================

import numpy as np
import pandas as pd
import json

from pathlib import Path

# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "nasa_power_grid_2deg.parquet"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

START_DATE = "2015-01-01"
END_DATE = "2024-12-01"

# ------------------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------------------

df = pd.read_parquet(INPUT_FILE)

df["time"] = pd.to_datetime(df["time"])

df = df.sort_values(
    ["time", "node_id"]
).reset_index(drop=True)

# ------------------------------------------------------------
# 3. CREATE COMPLETE MONTH INDEX
# ------------------------------------------------------------

time_index = pd.date_range(
    start=START_DATE,
    end=END_DATE,
    freq="MS"
)

print("Total monthly time steps:", len(time_index))

# ------------------------------------------------------------
# 4. CREATE STABLE SPATIAL NODE INDEX
# ------------------------------------------------------------

nodes = (
    df[
        ["node_id", "grid_latitude", "grid_longitude"]
    ]
    .drop_duplicates()
    .sort_values("node_id")
    .reset_index(drop=True)
)

node_ids = nodes["node_id"].tolist()

print("Total spatial nodes:", len(node_ids))

# ------------------------------------------------------------
# 5. CREATE TIME-NODE-FEATURE ARRAY
# ------------------------------------------------------------

tensor_df = df.pivot(
    index="time",
    columns="node_id",
    values=FEATURES
)

# Reindex all expected months and nodes
tensor_df = tensor_df.reindex(
    index=time_index,
    columns=pd.MultiIndex.from_product(
        [FEATURES, node_ids]
    )
)

# Convert to NumPy
# Original pivot order: feature, node
# Required order: time, node, feature

tensor = (
    tensor_df
    .to_numpy(dtype=np.float32)
    .reshape(
        len(time_index),
        len(FEATURES),
        len(node_ids)
    )
    .transpose(0, 2, 1)
)

# ------------------------------------------------------------
# 6. VALIDATE TENSOR
# ------------------------------------------------------------

print("\n" + "=" * 65)
print("SPATIOTEMPORAL TENSOR REPORT")
print("=" * 65)

print("Tensor shape:", tensor.shape)
print("Expected shape:", (
    len(time_index),
    len(node_ids),
    len(FEATURES)
))

print("Data type:", tensor.dtype)

print(
    "Missing values:",
    int(np.isnan(tensor).sum())
)

print(
    "Infinite values:",
    int(np.isinf(tensor).sum())
)

assert tensor.shape == (
    120,
    255,
    4
), "Unexpected tensor shape"

assert np.isfinite(tensor).all(), (
    "Tensor contains missing or infinite values"
)

# ------------------------------------------------------------
# 7. SAVE TENSOR AND METADATA
# ------------------------------------------------------------

np.save(
    OUTPUT_DIR / "nasa_power_tensor.npy",
    tensor
)

nodes.to_csv(
    OUTPUT_DIR / "spatial_nodes.csv",
    index=False
)

metadata = {
    "project": "Earth Systems Trend Detective",
    "start_date": START_DATE,
    "end_date": END_DATE,
    "time_steps": len(time_index),
    "spatial_nodes": len(node_ids),
    "features": FEATURES,
    "tensor_shape": list(tensor.shape),
    "tensor_order": [
        "time",
        "spatial_node",
        "feature"
    ],
    "grid_resolution_degrees": 2.0
}

with open(
    OUTPUT_DIR / "tensor_metadata.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(metadata, f, indent=4)

np.save(
    OUTPUT_DIR / "tensor_time_index.npy",
    time_index.to_numpy()
)

print("\nSaved files:")
print("1. nasa_power_tensor.npy")
print("2. spatial_nodes.csv")
print("3. tensor_metadata.json")
print("4. tensor_time_index.npy")

print("\nCELL 8 COMPLETED SUCCESSFULLY")


# ============================================================
# ORIGINAL NOTEBOOK CELL 12
# Execution count: 17
# ============================================================


# ============================================================
# CELL 9: CHRONOLOGICAL DATA SPLIT AND NORMALIZATION
# ============================================================

import numpy as np
import json
from pathlib import Path

# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "model_training"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TENSOR_FILE = DATA_DIR / "nasa_power_tensor.npy"
TIME_FILE = DATA_DIR / "tensor_time_index.npy"

FEATURES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

# ------------------------------------------------------------
# 2. LOAD TENSOR AND TIME INDEX
# ------------------------------------------------------------

tensor = np.load(TENSOR_FILE)
time_index = np.load(TIME_FILE, allow_pickle=True)

print("Original tensor shape:", tensor.shape)

# ------------------------------------------------------------
# 3. VALIDATE INPUT
# ------------------------------------------------------------

assert tensor.ndim == 3, "Tensor must have 3 dimensions"

num_months, num_nodes, num_features = tensor.shape

assert num_months == 120
assert num_features == len(FEATURES)
assert len(time_index) == num_months
assert np.isfinite(tensor).all(), (
    "Input tensor contains missing or infinite values"
)

# ------------------------------------------------------------
# 4. CHRONOLOGICAL SPLIT
# ------------------------------------------------------------

TRAIN_END = 84
VAL_END = 108

X_train_raw = tensor[:TRAIN_END].copy()

X_val_raw = tensor[TRAIN_END:VAL_END].copy()

X_test_raw = tensor[VAL_END:].copy()

train_dates = time_index[:TRAIN_END]
val_dates = time_index[TRAIN_END:VAL_END]
test_dates = time_index[VAL_END:]

print("\nDataset split:")
print("Training months:", len(X_train_raw))
print("Validation months:", len(X_val_raw))
print("Testing months:", len(X_test_raw))

print("\nDate ranges:")
print("Training:", train_dates[0], "to", train_dates[-1])
print("Validation:", val_dates[0], "to", val_dates[-1])
print("Testing:", test_dates[0], "to", test_dates[-1])

# ------------------------------------------------------------
# 5. CALCULATE TRAINING-ONLY NORMALIZATION PARAMETERS
# ------------------------------------------------------------

# Calculate one mean and standard deviation per feature.
# Statistics are calculated over training months and spatial nodes.

feature_mean = X_train_raw.mean(axis=(0, 1))

feature_std = X_train_raw.std(axis=(0, 1))

# Protect against division by zero.
feature_std = np.where(
    feature_std < 1e-8,
    1.0,
    feature_std
)

print("\nTraining feature means:")
for name, value in zip(FEATURES, feature_mean):
    print(f"{name}: {value:.6f}")

print("\nTraining feature standard deviations:")
for name, value in zip(FEATURES, feature_std):
    print(f"{name}: {value:.6f}")

# ------------------------------------------------------------
# 6. NORMALIZE ALL SPLITS USING TRAINING STATISTICS
# ------------------------------------------------------------

X_train = (
    X_train_raw - feature_mean
) / feature_std

X_val = (
    X_val_raw - feature_mean
) / feature_std

X_test = (
    X_test_raw - feature_mean
) / feature_std

X_train = X_train.astype(np.float32)
X_val = X_val.astype(np.float32)
X_test = X_test.astype(np.float32)

# ------------------------------------------------------------
# 7. VALIDATE NORMALIZED DATA
# ------------------------------------------------------------

print("\nNormalized tensor shapes:")
print("Training:", X_train.shape)
print("Validation:", X_val.shape)
print("Testing:", X_test.shape)

print("\nTraining normalized feature means:")
print(X_train.mean(axis=(0, 1)).round(5))

print("\nTraining normalized feature std:")
print(X_train.std(axis=(0, 1)).round(5))

assert np.isfinite(X_train).all()
assert np.isfinite(X_val).all()
assert np.isfinite(X_test).all()

# ------------------------------------------------------------
# 8. SAVE SPLITS
# ------------------------------------------------------------

np.save(OUTPUT_DIR / "X_train.npy", X_train)
np.save(OUTPUT_DIR / "X_val.npy", X_val)
np.save(OUTPUT_DIR / "X_test.npy", X_test)

np.save(OUTPUT_DIR / "train_dates.npy", train_dates)
np.save(OUTPUT_DIR / "val_dates.npy", val_dates)
np.save(OUTPUT_DIR / "test_dates.npy", test_dates)

# Save normalization parameters for later inverse transformation.
scaler_metadata = {
    "features": FEATURES,
    "mean": feature_mean.tolist(),
    "std": feature_std.tolist(),
    "normalization": "z-score",
    "statistics_fit_on": "training data only",
    "training_months": 84,
    "validation_months": 24,
    "testing_months": 12
}

with open(
    OUTPUT_DIR / "scaler_metadata.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(scaler_metadata, f, indent=4)

# ------------------------------------------------------------
# 9. FINAL REPORT
# ------------------------------------------------------------

print("\n" + "=" * 65)
print("CELL 9 COMPLETED SUCCESSFULLY")
print("=" * 65)

print("Training shape:", X_train.shape)
print("Validation shape:", X_val.shape)
print("Testing shape:", X_test.shape)

print("Training date range:", train_dates[0], "to", train_dates[-1])
print("Validation date range:", val_dates[0], "to", val_dates[-1])
print("Testing date range:", test_dates[0], "to", test_dates[-1])

print("\nMissing values:", 
      np.isnan(X_train).sum()
      + np.isnan(X_val).sum()
      + np.isnan(X_test).sum())

print("Infinite values:",
      np.isinf(X_train).sum()
      + np.isinf(X_val).sum()
      + np.isinf(X_test).sum())

print("\nSaved files in:", OUTPUT_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 13
# Execution count: 18
# ============================================================


# ============================================================
# CELL 10: BUILD SPATIAL GRAPH
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json

from pathlib import Path
from sklearn.neighbors import BallTree
from scipy.sparse import coo_matrix, save_npz

# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "outputs" / "model_training"
GRAPH_DIR = PROJECT_ROOT / "outputs" / "spatial_graph"

GRAPH_DIR.mkdir(parents=True, exist_ok=True)

K_NEIGHBORS = 6
EARTH_RADIUS_KM = 6371.0088

# ------------------------------------------------------------
# 2. LOAD SPATIAL NODES
# ------------------------------------------------------------

nodes = pd.read_csv(
    DATA_DIR / "spatial_nodes.csv"
)

required_columns = [
    "node_id",
    "grid_latitude",
    "grid_longitude"
]

assert all(
    col in nodes.columns for col in required_columns
), "Required spatial node columns are missing"

nodes = nodes.sort_values(
    "node_id"
).reset_index(drop=True)

num_nodes = len(nodes)

print("Total spatial nodes:", num_nodes)

# ------------------------------------------------------------
# 3. CONVERT COORDINATES TO RADIANS
# ------------------------------------------------------------

coordinates_degrees = nodes[
    ["grid_latitude", "grid_longitude"]
].to_numpy(dtype=np.float64)

coordinates_radians = np.radians(
    coordinates_degrees
)

# ------------------------------------------------------------
# 4. BUILD SPHERICAL NEAREST-NEIGHBOR TREE
# ------------------------------------------------------------

tree = BallTree(
    coordinates_radians,
    metric="haversine"
)

distances, neighbors = tree.query(
    coordinates_radians,
    k=min(K_NEIGHBORS + 1, num_nodes)
)

# ------------------------------------------------------------
# 5. CREATE DIRECTED EDGE LIST
# ------------------------------------------------------------

edge_pairs = set()

for source in range(num_nodes):

    for target in neighbors[source]:

        edge_pairs.add((source, int(target)))

        # Add reverse connection to make the graph bidirectional.
        edge_pairs.add((int(target), source))

# Ensure every node has a self-loop.
for node in range(num_nodes):
    edge_pairs.add((node, node))

edge_index = np.array(
    sorted(edge_pairs),
    dtype=np.int64
).T

# ------------------------------------------------------------
# 6. CALCULATE HAVERSINE DISTANCES
# ------------------------------------------------------------

source_nodes = edge_index[0]
target_nodes = edge_index[1]

source_coordinates = coordinates_radians[source_nodes]
target_coordinates = coordinates_radians[target_nodes]

delta = target_coordinates - source_coordinates

a = (
    np.sin(delta[:, 0] / 2) ** 2
    +
    np.cos(source_coordinates[:, 0])
    * np.cos(target_coordinates[:, 0])
    * np.sin(delta[:, 1] / 2) ** 2
)

a = np.clip(a, 0.0, 1.0)

angular_distance = 2 * np.arcsin(
    np.sqrt(a)
)

edge_distances_km = (
    EARTH_RADIUS_KM * angular_distance
)

# ------------------------------------------------------------
# 7. CALCULATE DISTANCE-BASED EDGE WEIGHTS
# ------------------------------------------------------------

# Gaussian kernel:
# Nearby nodes receive larger weights.

sigma = max(
    np.median(edge_distances_km[edge_distances_km > 0]),
    1e-6
)

edge_weights = np.exp(
    -(edge_distances_km ** 2) / (2 * sigma ** 2)
)

# Self-loop weight = 1
edge_weights[source_nodes == target_nodes] = 1.0

edge_weights = edge_weights.astype(np.float32)

# ------------------------------------------------------------
# 8. BUILD SPARSE ADJACENCY MATRIX
# ------------------------------------------------------------

adjacency = coo_matrix(
    (
        edge_weights,
        (source_nodes, target_nodes)
    ),
    shape=(num_nodes, num_nodes),
    dtype=np.float32
).tocsr()

# ------------------------------------------------------------
# 9. VALIDATE GRAPH
# ------------------------------------------------------------

assert adjacency.shape == (
    num_nodes,
    num_nodes
)

assert np.isfinite(edge_weights).all()

assert np.all(
    adjacency.diagonal() > 0
), "Some nodes are missing self-loops"

# Verify undirected connectivity weights.
difference = adjacency - adjacency.T

assert (
    difference.nnz == 0
    or np.max(np.abs(difference.data)) < 1e-6
), "Graph is not symmetric"

# ------------------------------------------------------------
# 10. GRAPH STATISTICS
# ------------------------------------------------------------

degrees = np.diff(adjacency.indptr)

print("\n" + "=" * 65)
print("SPATIAL GRAPH REPORT")
print("=" * 65)

print("Nodes:", num_nodes)
print("Edges:", edge_index.shape[1])
print("Average degree:", degrees.mean())
print("Minimum degree:", degrees.min())
print("Maximum degree:", degrees.max())

print(
    "Mean edge distance (km):",
    round(edge_distances_km.mean(), 3)
)

print(
    "Median edge distance (km):",
    round(np.median(edge_distances_km), 3)
)

print("Adjacency shape:", adjacency.shape)
print("Graph symmetric:", (
    difference.nnz == 0
    or np.max(np.abs(difference.data)) < 1e-6
))

# ------------------------------------------------------------
# 11. VISUALIZE SPATIAL GRAPH
# ------------------------------------------------------------

plt.figure(figsize=(12, 9))

# Draw edges.
for source, target in zip(
    source_nodes,
    target_nodes
):

    if source < target:

        plt.plot(
            [
                coordinates_degrees[source, 1],
                coordinates_degrees[target, 1]
            ],
            [
                coordinates_degrees[source, 0],
                coordinates_degrees[target, 0]
            ],
            linewidth=0.5,
            alpha=0.25
        )

plt.scatter(
    coordinates_degrees[:, 1],
    coordinates_degrees[:, 0],
    s=22
)

plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.title(
    "Spatial Nearest-Neighbor Graph — India"
)

plt.grid(alpha=0.2)

plt.savefig(
    GRAPH_DIR / "spatial_graph.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# ------------------------------------------------------------
# 12. SAVE GRAPH FILES
# ------------------------------------------------------------

np.save(
    GRAPH_DIR / "edge_index.npy",
    edge_index
)

np.save(
    GRAPH_DIR / "edge_weights.npy",
    edge_weights
)

np.save(
    GRAPH_DIR / "edge_distances_km.npy",
    edge_distances_km
)

save_npz(
    GRAPH_DIR / "adjacency_matrix.npz",
    adjacency
)

nodes.to_csv(
    GRAPH_DIR / "graph_nodes.csv",
    index=False
)

metadata = {
    "graph_type": "spherical_haversine_knn",
    "num_nodes": int(num_nodes),
    "num_edges": int(edge_index.shape[1]),
    "k_neighbors": K_NEIGHBORS,
    "earth_radius_km": EARTH_RADIUS_KM,
    "distance_metric": "haversine",
    "edge_weight_method": "gaussian_kernel",
    "self_loops": True,
    "bidirectional": True,
    "adjacency_shape": list(adjacency.shape)
}

with open(
    GRAPH_DIR / "graph_metadata.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metadata,
        f,
        indent=4
    )

print("\nSaved graph files:")
print("1. edge_index.npy")
print("2. edge_weights.npy")
print("3. edge_distances_km.npy")
print("4. adjacency_matrix.npz")
print("5. graph_nodes.csv")
print("6. graph_metadata.json")
print("7. spatial_graph.png")

print("\nCELL 10 COMPLETED SUCCESSFULLY")
print("Output directory:", GRAPH_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 14
# Execution count: 19
# ============================================================


# ============================================================
# CELL 11: CREATE TEMPORAL SEQUENCES
# ============================================================

import numpy as np
import json

from pathlib import Path

# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

MODEL_DIR = PROJECT_ROOT / "outputs" / "model_training"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

SEQUENCE_LENGTH = 12

# ------------------------------------------------------------
# 2. LOAD NORMALIZED DATA
# ------------------------------------------------------------

X_train = np.load(MODEL_DIR / "X_train.npy")
X_val = np.load(MODEL_DIR / "X_val.npy")
X_test = np.load(MODEL_DIR / "X_test.npy")

print("Training data:", X_train.shape)
print("Validation data:", X_val.shape)
print("Testing data:", X_test.shape)

# ------------------------------------------------------------
# 3. SEQUENCE GENERATION FUNCTION
# ------------------------------------------------------------

def create_sequences(data, sequence_length=12):

    X = []
    y = []

    for i in range(
        len(data) - sequence_length
    ):

        # Previous 12 months
        input_sequence = data[
            i:i + sequence_length
        ]

        # Following month
        target = data[
            i + sequence_length
        ]

        X.append(input_sequence)
        y.append(target)

    return (
        np.asarray(X, dtype=np.float32),
        np.asarray(y, dtype=np.float32)
    )

# ------------------------------------------------------------
# 4. CREATE TRAINING SEQUENCES
# ------------------------------------------------------------

X_train_seq, y_train_seq = create_sequences(
    X_train,
    SEQUENCE_LENGTH
)

# ------------------------------------------------------------
# 5. CREATE VALIDATION SEQUENCES
# ------------------------------------------------------------

# Use the last 12 training months as historical context.
# This allows validation to begin in January 2022.

val_context = np.concatenate(
    [
        X_train[-SEQUENCE_LENGTH:],
        X_val
    ],
    axis=0
)

X_val_seq, y_val_seq = create_sequences(
    val_context,
    SEQUENCE_LENGTH
)

# ------------------------------------------------------------
# 6. CREATE TEST SEQUENCES
# ------------------------------------------------------------

# Use the last 12 validation months as historical context.
# This allows testing to begin in January 2024.

test_context = np.concatenate(
    [
        X_val[-SEQUENCE_LENGTH:],
        X_test
    ],
    axis=0
)

X_test_seq, y_test_seq = create_sequences(
    test_context,
    SEQUENCE_LENGTH
)

# ------------------------------------------------------------
# 7. DISPLAY SEQUENCE SHAPES
# ------------------------------------------------------------

print("\n" + "=" * 65)
print("TEMPORAL SEQUENCE REPORT")
print("=" * 65)

print("Sequence length:", SEQUENCE_LENGTH)

print("\nTraining:")
print("X_train_seq:", X_train_seq.shape)
print("y_train_seq:", y_train_seq.shape)

print("\nValidation:")
print("X_val_seq:", X_val_seq.shape)
print("y_val_seq:", y_val_seq.shape)

print("\nTesting:")
print("X_test_seq:", X_test_seq.shape)
print("y_test_seq:", y_test_seq.shape)

# ------------------------------------------------------------
# 8. VALIDATE SEQUENCE SHAPES
# ------------------------------------------------------------

num_nodes = X_train.shape[1]
num_features = X_train.shape[2]

assert X_train_seq.shape == (
    72,
    SEQUENCE_LENGTH,
    num_nodes,
    num_features
)

assert y_train_seq.shape == (
    72,
    num_nodes,
    num_features
)

assert X_val_seq.shape == (
    24,
    SEQUENCE_LENGTH,
    num_nodes,
    num_features
)

assert y_val_seq.shape == (
    24,
    num_nodes,
    num_features
)

assert X_test_seq.shape == (
    12,
    SEQUENCE_LENGTH,
    num_nodes,
    num_features
)

assert y_test_seq.shape == (
    12,
    num_nodes,
    num_features
)

# ------------------------------------------------------------
# 9. CHECK DATA VALIDITY
# ------------------------------------------------------------

for name, array in [
    ("Training inputs", X_train_seq),
    ("Training targets", y_train_seq),
    ("Validation inputs", X_val_seq),
    ("Validation targets", y_val_seq),
    ("Testing inputs", X_test_seq),
    ("Testing targets", y_test_seq)
]:

    assert np.isfinite(array).all(), (
        f"{name} contains NaN or infinite values"
    )

# ------------------------------------------------------------
# 10. SAVE SEQUENCES
# ------------------------------------------------------------

np.save(
    MODEL_DIR / "X_train_seq.npy",
    X_train_seq
)

np.save(
    MODEL_DIR / "y_train_seq.npy",
    y_train_seq
)

np.save(
    MODEL_DIR / "X_val_seq.npy",
    X_val_seq
)

np.save(
    MODEL_DIR / "y_val_seq.npy",
    y_val_seq
)

np.save(
    MODEL_DIR / "X_test_seq.npy",
    X_test_seq
)

np.save(
    MODEL_DIR / "y_test_seq.npy",
    y_test_seq
)

# ------------------------------------------------------------
# 11. SAVE SEQUENCE METADATA
# ------------------------------------------------------------

metadata = {
    "sequence_length": SEQUENCE_LENGTH,
    "prediction_horizon_months": 1,
    "num_spatial_nodes": int(num_nodes),
    "num_features": int(num_features),
    "training_sequences": int(len(X_train_seq)),
    "validation_sequences": int(len(X_val_seq)),
    "testing_sequences": int(len(X_test_seq)),
    "input_shape": [
        SEQUENCE_LENGTH,
        num_nodes,
        num_features
    ]
}

with open(
    MODEL_DIR / "sequence_metadata.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metadata,
        f,
        indent=4
    )

print("\nSaved all sequence files.")

print("\nCELL 11 COMPLETED SUCCESSFULLY")


# ============================================================
# ORIGINAL NOTEBOOK CELL 15
# Execution count: 20
# ============================================================

# ================================================================
# CELL 12: BUILD GCN-GRU MODEL
# Project: NASA Earth Systems Trend Detective
# ================================================================

import os
import json
import random
import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch
import torch.nn as nn
from pathlib import Path

# ------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TRAINING_DIR = PROJECT_ROOT / "outputs" / "model_training"
GRAPH_DIR = PROJECT_ROOT / "outputs" / "spatial_graph"

TRAINING_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
INPUT_FEATURES = 4
GCN_HIDDEN = 32
GRU_HIDDEN = 64
OUTPUT_FEATURES = 4
DROPOUT = 0.15

# ------------------------------------------------
# 2. REPRODUCIBILITY
# ------------------------------------------------

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# ------------------------------------------------
# 3. DEVICE CONFIGURATION
# ------------------------------------------------

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", DEVICE)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print(
        "GPU memory:",
        round(
            torch.cuda.get_device_properties(0).total_memory
            / (1024 ** 3),
            2
        ),
        "GB"
    )

# ------------------------------------------------
# 4. LOAD TRAINING SEQUENCES
# ------------------------------------------------

X_train_seq = np.load(
    TRAINING_DIR / "X_train_seq.npy"
)

y_train_seq = np.load(
    TRAINING_DIR / "y_train_seq.npy"
)

X_val_seq = np.load(
    TRAINING_DIR / "X_val_seq.npy"
)

y_val_seq = np.load(
    TRAINING_DIR / "y_val_seq.npy"
)

X_test_seq = np.load(
    TRAINING_DIR / "X_test_seq.npy"
)

y_test_seq = np.load(
    TRAINING_DIR / "y_test_seq.npy"
)

print("\nLoaded sequence datasets:")

print("Training:", X_train_seq.shape, y_train_seq.shape)
print("Validation:", X_val_seq.shape, y_val_seq.shape)
print("Testing:", X_test_seq.shape, y_test_seq.shape)

# ------------------------------------------------
# 5. VALIDATE SPATIAL GRAPH
# ------------------------------------------------

adjacency_path = GRAPH_DIR / "adjacency_matrix.npz"

if not adjacency_path.exists():
    raise FileNotFoundError(
        f"Spatial adjacency matrix not found: {adjacency_path}"
    )

adjacency = sp.load_npz(adjacency_path).astype(np.float32)

print("\nOriginal adjacency shape:", adjacency.shape)

num_nodes = X_train_seq.shape[2]

if adjacency.shape != (num_nodes, num_nodes):
    raise ValueError(
        "Graph node count does not match training data."
    )

if (adjacency - adjacency.T).nnz != 0:
    raise ValueError(
        "Adjacency matrix must be symmetric."
    )

# ------------------------------------------------
# 6. NORMALIZE ADJACENCY MATRIX
# ------------------------------------------------

# A_hat = D^(-1/2) * A * D^(-1/2)

degree = np.asarray(
    adjacency.sum(axis=1)
).flatten()

degree_inv_sqrt = np.zeros_like(degree)

nonzero = degree > 0

degree_inv_sqrt[nonzero] = (
    degree[nonzero] ** -0.5
)

D_inv_sqrt = sp.diags(degree_inv_sqrt)

normalized_adjacency = (
    D_inv_sqrt @ adjacency @ D_inv_sqrt
).toarray().astype(np.float32)

ADJACENCY_TENSOR = torch.tensor(
    normalized_adjacency,
    dtype=torch.float32,
    device=DEVICE
)

print("Normalized adjacency:", ADJACENCY_TENSOR.shape)

# ------------------------------------------------
# 7. DEFINE GCN LAYER
# ------------------------------------------------

class GraphConvolution(nn.Module):

    def __init__(self, in_features, out_features):

        super().__init__()

        self.linear = nn.Linear(
            in_features,
            out_features
        )

    def forward(self, x, adjacency):

        # x shape: [batch, time, nodes, features]

        x = self.linear(x)

        # Spatial message aggregation
        x = torch.einsum(
            "nm,btmf->btnf",
            adjacency,
            x
        )

        return x

# ------------------------------------------------
# 8. DEFINE GCN-GRU MODEL
# ------------------------------------------------

class GCNGRU(nn.Module):

    def __init__(
        self,
        input_features=4,
        gcn_hidden=32,
        gru_hidden=64,
        output_features=4,
        dropout=0.15
    ):

        super().__init__()

        # Spatial encoder
        self.gcn1 = GraphConvolution(
            input_features,
            gcn_hidden
        )

        self.gcn2 = GraphConvolution(
            gcn_hidden,
            gcn_hidden
        )

        self.dropout = nn.Dropout(dropout)

        self.activation = nn.ReLU()

        # Temporal encoder
        self.gru = nn.GRU(
            input_size=gcn_hidden,
            hidden_size=gru_hidden,
            num_layers=1,
            batch_first=True
        )

        # Next-month prediction layer
        self.output_layer = nn.Linear(
            gru_hidden,
            output_features
        )

    def forward(self, x, adjacency):

        # Input:
        # [batch, 12, 255, 4]

        # ----------------------------
        # Spatial learning
        # ----------------------------

        x = self.gcn1(x, adjacency)

        x = self.activation(x)

        x = self.dropout(x)

        x = self.gcn2(x, adjacency)

        x = self.activation(x)

        # Shape:
        # [batch, time, nodes, gcn_hidden]

        # ----------------------------
        # Prepare GRU input
        # ----------------------------

        batch_size = x.shape[0]
        time_steps = x.shape[1]
        nodes = x.shape[2]
        hidden_size = x.shape[3]

        # Each spatial node gets its own
        # 12-month temporal sequence.

        x = x.permute(0, 2, 1, 3)

        x = x.reshape(
            batch_size * nodes,
            time_steps,
            hidden_size
        )

        # ----------------------------
        # Temporal learning
        # ----------------------------

        gru_output, hidden_state = self.gru(x)

        # Last GRU hidden state
        x = hidden_state[-1]

        # ----------------------------
        # Prediction
        # ----------------------------

        x = self.output_layer(x)

        x = x.reshape(
            batch_size,
            nodes,
            OUTPUT_FEATURES
        )

        return x

# ------------------------------------------------
# 9. INITIALIZE MODEL
# ------------------------------------------------

model = GCNGRU(
    input_features=INPUT_FEATURES,
    gcn_hidden=GCN_HIDDEN,
    gru_hidden=GRU_HIDDEN,
    output_features=OUTPUT_FEATURES,
    dropout=DROPOUT
).to(DEVICE)

print("\nGCN-GRU MODEL")
print("=" * 65)

print(model)

total_parameters = sum(
    p.numel() for p in model.parameters()
)

trainable_parameters = sum(
    p.numel()
    for p in model.parameters()
    if p.requires_grad
)

print("\nTotal parameters:", total_parameters)

print("Trainable parameters:", trainable_parameters)

# ------------------------------------------------
# 10. TEST MODEL FORWARD PASS
# ------------------------------------------------

sample_input = torch.tensor(
    X_train_seq[:2],
    dtype=torch.float32,
    device=DEVICE
)

model.eval()

with torch.no_grad():

    sample_output = model(
        sample_input,
        ADJACENCY_TENSOR
    )

print("\nFORWARD PASS VALIDATION")
print("=" * 65)

print("Input shape:", tuple(sample_input.shape))

print("Output shape:", tuple(sample_output.shape))

expected_shape = (2, num_nodes, OUTPUT_FEATURES)

assert tuple(sample_output.shape) == expected_shape

assert torch.isfinite(sample_output).all()

print("\nForward pass successful.")
print("All output values are finite.")

# ------------------------------------------------
# 11. SAVE MODEL CONFIGURATION
# ------------------------------------------------

model_config = {
    "architecture": "GCN-GRU",
    "input_features": INPUT_FEATURES,
    "gcn_hidden": GCN_HIDDEN,
    "gru_hidden": GRU_HIDDEN,
    "output_features": OUTPUT_FEATURES,
    "dropout": DROPOUT,
    "sequence_length": 12,
    "spatial_nodes": num_nodes,
    "total_parameters": total_parameters,
    "trainable_parameters": trainable_parameters,
    "device": str(DEVICE),
    "feature_names": [
        "T2M",
        "PRECTOTCORR",
        "RH2M",
        "WS10M"
    ]
}

config_path = TRAINING_DIR / "gcn_gru_config.json"

with open(config_path, "w") as f:
    json.dump(model_config, f, indent=4)

print("\nSaved model configuration:")
print(config_path)

print("\n" + "=" * 65)
print("CELL 12 COMPLETED SUCCESSFULLY")
print("=" * 65)


# ============================================================
# ORIGINAL NOTEBOOK CELL 16
# Execution count: 21
# ============================================================


# ================================================================
# CELL 13: TRAIN GCN-GRU MODEL
# Project: NASA Earth Systems Trend Detective
# ================================================================

import os
import json
import time
import copy
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from torch.utils.data import TensorDataset, DataLoader
from pathlib import Path

# ------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

TRAINING_DIR = PROJECT_ROOT / "outputs" / "model_training"
TRAINING_DIR.mkdir(parents=True, exist_ok=True)

EPOCHS = 100
BATCH_SIZE = 4
LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-5
PATIENCE = 15
MIN_DELTA = 1e-5
GRADIENT_CLIP = 1.0

CHECKPOINT_PATH = TRAINING_DIR / "best_gcn_gru_model.pth"
HISTORY_PATH = TRAINING_DIR / "training_history.csv"
TRAINING_REPORT_PATH = TRAINING_DIR / "training_report.json"

# ------------------------------------------------
# 2. VERIFY MODEL AND DEVICE
# ------------------------------------------------

assert "model" in globals(), "Run Cell 12 first."
assert "ADJACENCY_TENSOR" in globals(), "Run Cell 12 first."
assert "DEVICE" in globals(), "Run Cell 12 first."

print("Training device:", DEVICE)
print("Model:", model.__class__.__name__)

# ------------------------------------------------
# 3. LOAD SEQUENCE DATA
# ------------------------------------------------

X_train_seq = np.load(TRAINING_DIR / "X_train_seq.npy")
y_train_seq = np.load(TRAINING_DIR / "y_train_seq.npy")

X_val_seq = np.load(TRAINING_DIR / "X_val_seq.npy")
y_val_seq = np.load(TRAINING_DIR / "y_val_seq.npy")

X_test_seq = np.load(TRAINING_DIR / "X_test_seq.npy")
y_test_seq = np.load(TRAINING_DIR / "y_test_seq.npy")

# Check dimensions
assert X_train_seq.shape[1:] == (12, 255, 4)
assert y_train_seq.shape[1:] == (255, 4)

assert X_val_seq.shape[1:] == (12, 255, 4)
assert y_val_seq.shape[1:] == (255, 4)

assert X_test_seq.shape[1:] == (12, 255, 4)
assert y_test_seq.shape[1:] == (255, 4)

# Check numerical validity
for name, array in [
    ("X_train", X_train_seq),
    ("y_train", y_train_seq),
    ("X_val", X_val_seq),
    ("y_val", y_val_seq),
    ("X_test", X_test_seq),
    ("y_test", y_test_seq)
]:
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains NaN or infinite values.")

print("\nDataset validation successful.")

# ------------------------------------------------
# 4. CONVERT DATA TO PYTORCH TENSORS
# ------------------------------------------------

X_train_tensor = torch.tensor(
    X_train_seq, dtype=torch.float32
)

y_train_tensor = torch.tensor(
    y_train_seq, dtype=torch.float32
)

X_val_tensor = torch.tensor(
    X_val_seq, dtype=torch.float32
)

y_val_tensor = torch.tensor(
    y_val_seq, dtype=torch.float32
)

X_test_tensor = torch.tensor(
    X_test_seq, dtype=torch.float32
)

y_test_tensor = torch.tensor(
    y_test_seq, dtype=torch.float32
)

# Keep datasets on CPU.
# Batches are transferred to GPU during training.

train_dataset = TensorDataset(
    X_train_tensor,
    y_train_tensor
)

val_dataset = TensorDataset(
    X_val_tensor,
    y_val_tensor
)

test_dataset = TensorDataset(
    X_test_tensor,
    y_test_tensor
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
    pin_memory=(DEVICE.type == "cuda")
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=(DEVICE.type == "cuda")
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=(DEVICE.type == "cuda")
)

print("\nDataLoaders created:")
print("Training batches:", len(train_loader))
print("Validation batches:", len(val_loader))
print("Testing batches:", len(test_loader))

# ------------------------------------------------
# 5. LOSS AND OPTIMIZER
# ------------------------------------------------

criterion = nn.MSELoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=WEIGHT_DECAY
)

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="min",
    factor=0.5,
    patience=5
)

# ------------------------------------------------
# 6. TRAINING FUNCTION
# ------------------------------------------------

def train_one_epoch():

    model.train()

    total_loss = 0.0
    total_samples = 0

    for batch_x, batch_y in train_loader:

        batch_x = batch_x.to(
            DEVICE,
            non_blocking=True
        )

        batch_y = batch_y.to(
            DEVICE,
            non_blocking=True
        )

        optimizer.zero_grad(set_to_none=True)

        predictions = model(
            batch_x,
            ADJACENCY_TENSOR
        )

        loss = criterion(
            predictions,
            batch_y
        )

        if not torch.isfinite(loss):
            raise RuntimeError(
                "Non-finite training loss detected."
            )

        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=GRADIENT_CLIP
        )

        optimizer.step()

        batch_size = batch_x.size(0)

        total_loss += loss.item() * batch_size
        total_samples += batch_size

    return total_loss / total_samples

# ------------------------------------------------
# 7. VALIDATION FUNCTION
# ------------------------------------------------

def validate_model():

    model.eval()

    total_loss = 0.0
    total_samples = 0

    with torch.no_grad():

        for batch_x, batch_y in val_loader:

            batch_x = batch_x.to(
                DEVICE,
                non_blocking=True
            )

            batch_y = batch_y.to(
                DEVICE,
                non_blocking=True
            )

            predictions = model(
                batch_x,
                ADJACENCY_TENSOR
            )

            loss = criterion(
                predictions,
                batch_y
            )

            if not torch.isfinite(loss):
                raise RuntimeError(
                    "Non-finite validation loss detected."
                )

            batch_size = batch_x.size(0)

            total_loss += loss.item() * batch_size
            total_samples += batch_size

    return total_loss / total_samples

# ------------------------------------------------
# 8. TRAINING LOOP WITH EARLY STOPPING
# ------------------------------------------------

best_val_loss = float("inf")
best_epoch = 0
epochs_without_improvement = 0

history = []

best_model_state = None

print("\n" + "=" * 75)
print("STARTING GCN-GRU TRAINING")
print("=" * 75)

start_time = time.time()

for epoch in range(1, EPOCHS + 1):

    epoch_start = time.time()

    train_loss = train_one_epoch()

    val_loss = validate_model()

    scheduler.step(val_loss)

    current_lr = optimizer.param_groups[0]["lr"]

    improved = val_loss < (best_val_loss - MIN_DELTA)

    if improved:

        best_val_loss = val_loss
        best_epoch = epoch

        epochs_without_improvement = 0

        best_model_state = copy.deepcopy(
            model.state_dict()
        )

        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": best_model_state,
                "optimizer_state_dict": optimizer.state_dict(),
                "best_validation_loss": best_val_loss,
                "model_config": {
                    "input_features": 4,
                    "gcn_hidden": 32,
                    "gru_hidden": 64,
                    "output_features": 4,
                    "sequence_length": 12,
                    "spatial_nodes": 255
                }
            },
            CHECKPOINT_PATH
        )

    else:

        epochs_without_improvement += 1

    epoch_time = time.time() - epoch_start

    history.append({
        "epoch": epoch,
        "train_loss": train_loss,
        "validation_loss": val_loss,
        "learning_rate": current_lr,
        "epoch_time_seconds": epoch_time
    })

    print(
        f"Epoch [{epoch:03d}/{EPOCHS}] "
        f"| Train Loss: {train_loss:.6f} "
        f"| Val Loss: {val_loss:.6f} "
        f"| LR: {current_lr:.7f} "
        f"| Time: {epoch_time:.2f}s"
    )

    if epochs_without_improvement >= PATIENCE:

        print(
            f"\nEarly stopping triggered at epoch {epoch}."
        )

        break

# ------------------------------------------------
# 9. RESTORE BEST MODEL
# ------------------------------------------------

if best_model_state is None:

    raise RuntimeError(
        "No valid model checkpoint was produced."
    )

model.load_state_dict(best_model_state)

model.eval()

total_training_time = time.time() - start_time

# ------------------------------------------------
# 10. SAVE TRAINING HISTORY
# ------------------------------------------------

history_df = pd.DataFrame(history)

history_df.to_csv(
    HISTORY_PATH,
    index=False
)

# ------------------------------------------------
# 11. SAVE TRAINING REPORT
# ------------------------------------------------

training_report = {
    "architecture": "GCN-GRU",
    "device": str(DEVICE),
    "epochs_configured": EPOCHS,
    "epochs_completed": len(history),
    "best_epoch": best_epoch,
    "best_validation_loss": float(best_val_loss),
    "batch_size": BATCH_SIZE,
    "learning_rate_initial": LEARNING_RATE,
    "weight_decay": WEIGHT_DECAY,
    "early_stopping_patience": PATIENCE,
    "training_time_seconds": total_training_time,
    "checkpoint": str(CHECKPOINT_PATH),
    "history_file": str(HISTORY_PATH)
}

with open(TRAINING_REPORT_PATH, "w") as f:

    json.dump(
        training_report,
        f,
        indent=4
    )

# ------------------------------------------------
# 12. FINAL REPORT
# ------------------------------------------------

print("\n" + "=" * 75)
print("GCN-GRU TRAINING REPORT")
print("=" * 75)

print("Architecture:", "GCN-GRU")
print("Device:", DEVICE)
print("Epochs completed:", len(history))
print("Best epoch:", best_epoch)
print("Best validation loss:", round(best_val_loss, 6))
print("Training time:", round(total_training_time, 2), "seconds")

print("\nSaved files:")
print("Best model:", CHECKPOINT_PATH)
print("Training history:", HISTORY_PATH)
print("Training report:", TRAINING_REPORT_PATH)

if DEVICE.type == "cuda":

    print(
        "\nPeak GPU memory allocated:",
        round(
            torch.cuda.max_memory_allocated() / (1024 ** 3),
            3
        ),
        "GB"
    )

print("\n" + "=" * 75)
print("CELL 13 COMPLETED SUCCESSFULLY")
print("=" * 75)


# ============================================================
# ORIGINAL NOTEBOOK CELL 17
# Execution count: 22
# ============================================================


# ================================================================
# CELL 14: TRAINING PERFORMANCE VISUALIZATION
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

from pathlib import Path

# ------------------------------------------------
# 1. PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

TRAINING_DIR = PROJECT_ROOT / "outputs" / "model_training"

HISTORY_PATH = TRAINING_DIR / "training_history.csv"
REPORT_PATH = TRAINING_DIR / "training_report.json"

PLOT_DIR = PROJECT_ROOT / "outputs" / "visualizations"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

if not HISTORY_PATH.exists():
    raise FileNotFoundError(
        "Training history not found. Run Cell 13 first."
    )

# ------------------------------------------------
# 2. LOAD TRAINING HISTORY
# ------------------------------------------------

history = pd.read_csv(HISTORY_PATH)

required_columns = [
    "epoch",
    "train_loss",
    "validation_loss",
    "learning_rate"
]

missing_columns = [
    col for col in required_columns
    if col not in history.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: {missing_columns}"
    )

if history.empty:
    raise ValueError("Training history is empty.")

print("Training history loaded:", history.shape)
print("\nFirst five records:")
print(history.head())

# ------------------------------------------------
# 3. LOAD TRAINING REPORT
# ------------------------------------------------

if REPORT_PATH.exists():

    with open(REPORT_PATH, "r") as f:
        report = json.load(f)

    best_epoch = report["best_epoch"]
    best_val_loss = report["best_validation_loss"]

else:

    best_idx = history["validation_loss"].idxmin()

    best_epoch = int(history.loc[best_idx, "epoch"])

    best_val_loss = float(
        history.loc[best_idx, "validation_loss"]
    )

# ------------------------------------------------
# 4. TRAINING AND VALIDATION LOSS
# ------------------------------------------------

plt.figure(figsize=(12, 6))

plt.plot(
    history["epoch"],
    history["train_loss"],
    label="Training Loss",
    linewidth=2
)

plt.plot(
    history["epoch"],
    history["validation_loss"],
    label="Validation Loss",
    linewidth=2
)

plt.axvline(
    best_epoch,
    linestyle="--",
    label=f"Best Epoch: {best_epoch}"
)

plt.scatter(
    [best_epoch],
    [best_val_loss],
    s=70,
    zorder=5,
    label=f"Best Val Loss: {best_val_loss:.5f}"
)

plt.xlabel("Epoch")
plt.ylabel("Mean Squared Error")
plt.title("GCN-GRU Training and Validation Loss")

plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

loss_plot_path = PLOT_DIR / "training_validation_loss.png"

plt.savefig(
    loss_plot_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# ------------------------------------------------
# 5. LEARNING RATE HISTORY
# ------------------------------------------------

plt.figure(figsize=(10, 5))

plt.plot(
    history["epoch"],
    history["learning_rate"],
    marker="o",
    linewidth=2
)

plt.xlabel("Epoch")
plt.ylabel("Learning Rate")
plt.title("Learning Rate Schedule")

plt.yscale("log")
plt.grid(alpha=0.3)
plt.tight_layout()

lr_plot_path = PLOT_DIR / "learning_rate_schedule.png"

plt.savefig(
    lr_plot_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# ------------------------------------------------
# 6. EPOCH TRAINING TIME
# ------------------------------------------------

if "epoch_time_seconds" in history.columns:

    plt.figure(figsize=(10, 5))

    plt.plot(
        history["epoch"],
        history["epoch_time_seconds"],
        marker="o",
        linewidth=2
    )

    plt.xlabel("Epoch")
    plt.ylabel("Time (seconds)")
    plt.title("Training Time Per Epoch")

    plt.grid(alpha=0.3)
    plt.tight_layout()

    time_plot_path = PLOT_DIR / "epoch_training_time.png"

    plt.savefig(
        time_plot_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()

# ------------------------------------------------
# 7. TRAINING SUMMARY
# ------------------------------------------------

best_idx = history["validation_loss"].idxmin()

summary = {
    "epochs_completed": int(len(history)),
    "best_epoch": int(best_epoch),
    "best_validation_loss": float(best_val_loss),
    "final_training_loss": float(history.iloc[-1]["train_loss"]),
    "final_validation_loss": float(
        history.iloc[-1]["validation_loss"]
    ),
    "minimum_training_loss": float(
        history["train_loss"].min()
    ),
    "minimum_validation_loss": float(
        history["validation_loss"].min()
    )
}

print("\n" + "=" * 65)
print("TRAINING PERFORMANCE SUMMARY")
print("=" * 65)

for key, value in summary.items():
    print(f"{key}: {value}")

# ------------------------------------------------
# 8. SAVE VISUALIZATION SUMMARY
# ------------------------------------------------

with open(
    PLOT_DIR / "training_visualization_summary.json",
    "w"
) as f:

    json.dump(summary, f, indent=4)

print("\nSaved visualizations:")
print(loss_plot_path)
print(lr_plot_path)

if "epoch_time_seconds" in history.columns:
    print(time_plot_path)

print("\n" + "=" * 65)
print("CELL 14 COMPLETED SUCCESSFULLY")
print("=" * 65)


# ============================================================
# ORIGINAL NOTEBOOK CELL 18
# Execution count: 23
# ============================================================


# ================================================================
# CELL 15: TEST MODEL EVALUATION
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import json
import numpy as np
import pandas as pd
import torch

from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ------------------------------------------------
# 1. PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

TRAINING_DIR = PROJECT_ROOT / "outputs" / "model_training"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

EVALUATION_DIR = PROJECT_ROOT / "outputs" / "evaluation"
EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------
# 2. VERIFY MODEL
# ------------------------------------------------

assert "model" in globals(), "Run Cell 12 and Cell 13 first."
assert "DEVICE" in globals()
assert "ADJACENCY_TENSOR" in globals()

checkpoint_path = TRAINING_DIR / "best_gcn_gru_model.pth"

if not checkpoint_path.exists():
    raise FileNotFoundError(
        "Best model checkpoint not found. Run Cell 13."
    )

# Restore the best checkpoint saved by Cell 13.
try:
    checkpoint = torch.load(
        checkpoint_path,
        map_location=DEVICE,
        weights_only=False
    )
except TypeError:
    checkpoint = torch.load(
        checkpoint_path,
        map_location=DEVICE
    )

model.load_state_dict(checkpoint["model_state_dict"])
model.to(DEVICE)
model.eval()

print("Best checkpoint loaded.")
print("Best training epoch:", checkpoint["epoch"])
print("Best validation loss:", checkpoint["best_validation_loss"])

# ------------------------------------------------
# 3. LOAD TEST DATA
# ------------------------------------------------

X_test_seq = np.load(
    TRAINING_DIR / "X_test_seq.npy"
)

y_test_seq = np.load(
    TRAINING_DIR / "y_test_seq.npy"
)

spatial_nodes = pd.read_csv(
    PROCESSED_DIR / "spatial_nodes.csv"
)

test_dates = np.load(
    TRAINING_DIR / "test_dates.npy",
    allow_pickle=True
)

print("\nTest input shape:", X_test_seq.shape)
print("Test target shape:", y_test_seq.shape)
print("Spatial nodes:", len(spatial_nodes))
print("Test dates:", len(test_dates))

assert X_test_seq.shape == (12, 12, 255, 4)
assert y_test_seq.shape == (12, 255, 4)
assert len(spatial_nodes) == 255
assert len(test_dates) == 12

# ------------------------------------------------
# 4. SCALING PARAMETERS FROM CELL 9
# ------------------------------------------------

FEATURE_NAMES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

FEATURE_UNITS = {
    "T2M": "°C",
    "PRECTOTCORR": "mm/day",
    "RH2M": "%",
    "WS10M": "m/s"
}

# Training-only means and standard deviations
FEATURE_MEANS = np.array(
    [19.036497, 3.183543, 63.729874, 3.985626],
    dtype=np.float32
)

FEATURE_STDS = np.array(
    [13.484526, 4.811038, 19.049213, 1.667947],
    dtype=np.float32
)

assert np.all(FEATURE_STDS > 0)

def inverse_transform(data):
    return (
        data * FEATURE_STDS.reshape(1, 1, -1)
        + FEATURE_MEANS.reshape(1, 1, -1)
    )

# ------------------------------------------------
# 5. GENERATE MODEL PREDICTIONS
# ------------------------------------------------

BATCH_SIZE = 4

predictions_normalized = []

with torch.inference_mode():

    for start in range(0, len(X_test_seq), BATCH_SIZE):

        batch = torch.tensor(
            X_test_seq[start:start + BATCH_SIZE],
            dtype=torch.float32,
            device=DEVICE
        )

        output = model(
            batch,
            ADJACENCY_TENSOR
        )

        predictions_normalized.append(
            output.detach().cpu().numpy()
        )

predictions_normalized = np.concatenate(
    predictions_normalized,
    axis=0
)

actual_normalized = y_test_seq.copy()

print("\nNormalized prediction shape:")
print(predictions_normalized.shape)

assert predictions_normalized.shape == actual_normalized.shape

# ------------------------------------------------
# 6. PERSISTENCE BASELINE
# ------------------------------------------------

# Baseline assumes next month's value equals
# the last observed month's value.

persistence_normalized = X_test_seq[:, -1, :, :].copy()

# ------------------------------------------------
# 7. CONVERT TO ORIGINAL UNITS
# ------------------------------------------------

predictions = inverse_transform(
    predictions_normalized
)

actual = inverse_transform(
    actual_normalized
)

persistence_predictions = inverse_transform(
    persistence_normalized
)

print("\nPhysical-unit prediction shape:", predictions.shape)

# ------------------------------------------------
# 8. METRIC CALCULATION
# ------------------------------------------------

def calculate_metrics(y_true, y_pred):

    y_true_flat = y_true.reshape(-1)
    y_pred_flat = y_pred.reshape(-1)

    mae = mean_absolute_error(
        y_true_flat,
        y_pred_flat
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_true_flat,
            y_pred_flat
        )
    )

    r2 = r2_score(
        y_true_flat,
        y_pred_flat
    )

    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "R2": float(r2)
    }

# ------------------------------------------------
# 9. PER-FEATURE EVALUATION
# ------------------------------------------------

evaluation_results = []

for feature_index, feature_name in enumerate(FEATURE_NAMES):

    y_true = actual[:, :, feature_index]

    y_model = predictions[:, :, feature_index]

    y_baseline = persistence_predictions[:, :, feature_index]

    model_metrics = calculate_metrics(
        y_true,
        y_model
    )

    baseline_metrics = calculate_metrics(
        y_true,
        y_baseline
    )

    evaluation_results.append({
        "Feature": feature_name,
        "Unit": FEATURE_UNITS[feature_name],

        "GCN_GRU_MAE": model_metrics["MAE"],
        "GCN_GRU_RMSE": model_metrics["RMSE"],
        "GCN_GRU_R2": model_metrics["R2"],

        "Persistence_MAE": baseline_metrics["MAE"],
        "Persistence_RMSE": baseline_metrics["RMSE"],
        "Persistence_R2": baseline_metrics["R2"]
    })

results_df = pd.DataFrame(evaluation_results)

# ------------------------------------------------
# 10. CALCULATE IMPROVEMENT OVER BASELINE
# ------------------------------------------------

results_df["MAE_Improvement_Percent"] = (
    (
        results_df["Persistence_MAE"]
        - results_df["GCN_GRU_MAE"]
    )
    / results_df["Persistence_MAE"].replace(0, np.nan)
) * 100

results_df["RMSE_Improvement_Percent"] = (
    (
        results_df["Persistence_RMSE"]
        - results_df["GCN_GRU_RMSE"]
    )
    / results_df["Persistence_RMSE"].replace(0, np.nan)
) * 100

# ------------------------------------------------
# 11. PRINT RESULTS
# ------------------------------------------------

print("\n" + "=" * 100)
print("2024 TEST SET EVALUATION")
print("=" * 100)

print(
    results_df.round(4).to_string(index=False)
)

# ------------------------------------------------
# 12. SAVE PREDICTIONS
# ------------------------------------------------

np.save(
    EVALUATION_DIR / "gcn_gru_predictions_2024.npy",
    predictions
)

np.save(
    EVALUATION_DIR / "actual_values_2024.npy",
    actual
)

np.save(
    EVALUATION_DIR / "persistence_predictions_2024.npy",
    persistence_predictions
)

# ------------------------------------------------
# 13. SAVE NODE-WISE PREDICTION CSV
# ------------------------------------------------

rows = []

for time_index in range(len(test_dates)):

    for node_index in range(len(spatial_nodes)):

        node = spatial_nodes.iloc[node_index]

        row = {
            "date": str(test_dates[time_index]),
            "node_index": node_index
        }

        for coordinate in ["latitude", "longitude"]:

            if coordinate in spatial_nodes.columns:
                row[coordinate] = node[coordinate]

        for feature_index, feature_name in enumerate(FEATURE_NAMES):

            row[f"actual_{feature_name}"] = float(
                actual[time_index, node_index, feature_index]
            )

            row[f"predicted_{feature_name}"] = float(
                predictions[time_index, node_index, feature_index]
            )

            row[f"persistence_{feature_name}"] = float(
                persistence_predictions[
                    time_index, node_index, feature_index
                ]
            )

        rows.append(row)

predictions_df = pd.DataFrame(rows)

predictions_csv_path = (
    EVALUATION_DIR / "node_wise_predictions_2024.csv"
)

predictions_df.to_csv(
    predictions_csv_path,
    index=False
)

# ------------------------------------------------
# 14. SAVE METRICS
# ------------------------------------------------

metrics_csv_path = (
    EVALUATION_DIR / "evaluation_metrics_2024.csv"
)

results_df.to_csv(
    metrics_csv_path,
    index=False
)

report = {
    "evaluation_period": "January 2024 to December 2024",
    "model": "GCN-GRU",
    "baseline": "Persistence",
    "test_months": len(test_dates),
    "spatial_nodes": len(spatial_nodes),
    "features": FEATURE_NAMES,
    "best_training_epoch": int(checkpoint["epoch"]),
    "best_validation_loss": float(
        checkpoint["best_validation_loss"]
    ),
    "metrics": evaluation_results
}

with open(
    EVALUATION_DIR / "evaluation_report_2024.json",
    "w"
) as f:

    json.dump(report, f, indent=4)

# ------------------------------------------------
# 15. FINAL REPORT
# ------------------------------------------------

print("\n" + "=" * 75)
print("EVALUATION FILES SAVED")
print("=" * 75)

print("Predictions:", predictions_csv_path)
print("Metrics:", metrics_csv_path)

print(
    "Report:",
    EVALUATION_DIR / "evaluation_report_2024.json"
)

print("\n" + "=" * 75)
print("CELL 15 COMPLETED SUCCESSFULLY")
print("=" * 75)


# ============================================================
# ORIGINAL NOTEBOOK CELL 19
# Execution count: 26
# ============================================================


# ------------------------------------------------
# 3. VALIDATE ARRAYS AND COORDINATES
# ------------------------------------------------

if actual.shape != predictions.shape:
    raise ValueError("Actual and predicted shapes do not match.")

if actual.shape != persistence.shape:
    raise ValueError("Persistence array shape does not match.")

if actual.shape != (12, 255, 4):
    raise ValueError(
        f"Unexpected evaluation shape: {actual.shape}"
    )

if len(spatial_nodes) != actual.shape[1]:
    raise ValueError(
        "Spatial node count does not match prediction arrays."
    )

# Correct coordinate column names from spatial_nodes.csv
LAT_COL = "grid_latitude"
LON_COL = "grid_longitude"

required_columns = [
    "node_id",
    LAT_COL,
    LON_COL
]

missing_columns = [
    col for col in required_columns
    if col not in spatial_nodes.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: {missing_columns}"
    )

# Extract coordinates
latitudes = spatial_nodes[LAT_COL].to_numpy()
longitudes = spatial_nodes[LON_COL].to_numpy()

if not (
    np.isfinite(latitudes).all()
    and np.isfinite(longitudes).all()
):
    raise ValueError("Invalid spatial coordinates detected.")

if len(test_dates) != actual.shape[0]:
    raise ValueError("Test dates do not match prediction months.")

if not (
    np.isfinite(actual).all()
    and np.isfinite(predictions).all()
):
    raise ValueError("Evaluation arrays contain non-finite values.")

print("Evaluation data validated successfully.")
print("Actual shape:", actual.shape)
print("Predicted shape:", predictions.shape)
print("Spatial nodes:", len(spatial_nodes))
print("Latitude range:", latitudes.min(), "to", latitudes.max())
print("Longitude range:", longitudes.min(), "to", longitudes.max())
print("Test months:", len(test_dates))


# ============================================================
# ORIGINAL NOTEBOOK CELL 20
# Execution count: 25
# ============================================================

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

spatial_nodes = pd.read_csv(
    PROJECT_ROOT / "data" / "processed" / "spatial_nodes.csv"
)

print("Columns:")
print(spatial_nodes.columns.tolist())

print("\nFirst 5 rows:")
display(spatial_nodes.head())

print("\nData types:")
print(spatial_nodes.dtypes)


# ============================================================
# ORIGINAL NOTEBOOK CELL 21
# Execution count: 27
# ============================================================


# ================================================================
# CELL 17: AUTOREGRESSIVE FUTURE CLIMATE FORECASTING
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import numpy as np
import pandas as pd
import torch
import scipy.sparse as sp
import json

from pathlib import Path

# ------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
GRAPH_DIR = PROJECT_ROOT / "outputs" / "spatial_graph"
MODEL_DIR = PROJECT_ROOT / "outputs" / "model_training"

FORECAST_DIR = PROJECT_ROOT / "outputs" / "future_forecasting"

FORECAST_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ------------------------------------------------
# 2. CONFIGURATION
# ------------------------------------------------

FORECAST_MONTHS = 12
SEQUENCE_LENGTH = 12

FEATURE_NAMES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

FEATURE_UNITS = {
    "T2M": "°C",
    "PRECTOTCORR": "mm/day",
    "RH2M": "%",
    "WS10M": "m/s"
}

# Training-only normalization statistics from Cell 9
FEATURE_MEAN = np.array(
    [19.036497, 3.183543, 63.729874, 3.985626],
    dtype=np.float32
)

FEATURE_STD = np.array(
    [13.484526, 4.811038, 19.049213, 1.667947],
    dtype=np.float32
)

# ------------------------------------------------
# 3. DEVICE AND MODEL VALIDATION
# ------------------------------------------------

if "model" not in globals():
    raise RuntimeError(
        "Trained model not found. Run Cell 15 first "
        "to load the best checkpoint."
    )

model.eval()

device = next(model.parameters()).device

print("Model:", model.__class__.__name__)
print("Device:", device)

# ------------------------------------------------
# 4. LOAD COMPLETE HISTORICAL TENSOR
# ------------------------------------------------

tensor_path = (
    PROCESSED_DIR / "nasa_power_tensor.npy"
)

historical_tensor = np.load(tensor_path)

print("\nHistorical tensor:", historical_tensor.shape)

if historical_tensor.shape != (120, 255, 4):
    raise ValueError(
        f"Unexpected historical tensor shape: "
        f"{historical_tensor.shape}"
    )

if not np.isfinite(historical_tensor).all():
    raise ValueError(
        "Historical tensor contains invalid values."
    )

# ------------------------------------------------
# 5. NORMALIZE HISTORICAL DATA
# ------------------------------------------------

historical_normalized = (
    historical_tensor - FEATURE_MEAN
) / FEATURE_STD

historical_normalized = historical_normalized.astype(
    np.float32
)

# Last 12 observed months: January–December 2024
forecast_input = historical_normalized[
    -SEQUENCE_LENGTH:
].copy()

print(
    "Initial forecast input:",
    forecast_input.shape
)

# ------------------------------------------------
# 6. LOAD SPATIAL ADJACENCY MATRIX
# ------------------------------------------------

adjacency_path = (
    GRAPH_DIR / "adjacency_matrix.npz"
)

adjacency = sp.load_npz(adjacency_path).toarray()

if adjacency.shape != (255, 255):
    raise ValueError(
        f"Unexpected adjacency shape: {adjacency.shape}"
    )

# Symmetric GCN normalization:
# A_norm = D^(-1/2) A D^(-1/2)

degree = np.asarray(
    adjacency.sum(axis=1)
).flatten()

degree_inv_sqrt = np.zeros_like(
    degree,
    dtype=np.float32
)

nonzero = degree > 0

degree_inv_sqrt[nonzero] = (
    1.0 / np.sqrt(degree[nonzero])
)

normalized_adjacency = (
    degree_inv_sqrt[:, None]
    * adjacency
    * degree_inv_sqrt[None, :]
)

adjacency_tensor = torch.tensor(
    normalized_adjacency,
    dtype=torch.float32,
    device=device
)

print("Normalized adjacency:", adjacency_tensor.shape)

# ------------------------------------------------
# 7. MODEL FORWARD-PASS VALIDATION
# ------------------------------------------------

test_input = torch.tensor(
    forecast_input[np.newaxis, ...],
    dtype=torch.float32,
    device=device
)

with torch.no_grad():

    test_output = model(
        test_input,
        adjacency_tensor
    )

if isinstance(test_output, tuple):
    test_output = test_output[0]

if test_output.shape != (1, 255, 4):
    raise ValueError(
        f"Unexpected model output shape: {test_output.shape}"
    )

print("Model forward pass validated:", test_output.shape)

# ------------------------------------------------
# 8. AUTOREGRESSIVE FORECASTING
# ------------------------------------------------

model.eval()

forecast_normalized = []

current_window = forecast_input.copy()

print("\nStarting autoregressive forecasting...")

with torch.no_grad():

    for month in range(FORECAST_MONTHS):

        input_tensor = torch.tensor(
            current_window[np.newaxis, ...],
            dtype=torch.float32,
            device=device
        )

        prediction = model(
            input_tensor,
            adjacency_tensor
        )

        if isinstance(prediction, tuple):
            prediction = prediction[0]

        prediction = prediction.detach().cpu().numpy()[0]

        if prediction.shape != (255, 4):
            raise ValueError(
                f"Invalid prediction shape: {prediction.shape}"
            )

        forecast_normalized.append(prediction)

        # Append predicted month and remove oldest month
        current_window = np.concatenate(
            [
                current_window[1:],
                prediction[np.newaxis, :, :]
            ],
            axis=0
        )

        print(
            f"Forecast month {month + 1}/{FORECAST_MONTHS} completed."
        )

forecast_normalized = np.stack(
    forecast_normalized,
    axis=0
)

print(
    "\nNormalized forecast shape:",
    forecast_normalized.shape
)

# ------------------------------------------------
# 9. INVERSE NORMALIZATION
# ------------------------------------------------

forecast_physical = (
    forecast_normalized * FEATURE_STD
) + FEATURE_MEAN

print(
    "Physical forecast shape:",
    forecast_physical.shape
)

if not np.isfinite(forecast_physical).all():
    raise ValueError(
        "Forecast contains NaN or infinite values."
    )

# ------------------------------------------------
# 10. SAVE FORECAST ARRAYS
# ------------------------------------------------

np.save(
    FORECAST_DIR / "forecast_2025_normalized.npy",
    forecast_normalized
)

np.save(
    FORECAST_DIR / "forecast_2025_physical.npy",
    forecast_physical
)

# ------------------------------------------------
# 11. LOAD SPATIAL NODE COORDINATES
# ------------------------------------------------

spatial_nodes = pd.read_csv(
    PROCESSED_DIR / "spatial_nodes.csv"
)

if len(spatial_nodes) != 255:
    raise ValueError(
        "Spatial node count mismatch."
    )

# ------------------------------------------------
# 12. CREATE FORECAST CSV
# ------------------------------------------------

forecast_dates = pd.date_range(
    start="2025-01-01",
    periods=FORECAST_MONTHS,
    freq="MS"
)

records = []

for month_index, forecast_date in enumerate(forecast_dates):

    for node_index in range(255):

        record = {
            "date": forecast_date.strftime("%Y-%m"),
            "node_id": spatial_nodes.iloc[node_index]["node_id"],
            "grid_latitude": spatial_nodes.iloc[node_index]["grid_latitude"],
            "grid_longitude": spatial_nodes.iloc[node_index]["grid_longitude"]
        }

        for feature_index, feature_name in enumerate(FEATURE_NAMES):

            record[feature_name] = float(
                forecast_physical[
                    month_index,
                    node_index,
                    feature_index
                ]
            )

        records.append(record)

forecast_df = pd.DataFrame(records)

forecast_csv = (
    FORECAST_DIR / "india_climate_forecast_2025.csv"
)

forecast_df.to_csv(
    forecast_csv,
    index=False
)

# ------------------------------------------------
# 13. MONTHLY REGIONAL SUMMARY
# ------------------------------------------------

summary_records = []

for month_index, forecast_date in enumerate(forecast_dates):

    row = {
        "date": forecast_date.strftime("%Y-%m")
    }

    for feature_index, feature_name in enumerate(FEATURE_NAMES):

        values = forecast_physical[
            month_index, :, feature_index
        ]

        row[f"{feature_name}_mean"] = float(
            np.mean(values)
        )

        row[f"{feature_name}_minimum"] = float(
            np.min(values)
        )

        row[f"{feature_name}_maximum"] = float(
            np.max(values)
        )

    summary_records.append(row)

summary_df = pd.DataFrame(summary_records)

summary_path = (
    FORECAST_DIR / "forecast_monthly_summary_2025.csv"
)

summary_df.to_csv(
    summary_path,
    index=False
)

# ------------------------------------------------
# 14. SAVE FORECAST METADATA
# ------------------------------------------------

metadata = {
    "project": "NASA Earth Systems Trend Detective",
    "model": model.__class__.__name__,
    "forecast_method": "Autoregressive GCN-GRU",
    "forecast_period": "January 2025 to December 2025",
    "historical_period": "January 2015 to December 2024",
    "forecast_months": FORECAST_MONTHS,
    "sequence_length": SEQUENCE_LENGTH,
    "spatial_nodes": 255,
    "features": FEATURE_NAMES,
    "feature_units": FEATURE_UNITS,
    "input_shape": list(forecast_input.shape),
    "output_shape": list(forecast_physical.shape),
    "normalization": "Training-set mean and standard deviation",
    "limitations": [
        "Experimental autoregressive extrapolation",
        "Model trained on 2015-2021 observations",
        "No external future climate forcing supplied",
        "Prediction errors may accumulate during recursive forecasting",
        "Not an operational climate forecast"
    ]
}

with open(
    FORECAST_DIR / "forecast_metadata.json",
    "w"
) as f:

    json.dump(metadata, f, indent=4)

# ------------------------------------------------
# 15. FINAL REPORT
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 17 COMPLETED SUCCESSFULLY")
print("=" * 75)

print("Forecast period: January–December 2025")
print("Spatial nodes:", len(spatial_nodes))
print("Features:", len(FEATURE_NAMES))
print("Forecast shape:", forecast_physical.shape)

print("\nMonthly regional forecast summary:")
display(summary_df.round(3))

print("\nSaved files:")
print(forecast_csv)
print(summary_path)
print(FORECAST_DIR / "forecast_2025_physical.npy")
print(FORECAST_DIR / "forecast_metadata.json")


# ============================================================
# ORIGINAL NOTEBOOK CELL 22
# Execution count: 28
# ============================================================


# ================================================================
# CELL 18: FUTURE FORECAST VISUALIZATION
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json

from pathlib import Path

# ------------------------------------------------
# 1. PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

FORECAST_DIR = (
    PROJECT_ROOT / "outputs" / "future_forecasting"
)

PROCESSED_DIR = (
    PROJECT_ROOT / "data" / "processed"
)

VIS_DIR = (
    PROJECT_ROOT / "outputs" / "visualizations" / "forecast_2025"
)

VIS_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------
# 2. LOAD FORECAST DATA
# ------------------------------------------------

forecast = np.load(
    FORECAST_DIR / "forecast_2025_physical.npy"
)

spatial_nodes = pd.read_csv(
    PROCESSED_DIR / "spatial_nodes.csv"
)

forecast_dates = pd.date_range(
    start="2025-01-01",
    periods=12,
    freq="MS"
)

FEATURE_NAMES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

FEATURE_UNITS = {
    "T2M": "°C",
    "PRECTOTCORR": "mm/day",
    "RH2M": "%",
    "WS10M": "m/s"
}

# ------------------------------------------------
# 3. VALIDATE DATA
# ------------------------------------------------

if forecast.shape != (12, 255, 4):
    raise ValueError(
        f"Unexpected forecast shape: {forecast.shape}"
    )

if len(spatial_nodes) != 255:
    raise ValueError(
        "Spatial node count mismatch."
    )

if not np.isfinite(forecast).all():
    raise ValueError(
        "Forecast contains NaN or infinite values."
    )

latitudes = spatial_nodes[
    "grid_latitude"
].to_numpy()

longitudes = spatial_nodes[
    "grid_longitude"
].to_numpy()

print("Forecast loaded:", forecast.shape)
print("Spatial nodes:", len(spatial_nodes))

# ------------------------------------------------
# 4. MONTHLY REGIONAL MEAN TRENDS
# ------------------------------------------------

summary_records = []

for month_index, date in enumerate(forecast_dates):

    row = {
        "date": date.strftime("%Y-%m")
    }

    for feature_index, feature_name in enumerate(FEATURE_NAMES):

        values = forecast[
            month_index, :, feature_index
        ]

        row[f"{feature_name}_mean"] = np.mean(values)
        row[f"{feature_name}_min"] = np.min(values)
        row[f"{feature_name}_max"] = np.max(values)
        row[f"{feature_name}_std"] = np.std(values)

    summary_records.append(row)

summary_df = pd.DataFrame(summary_records)

summary_df.to_csv(
    VIS_DIR / "forecast_regional_summary_2025.csv",
    index=False
)

# ------------------------------------------------
# 5. PLOT MONTHLY FORECAST TRENDS
# ------------------------------------------------

for feature_index, feature_name in enumerate(FEATURE_NAMES):

    monthly_mean = np.mean(
        forecast[:, :, feature_index],
        axis=1
    )

    monthly_min = np.min(
        forecast[:, :, feature_index],
        axis=1
    )

    monthly_max = np.max(
        forecast[:, :, feature_index],
        axis=1
    )

    plt.figure(figsize=(12, 6))

    plt.plot(
        forecast_dates,
        monthly_mean,
        marker="o",
        linewidth=2,
        label="Regional mean"
    )

    plt.fill_between(
        forecast_dates,
        monthly_min,
        monthly_max,
        alpha=0.2,
        label="Spatial minimum–maximum range"
    )

    plt.title(
        f"Experimental 2025 Forecast: {feature_name}"
    )

    plt.xlabel("Month")
    plt.ylabel(
        f"{feature_name} ({FEATURE_UNITS[feature_name]})"
    )

    plt.xticks(
        forecast_dates,
        [date.strftime("%b") for date in forecast_dates],
        rotation=45
    )

    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()

    output_path = (
        VIS_DIR / f"{feature_name}_forecast_trend_2025.png"
    )

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()

    print("Saved:", output_path)

# ------------------------------------------------
# 6. SPATIAL FORECAST MAPS
# ------------------------------------------------

# January, June and December
selected_months = [0, 5, 11]

for month_index in selected_months:

    forecast_date = forecast_dates[month_index]

    for feature_index, feature_name in enumerate(FEATURE_NAMES):

        values = forecast[
            month_index, :, feature_index
        ]

        plt.figure(figsize=(10, 7))

        scatter = plt.scatter(
            longitudes,
            latitudes,
            c=values,
            cmap="viridis",
            s=55
        )

        plt.colorbar(
            scatter,
            label=f"{feature_name} ({FEATURE_UNITS[feature_name]})"
        )

        plt.xlabel("Longitude")
        plt.ylabel("Latitude")

        plt.title(
            f"Experimental Spatial Forecast: "
            f"{feature_name} - {forecast_date.strftime('%B %Y')}"
        )

        plt.grid(alpha=0.2)
        plt.tight_layout()

        output_path = (
            VIS_DIR
            / f"{feature_name}_{forecast_date.strftime('%B').lower()}_2025.png"
        )

        plt.savefig(
            output_path,
            dpi=300,
            bbox_inches="tight"
        )

        plt.show()

        print("Saved:", output_path)

# ------------------------------------------------
# 7. PHYSICAL-VALUE QUALITY CHECK
# ------------------------------------------------

quality_report = {}

for feature_index, feature_name in enumerate(FEATURE_NAMES):

    values = forecast[:, :, feature_index]

    quality_report[feature_name] = {
        "minimum": float(np.min(values)),
        "maximum": float(np.max(values)),
        "mean": float(np.mean(values)),
        "negative_value_count": int(np.sum(values < 0)),
        "non_finite_count": int(np.sum(~np.isfinite(values)))
    }

# These are plausibility flags, not automatic corrections.
quality_report["plausibility_flags"] = {
    "negative_precipitation": bool(
        np.any(forecast[:, :, 1] < 0)
    ),
    "humidity_below_zero": bool(
        np.any(forecast[:, :, 2] < 0)
    ),
    "humidity_above_100": bool(
        np.any(forecast[:, :, 2] > 100)
    ),
    "negative_wind_speed": bool(
        np.any(forecast[:, :, 3] < 0)
    )
}

with open(
    VIS_DIR / "forecast_quality_report.json",
    "w"
) as f:

    json.dump(
        quality_report,
        f,
        indent=4
    )

# ------------------------------------------------
# 8. FINAL SUMMARY
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 18 COMPLETED SUCCESSFULLY")
print("=" * 75)

print("\n2025 Monthly Regional Forecast:")
display(summary_df.round(3))

print("\nPhysical plausibility checks:")
print(json.dumps(
    quality_report["plausibility_flags"],
    indent=4
))

print("\nVisualization directory:")
print(VIS_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 23
# Execution count: 29
# ============================================================


# ================================================================
# CELL 19: FORECAST PHYSICAL PLAUSIBILITY ANALYSIS
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

# ------------------------------------------------
# 1. PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

FORECAST_DIR = (
    PROJECT_ROOT / "outputs" / "future_forecasting"
)

QUALITY_DIR = (
    PROJECT_ROOT / "outputs" / "quality_analysis"
)

QUALITY_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------

historical = np.load(
    PROCESSED_DIR / "nasa_power_tensor.npy"
)

forecast = np.load(
    FORECAST_DIR / "forecast_2025_physical.npy"
)

spatial_nodes = pd.read_csv(
    PROCESSED_DIR / "spatial_nodes.csv"
)

FEATURE_NAMES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

# ------------------------------------------------
# 3. VALIDATE
# ------------------------------------------------

if historical.shape != (120, 255, 4):
    raise ValueError(
        f"Unexpected historical shape: {historical.shape}"
    )

if forecast.shape != (12, 255, 4):
    raise ValueError(
        f"Unexpected forecast shape: {forecast.shape}"
    )

# ------------------------------------------------
# 4. HISTORICAL VS FORECAST RANGES
# ------------------------------------------------

range_records = []

for feature_index, feature_name in enumerate(FEATURE_NAMES):

    historical_values = historical[
        :, :, feature_index
    ]

    forecast_values = forecast[
        :, :, feature_index
    ]

    range_records.append({

        "feature": feature_name,

        "historical_min": float(
            np.min(historical_values)
        ),

        "historical_max": float(
            np.max(historical_values)
        ),

        "historical_mean": float(
            np.mean(historical_values)
        ),

        "forecast_min": float(
            np.min(forecast_values)
        ),

        "forecast_max": float(
            np.max(forecast_values)
        ),

        "forecast_mean": float(
            np.mean(forecast_values)
        ),

        "outside_historical_range_count": int(
            np.sum(
                (forecast_values < np.min(historical_values))
                |
                (forecast_values > np.max(historical_values))
            )
        )
    })

range_df = pd.DataFrame(range_records)

print("\nHISTORICAL VS FORECAST RANGE")
display(range_df.round(4))

range_df.to_csv(
    QUALITY_DIR / "historical_forecast_range_comparison.csv",
    index=False
)

# ------------------------------------------------
# 5. IDENTIFY NEGATIVE PRECIPITATION NODES
# ------------------------------------------------

negative_records = []

for month_index in range(12):

    for node_index in range(255):

        precipitation = forecast[
            month_index,
            node_index,
            1
        ]

        if precipitation < 0:

            negative_records.append({

                "month": month_index + 1,

                "node_id": spatial_nodes.iloc[
                    node_index
                ]["node_id"],

                "latitude": spatial_nodes.iloc[
                    node_index
                ]["grid_latitude"],

                "longitude": spatial_nodes.iloc[
                    node_index
                ]["grid_longitude"],

                "predicted_precipitation_mm_day": float(
                    precipitation
                )
            })

negative_df = pd.DataFrame(
    negative_records
)

negative_df.to_csv(
    QUALITY_DIR / "negative_precipitation_nodes.csv",
    index=False
)

print("\nNEGATIVE PRECIPITATION ANALYSIS")

print(
    "Negative predictions:",
    len(negative_df)
)

print(
    "Total forecast values:",
    12 * 255
)

if not negative_df.empty:

    display(
        negative_df.head(20).round(4)
    )

# ------------------------------------------------
# 6. IDENTIFY EXTREME TEMPERATURE NODES
# ------------------------------------------------

temperature_records = []

historical_temperature = historical[:, :, 0]

historical_global_min = np.min(
    historical_temperature
)

historical_global_max = np.max(
    historical_temperature
)

for month_index in range(12):

    for node_index in range(255):

        value = forecast[
            month_index,
            node_index,
            0
        ]

        if (
            value < historical_global_min
            or value > historical_global_max
        ):

            temperature_records.append({

                "month": month_index + 1,

                "node_id": spatial_nodes.iloc[
                    node_index
                ]["node_id"],

                "latitude": spatial_nodes.iloc[
                    node_index
                ]["grid_latitude"],

                "longitude": spatial_nodes.iloc[
                    node_index
                ]["grid_longitude"],

                "forecast_temperature": float(value),

                "historical_global_min": float(
                    historical_global_min
                ),

                "historical_global_max": float(
                    historical_global_max
                )
            })

temperature_df = pd.DataFrame(
    temperature_records
)

temperature_df.to_csv(
    QUALITY_DIR / "temperature_outside_historical_range.csv",
    index=False
)

print("\nTEMPERATURE RANGE ANALYSIS")

print(
    "Values outside historical global range:",
    len(temperature_df)
)

# ------------------------------------------------
# 7. PHYSICAL CONSTRAINT SUMMARY
# ------------------------------------------------

constraint_summary = {

    "negative_precipitation_count": int(
        np.sum(forecast[:, :, 1] < 0)
    ),

    "negative_wind_speed_count": int(
        np.sum(forecast[:, :, 3] < 0)
    ),

    "humidity_below_zero_count": int(
        np.sum(forecast[:, :, 2] < 0)
    ),

    "humidity_above_100_count": int(
        np.sum(forecast[:, :, 2] > 100)
    ),

    "temperature_outside_historical_range_count": int(
        len(temperature_df)
    )
}

print("\nPHYSICAL CONSTRAINT SUMMARY")

for key, value in constraint_summary.items():

    print(f"{key}: {value}")

# ------------------------------------------------
# 8. SAVE QUALITY REPORT
# ------------------------------------------------

import json

with open(
    QUALITY_DIR / "physical_plausibility_report.json",
    "w"
) as f:

    json.dump(
        constraint_summary,
        f,
        indent=4
    )

print("\n" + "=" * 70)
print("CELL 19 COMPLETED SUCCESSFULLY")
print("=" * 70)

print("Quality analysis directory:")
print(QUALITY_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 24
# Execution count: 30
# ============================================================


# ================================================================
# CELL 20: SEASONAL MANN-KENDALL AND SEN'S SLOPE
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json

from pathlib import Path
from scipy.stats import norm

# ------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TREND_DIR = (
    PROJECT_ROOT / "outputs" / "historical_trend_analysis"
)

TREND_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ------------------------------------------------
# 2. CONFIGURATION
# ------------------------------------------------

FEATURE_NAMES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

FEATURE_UNITS = {
    "T2M": "°C/year",
    "PRECTOTCORR": "mm/day/year",
    "RH2M": "%/year",
    "WS10M": "m/s/year"
}

ALPHA = 0.05

# ------------------------------------------------
# 3. LOAD HISTORICAL DATA
# ------------------------------------------------

historical = np.load(
    PROCESSED_DIR / "nasa_power_tensor.npy"
)

spatial_nodes = pd.read_csv(
    PROCESSED_DIR / "spatial_nodes.csv"
)

time_index = np.load(
    PROCESSED_DIR / "tensor_time_index.npy",
    allow_pickle=True
)

dates = pd.to_datetime(time_index)

print("Historical tensor:", historical.shape)
print("Spatial nodes:", len(spatial_nodes))
print("Time observations:", len(dates))

if historical.shape != (120, 255, 4):
    raise ValueError(
        f"Unexpected historical tensor shape: {historical.shape}"
    )

if len(dates) != 120:
    raise ValueError("Time index length mismatch.")

if len(spatial_nodes) != 255:
    raise ValueError("Spatial node count mismatch.")

if not np.isfinite(historical).all():
    raise ValueError("Historical data contains invalid values.")

if not dates.is_monotonic_increasing:
    raise ValueError("Dates are not chronologically sorted.")

# ------------------------------------------------
# 4. SEASONAL MANN-KENDALL AND SEN'S SLOPE
# ------------------------------------------------

def seasonal_mann_kendall_sen(values, dates):

    """
    Seasonal Mann-Kendall test and seasonal Sen's slope.

    Compares observations from the same calendar month
    across different years.

    Slope unit: feature unit per year.
    """

    values = np.asarray(values, dtype=float)

    date_series = pd.DatetimeIndex(dates)

    if len(values) != len(date_series):
        raise ValueError("Values and dates length mismatch.")

    if len(values) < 24:
        return np.nan, np.nan, np.nan, "insufficient_data"

    slopes = []
    total_s = 0
    total_variance = 0

    for month in range(1, 13):

        mask = date_series.month == month

        month_values = values[mask]

        month_years = (
            date_series[mask].year.to_numpy()
        )

        n = len(month_values)

        if n < 2:
            continue

        # Mann-Kendall S statistic for this calendar month
        for i in range(n - 1):

            differences = (
                month_values[i + 1:] - month_values[i]
            )

            total_s += np.sum(
                np.sign(differences)
            )

            # Sen slope for all within-month pairs
            year_differences = (
                month_years[i + 1:] - month_years[i]
            )

            valid = year_differences != 0

            if np.any(valid):

                slopes.extend(
                    (
                        differences[valid]
                        / year_differences[valid]
                    ).tolist()
                )

        # Tie-corrected variance for this month
        _, tie_counts = np.unique(
            month_values,
            return_counts=True
        )

        tie_term = np.sum(
            tie_counts * (tie_counts - 1) * (2 * tie_counts + 5)
        )

        total_variance += (
            n * (n - 1) * (2 * n + 5) - tie_term
        ) / 18.0

    if total_variance <= 0 or len(slopes) == 0:
        return np.nan, np.nan, np.nan, "no_variation"

    # Continuity correction
    if total_s > 0:
        z_score = (
            total_s - 1
        ) / np.sqrt(total_variance)

    elif total_s < 0:
        z_score = (
            total_s + 1
        ) / np.sqrt(total_variance)

    else:
        z_score = 0.0

    p_value = 2 * norm.sf(
        abs(z_score)
    )

    sen_slope = float(
        np.median(slopes)
    )

    if p_value < 0.05 and sen_slope > 0:
        trend = "significant_increasing"

    elif p_value < 0.05 and sen_slope < 0:
        trend = "significant_decreasing"

    elif sen_slope > 0:
        trend = "non_significant_increasing"

    elif sen_slope < 0:
        trend = "non_significant_decreasing"

    else:
        trend = "no_trend"

    return (
        float(total_s),
        float(z_score),
        float(p_value),
        trend,
        sen_slope
    )

# ------------------------------------------------
# 5. BENJAMINI-HOCHBERG FDR CORRECTION
# ------------------------------------------------

def benjamini_hochberg(p_values):

    """
    Benjamini-Hochberg false discovery rate correction.
    Returns adjusted p-values in original order.
    """

    p_values = np.asarray(
        p_values,
        dtype=float
    )

    adjusted = np.full(
        p_values.shape,
        np.nan,
        dtype=float
    )

    valid = np.isfinite(p_values)

    p = p_values[valid]

    if len(p) == 0:
        return adjusted

    n = len(p)

    order = np.argsort(p)

    sorted_p = p[order]

    ranks = np.arange(1, n + 1)

    sorted_adjusted = (
        sorted_p * n / ranks
    )

    sorted_adjusted = np.minimum.accumulate(
        sorted_adjusted[::-1]
    )[::-1]

    sorted_adjusted = np.clip(
        sorted_adjusted,
        0,
        1
    )

    restored = np.empty_like(
        sorted_adjusted
    )

    restored[order] = sorted_adjusted

    adjusted[valid] = restored

    return adjusted

# ------------------------------------------------
# 6. CALCULATE NODE-WISE TRENDS
# ------------------------------------------------

trend_records = []

print("\nStarting seasonal trend analysis...")

for feature_index, feature_name in enumerate(FEATURE_NAMES):

    print(
        f"\nAnalyzing feature: {feature_name}"
    )

    for node_index in range(255):

        values = historical[
            :, node_index, feature_index
        ]

        result = seasonal_mann_kendall_sen(
            values,
            dates
        )

        if len(result) == 4:
            s_value, z_score, p_value, trend = result
            slope = np.nan
        else:
            s_value, z_score, p_value, trend, slope = result

        trend_records.append({

            "node_index": node_index,

            "node_id": spatial_nodes.iloc[
                node_index
            ]["node_id"],

            "latitude": spatial_nodes.iloc[
                node_index
            ]["grid_latitude"],

            "longitude": spatial_nodes.iloc[
                node_index
            ]["grid_longitude"],

            "feature": feature_name,

            "mann_kendall_S": s_value,

            "z_score": z_score,

            "p_value": p_value,

            "sen_slope_per_year": slope,

            "trend": trend
        })

    print(
        f"Completed: {feature_name}"
    )

trend_df = pd.DataFrame(
    trend_records
)

# ------------------------------------------------
# 7. APPLY FDR CORRECTION
# ------------------------------------------------

trend_df["fdr_adjusted_p"] = (
    benjamini_hochberg(
        trend_df["p_value"].to_numpy()
    )
)

trend_df["fdr_significant"] = (
    trend_df["fdr_adjusted_p"] < ALPHA
)

# Final classification after FDR correction
trend_df["fdr_trend"] = "not_significant"

trend_df.loc[
    trend_df["fdr_significant"]
    & (trend_df["sen_slope_per_year"] > 0),
    "fdr_trend"
] = "significant_increasing"

trend_df.loc[
    trend_df["fdr_significant"]
    & (trend_df["sen_slope_per_year"] < 0),
    "fdr_trend"
] = "significant_decreasing"

# ------------------------------------------------
# 8. SAVE NODE-WISE RESULTS
# ------------------------------------------------

node_results_path = (
    TREND_DIR / "node_wise_seasonal_trends.csv"
)

trend_df.to_csv(
    node_results_path,
    index=False
)

# ------------------------------------------------
# 9. FEATURE-WISE SUMMARY
# ------------------------------------------------

summary_records = []

for feature_name in FEATURE_NAMES:

    subset = trend_df[
        trend_df["feature"] == feature_name
    ]

    significant = subset[
        subset["fdr_significant"]
    ]

    summary_records.append({

        "feature": feature_name,

        "spatial_nodes": len(subset),

        "mean_sen_slope": subset[
            "sen_slope_per_year"
        ].mean(),

        "median_sen_slope": subset[
            "sen_slope_per_year"
        ].median(),

        "significant_nodes_after_fdr": len(significant),

        "increasing_nodes_after_fdr": int(
            (
                significant["sen_slope_per_year"] > 0
            ).sum()
        ),

        "decreasing_nodes_after_fdr": int(
            (
                significant["sen_slope_per_year"] < 0
            ).sum()
        ),

        "alpha": ALPHA
    })

summary_df = pd.DataFrame(
    summary_records
)

summary_path = (
    TREND_DIR / "feature_trend_summary.csv"
)

summary_df.to_csv(
    summary_path,
    index=False
)

# ------------------------------------------------
# 10. FEATURE-WISE SPATIAL TREND MAPS
# ------------------------------------------------

for feature_name in FEATURE_NAMES:

    subset = trend_df[
        trend_df["feature"] == feature_name
    ]

    plt.figure(figsize=(11, 7))

    scatter = plt.scatter(
        subset["longitude"],
        subset["latitude"],
        c=subset["sen_slope_per_year"],
        cmap="coolwarm",
        s=65
    )

    plt.colorbar(
        scatter,
        label=FEATURE_UNITS[feature_name]
    )

    significant = subset[
        subset["fdr_significant"]
    ]

    if not significant.empty:

        plt.scatter(
            significant["longitude"],
            significant["latitude"],
            facecolors="none",
            edgecolors="black",
            s=110,
            linewidths=1.2,
            label="FDR significant"
        )

        plt.legend()

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    plt.title(
        f"2015–2024 Seasonal Sen's Slope: {feature_name}"
    )

    plt.grid(alpha=0.2)
    plt.tight_layout()

    output_path = (
        TREND_DIR / f"{feature_name}_sen_slope_map.png"
    )

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()

    print("Saved:", output_path)

# ------------------------------------------------
# 11. SAVE ANALYSIS METADATA
# ------------------------------------------------

metadata = {

    "project": "NASA Earth Systems Trend Detective",

    "analysis": "Seasonal Mann-Kendall and Sen's slope",

    "historical_period": "2015-01 to 2024-12",

    "spatial_nodes": 255,

    "features": FEATURE_NAMES,

    "seasonal_method": (
        "Same-calendar-month comparisons across years"
    ),

    "multiple_testing_correction": (
        "Benjamini-Hochberg false discovery rate"
    ),

    "fdr_alpha": ALPHA,

    "slope_unit": FEATURE_UNITS,

    "important_limitation": (
        "Results describe trends in the gridded NASA POWER "
        "variables and should not be interpreted as causal effects."
    )
}

with open(
    TREND_DIR / "trend_analysis_metadata.json",
    "w"
) as f:

    json.dump(
        metadata,
        f,
        indent=4
    )

# ------------------------------------------------
# 12. FINAL REPORT
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 20 COMPLETED SUCCESSFULLY")
print("=" * 75)

print("\nFEATURE-WISE TREND SUMMARY")

display(
    summary_df.round(5)
)

print("\nSaved files:")
print(node_results_path)
print(summary_path)
print(TREND_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 25
# Execution count: 31
# ============================================================


# ================================================================
# CELL 21: TEMPORAL AUTOCORRELATION DIAGNOSTICS
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import numpy as np
import pandas as pd
import json

from pathlib import Path
from scipy.stats import pearsonr

# ------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TREND_DIR = (
    PROJECT_ROOT / "outputs" / "historical_trend_analysis"
)

AUTOCORR_DIR = (
    PROJECT_ROOT / "outputs" / "autocorrelation_analysis"
)

AUTOCORR_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ------------------------------------------------
# 2. CONFIGURATION
# ------------------------------------------------

FEATURE_NAMES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

LAGS = [1, 12]

CORRELATION_THRESHOLD = 0.20

# ------------------------------------------------
# 3. LOAD HISTORICAL DATA
# ------------------------------------------------

historical = np.load(
    PROCESSED_DIR / "nasa_power_tensor.npy"
)

spatial_nodes = pd.read_csv(
    PROCESSED_DIR / "spatial_nodes.csv"
)

time_index = np.load(
    PROCESSED_DIR / "tensor_time_index.npy",
    allow_pickle=True
)

dates = pd.DatetimeIndex(
    pd.to_datetime(time_index)
)

print("Historical tensor:", historical.shape)
print("Spatial nodes:", len(spatial_nodes))
print("Time observations:", len(dates))

if historical.shape != (120, 255, 4):
    raise ValueError("Unexpected tensor shape.")

if not np.isfinite(historical).all():
    raise ValueError("Historical tensor contains invalid values.")

# ------------------------------------------------
# 4. AUTOCORRELATION FUNCTION
# ------------------------------------------------

def calculate_autocorrelation(values, lag):

    values = np.asarray(
        values,
        dtype=float
    )

    if len(values) <= lag:
        return np.nan, np.nan

    x = values[:-lag]
    y = values[lag:]

    if np.std(x) == 0 or np.std(y) == 0:
        return np.nan, np.nan

    correlation, p_value = pearsonr(x, y)

    return float(correlation), float(p_value)


# ------------------------------------------------
# 5. CALCULATE NODE-WISE AUTOCORRELATION
# ------------------------------------------------

records = []

print("\nStarting autocorrelation analysis...")

for feature_index, feature_name in enumerate(FEATURE_NAMES):

    print(f"\nAnalyzing: {feature_name}")

    for node_index in range(len(spatial_nodes)):

        values = historical[
            :,
            node_index,
            feature_index
        ]

        lag1_corr, lag1_p = calculate_autocorrelation(
            values,
            lag=1
        )

        lag12_corr, lag12_p = calculate_autocorrelation(
            values,
            lag=12
        )

        records.append({

            "node_index": node_index,

            "node_id": spatial_nodes.iloc[
                node_index
            ]["node_id"],

            "latitude": spatial_nodes.iloc[
                node_index
            ]["grid_latitude"],

            "longitude": spatial_nodes.iloc[
                node_index
            ]["grid_longitude"],

            "feature": feature_name,

            "lag1_autocorrelation": lag1_corr,

            "lag1_p_value": lag1_p,

            "lag12_autocorrelation": lag12_corr,

            "lag12_p_value": lag12_p

        })

    print(f"Completed: {feature_name}")


autocorr_df = pd.DataFrame(records)

# ------------------------------------------------
# 6. CLASSIFY AUTOCORRELATION STRENGTH
# ------------------------------------------------

for lag in LAGS:

    column = f"lag{lag}_autocorrelation"

    classification_column = (
        f"lag{lag}_autocorrelation_class"
    )

    autocorr_df[classification_column] = np.select(

        [
            autocorr_df[column] >= CORRELATION_THRESHOLD,

            autocorr_df[column] <= -CORRELATION_THRESHOLD

        ],

        [
            "positive_autocorrelation",

            "negative_autocorrelation"

        ],

        default="weak_or_negligible"

    )

# ------------------------------------------------
# 7. SAVE NODE-WISE RESULTS
# ------------------------------------------------

node_output = (
    AUTOCORR_DIR / "node_wise_autocorrelation.csv"
)

autocorr_df.to_csv(
    node_output,
    index=False
)

# ------------------------------------------------
# 8. FEATURE-WISE SUMMARY
# ------------------------------------------------

summary_records = []

for feature_name in FEATURE_NAMES:

    subset = autocorr_df[
        autocorr_df["feature"] == feature_name
    ]

    record = {
        "feature": feature_name,
        "spatial_nodes": len(subset)
    }

    for lag in LAGS:

        column = f"lag{lag}_autocorrelation"

        values = subset[column].dropna()

        record[f"lag{lag}_mean"] = values.mean()

        record[f"lag{lag}_median"] = values.median()

        record[f"lag{lag}_positive_nodes"] = int(
            (values >= CORRELATION_THRESHOLD).sum()
        )

        record[f"lag{lag}_negative_nodes"] = int(
            (values <= -CORRELATION_THRESHOLD).sum()
        )

        record[f"lag{lag}_strong_nodes"] = int(
            (values.abs() >= CORRELATION_THRESHOLD).sum()
        )

        record[f"lag{lag}_valid_nodes"] = len(values)

    summary_records.append(record)


summary_df = pd.DataFrame(
    summary_records
)

summary_output = (
    AUTOCORR_DIR / "autocorrelation_summary.csv"
)

summary_df.to_csv(
    summary_output,
    index=False
)

# ------------------------------------------------
# 9. COMPARE AUTOCORRELATION WITH CELL 20 TRENDS
# ------------------------------------------------

trend_file = (
    TREND_DIR / "node_wise_seasonal_trends.csv"
)

if trend_file.exists():

    trend_df = pd.read_csv(trend_file)

    comparison_df = autocorr_df.merge(

        trend_df[
            [
                "node_index",
                "feature",
                "fdr_significant",
                "sen_slope_per_year"
            ]
        ],

        on=["node_index", "feature"],

        how="left"

    )

    comparison_output = (
        AUTOCORR_DIR /
        "autocorrelation_trend_comparison.csv"
    )

    comparison_df.to_csv(
        comparison_output,
        index=False
    )

    print("\nCell 20 trend comparison completed.")

else:

    comparison_df = None

    print(
        "\nCell 20 trend file not found. "
        "Trend comparison skipped."
    )

# ------------------------------------------------
# 10. SAVE METADATA
# ------------------------------------------------

metadata = {

    "project": "NASA Earth Systems Trend Detective",

    "analysis": "Temporal autocorrelation diagnostics",

    "historical_period": "2015-01 to 2024-12",

    "spatial_nodes": len(spatial_nodes),

    "monthly_observations": len(dates),

    "features": FEATURE_NAMES,

    "lags": {
        "1": "Consecutive monthly observations",
        "12": "Same calendar month across consecutive years"
    },

    "correlation_threshold": CORRELATION_THRESHOLD,

    "important_limitation": (
        "Pearson autocorrelation is a diagnostic. "
        "It does not itself correct Mann-Kendall significance. "
        "The p-values are unadjusted and should be interpreted "
        "descriptively."
    )

}

with open(
    AUTOCORR_DIR / "autocorrelation_metadata.json",
    "w"
) as file:

    json.dump(
        metadata,
        file,
        indent=4
    )

# ------------------------------------------------
# 11. FINAL REPORT
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 21 COMPLETED SUCCESSFULLY")
print("=" * 75)

print("\nFEATURE-WISE AUTOCORRELATION SUMMARY")

display(
    summary_df.round(4)
)

print("\nSaved files:")

print(node_output)

print(summary_output)

if comparison_df is not None:
    print(comparison_output)

print(AUTOCORR_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 26
# Execution count: 32
# ============================================================


# ================================================================
# CELL 22: SEASONAL TREND-FREE PRE-WHITENING SENSITIVITY ANALYSIS
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import numpy as np
import pandas as pd
import json

from pathlib import Path
from scipy.stats import norm

# ------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TREND_DIR = (
    PROJECT_ROOT / "outputs" / "historical_trend_analysis"
)

AUTOCORR_DIR = (
    PROJECT_ROOT / "outputs" / "autocorrelation_analysis"
)

TFPW_DIR = (
    PROJECT_ROOT / "outputs" / "tfpw_sensitivity_analysis"
)

TFPW_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ------------------------------------------------
# 2. CONFIGURATION
# ------------------------------------------------

FEATURE_NAMES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

ALPHA = 0.05

# ------------------------------------------------
# 3. LOAD DATA
# ------------------------------------------------

historical = np.load(
    PROCESSED_DIR / "nasa_power_tensor.npy"
)

spatial_nodes = pd.read_csv(
    PROCESSED_DIR / "spatial_nodes.csv"
)

time_index = np.load(
    PROCESSED_DIR / "tensor_time_index.npy",
    allow_pickle=True
)

dates = pd.DatetimeIndex(
    pd.to_datetime(time_index)
)

original_trends = pd.read_csv(
    TREND_DIR / "node_wise_seasonal_trends.csv"
)

print("Historical tensor:", historical.shape)
print("Spatial nodes:", len(spatial_nodes))
print("Time observations:", len(dates))
print("Original trend records:", len(original_trends))

if historical.shape != (120, 255, 4):
    raise ValueError("Unexpected historical tensor shape.")

if len(original_trends) != 1020:
    raise ValueError(
        "Expected 1,020 original node-feature trend records."
    )

if not np.isfinite(historical).all():
    raise ValueError("Invalid historical observations found.")

# ------------------------------------------------
# 4. SEASONAL MANN-KENDALL TEST
# ------------------------------------------------

def seasonal_mk_test(values, dates):

    values = np.asarray(
        values,
        dtype=float
    )

    date_series = pd.DatetimeIndex(dates)

    total_s = 0
    total_variance = 0

    for month in range(1, 13):

        mask = date_series.month == month

        month_values = values[mask]

        n = len(month_values)

        if n < 2:
            continue

        for i in range(n - 1):

            differences = (
                month_values[i + 1:] - month_values[i]
            )

            total_s += np.sum(
                np.sign(differences)
            )

        _, tie_counts = np.unique(
            month_values,
            return_counts=True
        )

        tie_term = np.sum(
            tie_counts
            * (tie_counts - 1)
            * (2 * tie_counts + 5)
        )

        total_variance += (
            n * (n - 1) * (2 * n + 5) - tie_term
        ) / 18.0

    if total_variance <= 0:

        return np.nan, np.nan, np.nan

    if total_s > 0:

        z_score = (
            total_s - 1
        ) / np.sqrt(total_variance)

    elif total_s < 0:

        z_score = (
            total_s + 1
        ) / np.sqrt(total_variance)

    else:

        z_score = 0.0

    p_value = 2 * norm.sf(
        abs(z_score)
    )

    return (
        float(total_s),
        float(z_score),
        float(p_value)
    )


# ------------------------------------------------
# 5. BENJAMINI-HOCHBERG FDR
# ------------------------------------------------

def benjamini_hochberg(p_values):

    p_values = np.asarray(
        p_values,
        dtype=float
    )

    adjusted = np.full(
        p_values.shape,
        np.nan
    )

    valid = np.isfinite(p_values)

    p = p_values[valid]

    if len(p) == 0:
        return adjusted

    n = len(p)

    order = np.argsort(p)

    sorted_p = p[order]

    ranks = np.arange(1, n + 1)

    sorted_adjusted = (
        sorted_p * n / ranks
    )

    sorted_adjusted = np.minimum.accumulate(
        sorted_adjusted[::-1]
    )[::-1]

    sorted_adjusted = np.clip(
        sorted_adjusted,
        0,
        1
    )

    restored = np.empty_like(
        sorted_adjusted
    )

    restored[order] = sorted_adjusted

    adjusted[valid] = restored

    return adjusted


# ------------------------------------------------
# 6. SEASONAL TFPW TRANSFORMATION
# ------------------------------------------------

def seasonal_tfpw(
    values,
    dates,
    original_slope
):

    values = np.asarray(
        values,
        dtype=float
    )

    date_series = pd.DatetimeIndex(dates)

    if len(values) != len(date_series):
        raise ValueError("Values and dates length mismatch.")

    if not np.isfinite(original_slope):
        return None, np.nan

    # Decimal-year coordinate
    time_years = (
        date_series.year.to_numpy()
        + (date_series.month.to_numpy() - 1) / 12.0
    )

    centered_time = (
        time_years - np.mean(time_years)
    )

    # Remove the estimated long-term trend
    detrended = (
        values - original_slope * centered_time
    )

    # Estimate month-specific climatology
    month_climatology = {}

    for month in range(1, 13):

        mask = (
            date_series.month == month
        )

        month_climatology[month] = np.median(
            detrended[mask]
        )

    seasonal_component = np.array([
        month_climatology[month]
        for month in date_series.month
    ])

    # Residual after removing trend and seasonality
    residual = (
        detrended - seasonal_component
    )

    # Estimate residual lag-1 autocorrelation
    previous = residual[:-1]

    current = residual[1:]

    denominator = np.dot(
        previous,
        previous
    )

    if denominator <= 1e-12:

        rho = 0.0

    else:

        rho = (
            np.dot(previous, current)
            / denominator
        )

    # Bound coefficient for numerical stability
    rho = float(
        np.clip(rho, -0.99, 0.99)
    )

    # Pre-whiten residuals
    whitened_residual = np.zeros_like(
        residual
    )

    whitened_residual[0] = residual[0]

    whitened_residual[1:] = (
        residual[1:]
        - rho * residual[:-1]
    )

    # Restore seasonal component and original trend
    transformed = (
        seasonal_component
        + original_slope * centered_time
        + whitened_residual
    )

    return transformed, rho


# ------------------------------------------------
# 7. NODE-WISE TFPW ANALYSIS
# ------------------------------------------------

records = []

print("\nStarting seasonal TFPW sensitivity analysis...")

for feature_index, feature_name in enumerate(FEATURE_NAMES):

    print(f"\nProcessing feature: {feature_name}")

    feature_trends = original_trends[
        original_trends["feature"] == feature_name
    ].set_index("node_index")

    for node_index in range(len(spatial_nodes)):

        values = historical[
            :,
            node_index,
            feature_index
        ]

        original_row = feature_trends.loc[
            node_index
        ]

        original_slope = float(
            original_row["sen_slope_per_year"]
        )

        original_p = float(
            original_row["p_value"]
        )

        original_fdr = bool(
            original_row["fdr_significant"]
        )

        transformed, rho = seasonal_tfpw(
            values,
            dates,
            original_slope
        )

        if transformed is None:

            adjusted_s = np.nan
            adjusted_z = np.nan
            adjusted_p = np.nan

        else:

            (
                adjusted_s,
                adjusted_z,
                adjusted_p
            ) = seasonal_mk_test(
                transformed,
                dates
            )

        records.append({

            "node_index": node_index,

            "node_id": spatial_nodes.iloc[
                node_index
            ]["node_id"],

            "latitude": spatial_nodes.iloc[
                node_index
            ]["grid_latitude"],

            "longitude": spatial_nodes.iloc[
                node_index
            ]["grid_longitude"],

            "feature": feature_name,

            "original_sen_slope_per_year": original_slope,

            "original_p_value": original_p,

            "original_fdr_significant": original_fdr,

            "residual_lag1_rho": rho,

            "tfpw_mann_kendall_S": adjusted_s,

            "tfpw_z_score": adjusted_z,

            "tfpw_p_value": adjusted_p

        })

    print(f"Completed: {feature_name}")


tfpw_df = pd.DataFrame(records)

# ------------------------------------------------
# 8. APPLY FDR TO ADJUSTED P-VALUES
# ------------------------------------------------

tfpw_df["tfpw_fdr_adjusted_p"] = (
    benjamini_hochberg(
        tfpw_df["tfpw_p_value"].to_numpy()
    )
)

tfpw_df["tfpw_fdr_significant"] = (
    tfpw_df["tfpw_fdr_adjusted_p"] < ALPHA
)

# ------------------------------------------------
# 9. COMPARE ORIGINAL AND ADJUSTED SIGNIFICANCE
# ------------------------------------------------

tfpw_df["significance_changed"] = (
    tfpw_df["original_fdr_significant"]
    != tfpw_df["tfpw_fdr_significant"]
)

tfpw_df["comparison_class"] = np.select(

    [
        (
            tfpw_df["original_fdr_significant"]
            & tfpw_df["tfpw_fdr_significant"]
        ),

        (
            tfpw_df["original_fdr_significant"]
            & ~tfpw_df["tfpw_fdr_significant"]
        ),

        (
            ~tfpw_df["original_fdr_significant"]
            & tfpw_df["tfpw_fdr_significant"]
        )

    ],

    [
        "significant_in_both",
        "lost_significance_after_tfpw",
        "significant_only_after_tfpw"
    ],

    default="not_significant_in_either"

)

# ------------------------------------------------
# 10. SAVE NODE-WISE RESULTS
# ------------------------------------------------

node_output = (
    TFPW_DIR / "node_wise_tfpw_comparison.csv"
)

tfpw_df.to_csv(
    node_output,
    index=False
)

# ------------------------------------------------
# 11. FEATURE-WISE COMPARISON SUMMARY
# ------------------------------------------------

summary_records = []

for feature_name in FEATURE_NAMES:

    subset = tfpw_df[
        tfpw_df["feature"] == feature_name
    ]

    summary_records.append({

        "feature": feature_name,

        "spatial_nodes": len(subset),

        "mean_residual_lag1_rho": (
            subset["residual_lag1_rho"].mean()
        ),

        "original_significant_nodes": int(
            subset["original_fdr_significant"].sum()
        ),

        "tfpw_significant_nodes": int(
            subset["tfpw_fdr_significant"].sum()
        ),

        "significant_in_both": int(
            (
                subset["comparison_class"]
                == "significant_in_both"
            ).sum()
        ),

        "lost_significance_after_tfpw": int(
            (
                subset["comparison_class"]
                == "lost_significance_after_tfpw"
            ).sum()
        ),

        "significant_only_after_tfpw": int(
            (
                subset["comparison_class"]
                == "significant_only_after_tfpw"
            ).sum()
        ),

        "not_significant_in_either": int(
            (
                subset["comparison_class"]
                == "not_significant_in_either"
            ).sum()
        )

    })


summary_df = pd.DataFrame(
    summary_records
)

summary_output = (
    TFPW_DIR / "tfpw_feature_comparison_summary.csv"
)

summary_df.to_csv(
    summary_output,
    index=False
)

# ------------------------------------------------
# 12. TREND DIRECTION COMPARISON
# ------------------------------------------------

direction_records = []

for feature_name in FEATURE_NAMES:

    subset = tfpw_df[
        (tfpw_df["feature"] == feature_name)
        & tfpw_df["tfpw_fdr_significant"]
    ]

    direction_records.append({

        "feature": feature_name,

        "tfpw_significant_increasing": int(
            (
                subset["original_sen_slope_per_year"] > 0
            ).sum()
        ),

        "tfpw_significant_decreasing": int(
            (
                subset["original_sen_slope_per_year"] < 0
            ).sum()
        )

    })


direction_df = pd.DataFrame(
    direction_records
)

direction_output = (
    TFPW_DIR / "tfpw_trend_direction_summary.csv"
)

direction_df.to_csv(
    direction_output,
    index=False
)

# ------------------------------------------------
# 13. SAVE METADATA
# ------------------------------------------------

metadata = {

    "project": "NASA Earth Systems Trend Detective",

    "analysis": (
        "Seasonal trend-free pre-whitening sensitivity analysis"
    ),

    "historical_period": "2015-01 to 2024-12",

    "spatial_nodes": len(spatial_nodes),

    "features": FEATURE_NAMES,

    "method": (
        "Remove original seasonal Sen trend, estimate "
        "month-specific climatology, pre-whiten residuals "
        "using estimated lag-1 coefficient, restore trend "
        "and seasonal component, then apply Seasonal "
        "Mann-Kendall test."
    ),

    "fdr_method": "Benjamini-Hochberg",

    "alpha": ALPHA,

    "important_limitation": (
        "This is an approximate sensitivity implementation. "
        "It is not a validated replacement for a formally "
        "tested TFPW implementation. Residual dependence, "
        "short record length, and spatial dependence may "
        "still affect inference."
    )

}

with open(
    TFPW_DIR / "tfpw_metadata.json",
    "w"
) as file:

    json.dump(
        metadata,
        file,
        indent=4
    )

# ------------------------------------------------
# 14. FINAL REPORT
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 22 COMPLETED SUCCESSFULLY")
print("=" * 75)

print("\nORIGINAL VS TFPW SIGNIFICANCE SUMMARY")

display(
    summary_df.round(4)
)

print("\nTFPW TREND DIRECTION SUMMARY")

display(
    direction_df
)

print("\nSaved files:")

print(node_output)

print(summary_output)

print(direction_output)

print(TFPW_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 27
# Execution count: 33
# ============================================================


# ================================================================
# CELL 23: SEASONALLY ALIGNED TREND-FREE PRE-WHITENING
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import numpy as np
import pandas as pd
import json

from pathlib import Path
from scipy.stats import norm

# ------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TREND_DIR = (
    PROJECT_ROOT / "outputs" / "historical_trend_analysis"
)

TFPW_DIR = (
    PROJECT_ROOT / "outputs" / "seasonal_tfpw_analysis"
)

TFPW_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ------------------------------------------------
# 2. CONFIGURATION
# ------------------------------------------------

FEATURE_NAMES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

ALPHA = 0.05

# ------------------------------------------------
# 3. LOAD DATA
# ------------------------------------------------

historical = np.load(
    PROCESSED_DIR / "nasa_power_tensor.npy"
)

spatial_nodes = pd.read_csv(
    PROCESSED_DIR / "spatial_nodes.csv"
)

time_index = np.load(
    PROCESSED_DIR / "tensor_time_index.npy",
    allow_pickle=True
)

dates = pd.DatetimeIndex(
    pd.to_datetime(time_index)
)

original_trends = pd.read_csv(
    TREND_DIR / "node_wise_seasonal_trends.csv"
)

print("Historical tensor:", historical.shape)
print("Spatial nodes:", len(spatial_nodes))
print("Time observations:", len(dates))
print("Original trend records:", len(original_trends))

if historical.shape != (120, 255, 4):
    raise ValueError("Unexpected tensor shape.")

if len(original_trends) != 1020:
    raise ValueError("Expected 1,020 original trend records.")

if not np.isfinite(historical).all():
    raise ValueError("Historical data contains invalid values.")

if not dates.is_monotonic_increasing:
    raise ValueError("Dates are not chronologically sorted.")

# ------------------------------------------------
# 4. SEASONAL MANN-KENDALL TEST
# ------------------------------------------------

def seasonal_mk_test(values, dates):

    values = np.asarray(values, dtype=float)

    date_series = pd.DatetimeIndex(dates)

    total_s = 0
    total_variance = 0

    for month in range(1, 13):

        mask = date_series.month == month

        month_values = values[mask]

        n = len(month_values)

        if n < 2:
            continue

        for i in range(n - 1):

            differences = (
                month_values[i + 1:] - month_values[i]
            )

            total_s += np.sum(
                np.sign(differences)
            )

        _, tie_counts = np.unique(
            month_values,
            return_counts=True
        )

        tie_term = np.sum(
            tie_counts
            * (tie_counts - 1)
            * (2 * tie_counts + 5)
        )

        total_variance += (
            n * (n - 1) * (2 * n + 5) - tie_term
        ) / 18.0

    if total_variance <= 0:

        return np.nan, np.nan, np.nan

    if total_s > 0:

        z_score = (
            total_s - 1
        ) / np.sqrt(total_variance)

    elif total_s < 0:

        z_score = (
            total_s + 1
        ) / np.sqrt(total_variance)

    else:

        z_score = 0.0

    p_value = 2 * norm.sf(
        abs(z_score)
    )

    return (
        float(total_s),
        float(z_score),
        float(p_value)
    )


# ------------------------------------------------
# 5. BENJAMINI-HOCHBERG FDR
# ------------------------------------------------

def benjamini_hochberg(p_values):

    p_values = np.asarray(
        p_values,
        dtype=float
    )

    adjusted = np.full(
        p_values.shape,
        np.nan
    )

    valid = np.isfinite(p_values)

    p = p_values[valid]

    if len(p) == 0:
        return adjusted

    n = len(p)

    order = np.argsort(p)

    sorted_p = p[order]

    ranks = np.arange(1, n + 1)

    sorted_adjusted = (
        sorted_p * n / ranks
    )

    sorted_adjusted = np.minimum.accumulate(
        sorted_adjusted[::-1]
    )[::-1]

    sorted_adjusted = np.clip(
        sorted_adjusted,
        0,
        1
    )

    restored = np.empty_like(
        sorted_adjusted
    )

    restored[order] = sorted_adjusted

    adjusted[valid] = restored

    return adjusted


# ------------------------------------------------
# 6. SEASONALLY ALIGNED TFPW
# ------------------------------------------------

def seasonal_aligned_tfpw(
    values,
    dates,
    original_slope
):

    values = np.asarray(
        values,
        dtype=float
    )

    date_series = pd.DatetimeIndex(dates)

    if not np.isfinite(original_slope):
        return None, np.nan

    years = date_series.year.to_numpy()

    centered_years = (
        years - np.mean(years)
    )

    transformed = np.full_like(
        values,
        np.nan
    )

    monthly_rhos = []

    for month in range(1, 13):

        indices = np.where(
            date_series.month == month
        )[0]

        month_values = values[indices]

        month_times = centered_years[indices]

        if len(month_values) < 3:
            continue

        # Remove the estimated long-term trend
        detrended = (
            month_values
            - original_slope * month_times
        )

        # Remove the monthly climatological level
        seasonal_level = np.median(detrended)

        residual = (
            detrended - seasonal_level
        )

        # Estimate autocorrelation across successive
        # observations of this same calendar month
        previous = residual[:-1]

        current = residual[1:]

        denominator = np.dot(
            previous,
            previous
        )

        if denominator <= 1e-12:

            rho = 0.0

        else:

            rho = (
                np.dot(previous, current)
                / denominator
            )

        rho = float(
            np.clip(rho, -0.99, 0.99)
        )

        monthly_rhos.append(rho)

        # Pre-whiten the monthly residual series
        whitened = np.zeros_like(
            residual
        )

        whitened[0] = residual[0]

        whitened[1:] = (
            residual[1:]
            - rho * residual[:-1]
        )

        # Restore original trend and seasonal level
        transformed[indices] = (
            seasonal_level
            + original_slope * month_times
            + whitened
        )

    if not np.isfinite(transformed).all():
        return None, np.nan

    mean_rho = (
        float(np.mean(monthly_rhos))
        if monthly_rhos
        else np.nan
    )

    return transformed, mean_rho


# ------------------------------------------------
# 7. NODE-WISE ANALYSIS
# ------------------------------------------------

records = []

print("\nStarting seasonally aligned TFPW analysis...")

for feature_index, feature_name in enumerate(FEATURE_NAMES):

    print(f"\nProcessing: {feature_name}")

    feature_trends = original_trends[
        original_trends["feature"] == feature_name
    ].set_index("node_index")

    for node_index in range(len(spatial_nodes)):

        values = historical[
            :,
            node_index,
            feature_index
        ]

        original_row = feature_trends.loc[
            node_index
        ]

        original_slope = float(
            original_row["sen_slope_per_year"]
        )

        original_fdr = bool(
            original_row["fdr_significant"]
        )

        transformed, mean_rho = seasonal_aligned_tfpw(
            values,
            dates,
            original_slope
        )

        if transformed is None:

            s_value = np.nan
            z_score = np.nan
            p_value = np.nan

        else:

            s_value, z_score, p_value = seasonal_mk_test(
                transformed,
                dates
            )

        records.append({

            "node_index": node_index,

            "node_id": spatial_nodes.iloc[
                node_index
            ]["node_id"],

            "latitude": spatial_nodes.iloc[
                node_index
            ]["grid_latitude"],

            "longitude": spatial_nodes.iloc[
                node_index
            ]["grid_longitude"],

            "feature": feature_name,

            "original_sen_slope_per_year": original_slope,

            "original_fdr_significant": original_fdr,

            "mean_seasonal_residual_rho": mean_rho,

            "tfpw_mann_kendall_S": s_value,

            "tfpw_z_score": z_score,

            "tfpw_p_value": p_value

        })

    print(f"Completed: {feature_name}")


tfpw_df = pd.DataFrame(records)

# ------------------------------------------------
# 8. FDR CORRECTION
# ------------------------------------------------

tfpw_df["tfpw_fdr_adjusted_p"] = (
    benjamini_hochberg(
        tfpw_df["tfpw_p_value"].to_numpy()
    )
)

tfpw_df["tfpw_fdr_significant"] = (
    tfpw_df["tfpw_fdr_adjusted_p"] < ALPHA
)

# ------------------------------------------------
# 9. COMPARE SIGNIFICANCE
# ------------------------------------------------

tfpw_df["significance_changed"] = (
    tfpw_df["original_fdr_significant"]
    != tfpw_df["tfpw_fdr_significant"]
)

tfpw_df["comparison_class"] = np.select(

    [

        (
            tfpw_df["original_fdr_significant"]
            & tfpw_df["tfpw_fdr_significant"]
        ),

        (
            tfpw_df["original_fdr_significant"]
            & ~tfpw_df["tfpw_fdr_significant"]
        ),

        (
            ~tfpw_df["original_fdr_significant"]
            & tfpw_df["tfpw_fdr_significant"]
        )

    ],

    [

        "significant_in_both",

        "lost_significance_after_tfpw",

        "significant_only_after_tfpw"

    ],

    default="not_significant_in_either"

)

# ------------------------------------------------
# 10. SAVE NODE-WISE RESULTS
# ------------------------------------------------

node_output = (
    TFPW_DIR / "seasonally_aligned_tfpw_nodes.csv"
)

tfpw_df.to_csv(
    node_output,
    index=False
)

# ------------------------------------------------
# 11. FEATURE-WISE SUMMARY
# ------------------------------------------------

summary_records = []

for feature_name in FEATURE_NAMES:

    subset = tfpw_df[
        tfpw_df["feature"] == feature_name
    ]

    summary_records.append({

        "feature": feature_name,

        "spatial_nodes": len(subset),

        "mean_seasonal_residual_rho": (
            subset["mean_seasonal_residual_rho"].mean()
        ),

        "original_significant_nodes": int(
            subset["original_fdr_significant"].sum()
        ),

        "seasonal_tfpw_significant_nodes": int(
            subset["tfpw_fdr_significant"].sum()
        ),

        "significant_in_both": int(
            (
                subset["comparison_class"]
                == "significant_in_both"
            ).sum()
        ),

        "lost_significance_after_tfpw": int(
            (
                subset["comparison_class"]
                == "lost_significance_after_tfpw"
            ).sum()
        ),

        "significant_only_after_tfpw": int(
            (
                subset["comparison_class"]
                == "significant_only_after_tfpw"
            ).sum()
        ),

        "not_significant_in_either": int(
            (
                subset["comparison_class"]
                == "not_significant_in_either"
            ).sum()
        )

    })


summary_df = pd.DataFrame(
    summary_records
)

summary_output = (
    TFPW_DIR / "seasonally_aligned_tfpw_summary.csv"
)

summary_df.to_csv(
    summary_output,
    index=False
)

# ------------------------------------------------
# 12. TREND DIRECTION SUMMARY
# ------------------------------------------------

direction_records = []

for feature_name in FEATURE_NAMES:

    subset = tfpw_df[
        (tfpw_df["feature"] == feature_name)
        & tfpw_df["tfpw_fdr_significant"]
    ]

    direction_records.append({

        "feature": feature_name,

        "significant_increasing": int(
            (
                subset["original_sen_slope_per_year"] > 0
            ).sum()
        ),

        "significant_decreasing": int(
            (
                subset["original_sen_slope_per_year"] < 0
            ).sum()
        )

    })


direction_df = pd.DataFrame(
    direction_records
)

direction_output = (
    TFPW_DIR / "seasonally_aligned_tfpw_directions.csv"
)

direction_df.to_csv(
    direction_output,
    index=False
)

# ------------------------------------------------
# 13. SAVE METADATA
# ------------------------------------------------

metadata = {

    "project": "NASA Earth Systems Trend Detective",

    "analysis": (
        "Seasonally aligned trend-free pre-whitening sensitivity"
    ),

    "period": "2015-01 to 2024-12",

    "spatial_nodes": len(spatial_nodes),

    "features": FEATURE_NAMES,

    "method": (
        "For each calendar month, remove the original Sen trend, "
        "estimate lag-1 autocorrelation across successive years, "
        "pre-whiten that month's residual series, and restore "
        "the estimated trend and monthly climatological level."
    ),

    "multiple_testing": "Benjamini-Hochberg FDR",

    "alpha": ALPHA,

    "limitations": (
        "Only ten annual observations are available per calendar "
        "month. Autocorrelation estimates are therefore uncertain. "
        "This is a sensitivity analysis, not definitive corrected "
        "inference. Residual cross-month and spatial dependence "
        "may remain."
    )

}

with open(
    TFPW_DIR / "seasonally_aligned_tfpw_metadata.json",
    "w"
) as file:

    json.dump(
        metadata,
        file,
        indent=4
    )

# ------------------------------------------------
# 14. FINAL REPORT
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 23 COMPLETED SUCCESSFULLY")
print("=" * 75)

print("\nSEASONALLY ALIGNED TFPW SUMMARY")

display(
    summary_df.round(4)
)

print("\nTREND DIRECTION SUMMARY")

display(
    direction_df
)

print("\nSaved files:")

print(node_output)

print(summary_output)

print(direction_output)

print(TFPW_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 28
# Execution count: 34
# ============================================================


# ================================================================
# CELL 24: RESIDUAL AUTOCORRELATION DIAGNOSTICS
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import numpy as np
import pandas as pd
import json

from pathlib import Path

# ------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TREND_DIR = (
    PROJECT_ROOT / "outputs" / "historical_trend_analysis"
)

TFPW_DIR = (
    PROJECT_ROOT / "outputs" / "seasonal_tfpw_analysis"
)

DIAGNOSTIC_DIR = (
    PROJECT_ROOT / "outputs" / "tfpw_diagnostics"
)

DIAGNOSTIC_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ------------------------------------------------
# 2. CONFIGURATION
# ------------------------------------------------

FEATURE_NAMES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

# ------------------------------------------------
# 3. LOAD DATA
# ------------------------------------------------

historical = np.load(
    PROCESSED_DIR / "nasa_power_tensor.npy"
)

spatial_nodes = pd.read_csv(
    PROCESSED_DIR / "spatial_nodes.csv"
)

time_index = np.load(
    PROCESSED_DIR / "tensor_time_index.npy",
    allow_pickle=True
)

dates = pd.DatetimeIndex(
    pd.to_datetime(time_index)
)

original_trends = pd.read_csv(
    TREND_DIR / "node_wise_seasonal_trends.csv"
)

cell23_results = pd.read_csv(
    TFPW_DIR / "seasonally_aligned_tfpw_nodes.csv"
)

print("=" * 75)
print("CELL 24: RESIDUAL AUTOCORRELATION DIAGNOSTICS")
print("=" * 75)

print("Historical tensor:", historical.shape)
print("Spatial nodes:", len(spatial_nodes))
print("Cell 20 records:", len(original_trends))
print("Cell 23 records:", len(cell23_results))

if historical.shape != (120, 255, 4):
    raise ValueError("Unexpected historical tensor shape.")

if len(dates) != 120:
    raise ValueError("Expected 120 monthly observations.")

if len(original_trends) != 1020:
    raise ValueError("Unexpected Cell 20 trend record count.")

if len(cell23_results) != 1020:
    raise ValueError("Unexpected Cell 23 result count.")

# ------------------------------------------------
# 4. AUTOCORRELATION ESTIMATORS
# ------------------------------------------------

def estimate_rho_uncentered(residual):

    residual = np.asarray(
        residual,
        dtype=float
    )

    previous = residual[:-1]
    current = residual[1:]

    denominator = np.dot(
        previous,
        previous
    )

    if denominator <= 1e-12:
        return np.nan

    return float(
        np.dot(previous, current) / denominator
    )


def estimate_rho_centered(residual):

    residual = np.asarray(
        residual,
        dtype=float
    )

    centered = (
        residual - np.mean(residual)
    )

    previous = centered[:-1]
    current = centered[1:]

    denominator = np.dot(
        previous,
        previous
    )

    if denominator <= 1e-12:
        return np.nan

    return float(
        np.dot(previous, current) / denominator
    )


# ------------------------------------------------
# 5. SEASONAL RESIDUAL ANALYSIS
# ------------------------------------------------

diagnostic_records = []

monthly_rho_records = []

print("\nStarting node-wise residual diagnostics...")

for feature_index, feature_name in enumerate(FEATURE_NAMES):

    print("Processing:", feature_name)

    feature_trends = (
        original_trends[
            original_trends["feature"] == feature_name
        ]
        .set_index("node_index")
    )

    feature_cell23 = (
        cell23_results[
            cell23_results["feature"] == feature_name
        ]
        .set_index("node_index")
    )

    for node_index in range(len(spatial_nodes)):

        values = historical[
            :,
            node_index,
            feature_index
        ].astype(float)

        trend_row = feature_trends.loc[
            node_index
        ]

        cell23_row = feature_cell23.loc[
            node_index
        ]

        original_slope = float(
            trend_row["sen_slope_per_year"]
        )

        years = dates.year.to_numpy()

        centered_years = (
            years - np.mean(years)
        )

        monthly_rhos_uncentered = []
        monthly_rhos_centered = []

        for month in range(1, 13):

            indices = np.where(
                dates.month == month
            )[0]

            month_values = values[indices]

            month_years = centered_years[
                indices
            ]

            if len(month_values) < 3:
                continue

            # Remove original Sen trend
            detrended = (
                month_values
                - original_slope * month_years
            )

            # Remove monthly median
            residual = (
                detrended
                - np.median(detrended)
            )

            rho_uncentered = (
                estimate_rho_uncentered(
                    residual
                )
            )

            rho_centered = (
                estimate_rho_centered(
                    residual
                )
            )

            monthly_rhos_uncentered.append(
                rho_uncentered
            )

            monthly_rhos_centered.append(
                rho_centered
            )

            monthly_rho_records.append({

                "node_index": node_index,

                "node_id": spatial_nodes.iloc[
                    node_index
                ]["node_id"],

                "feature": feature_name,

                "calendar_month": month,

                "annual_observations": len(
                    month_values
                ),

                "rho_uncentered": rho_uncentered,

                "rho_centered": rho_centered,

                "residual_mean": float(
                    np.mean(residual)
                ),

                "residual_std": float(
                    np.std(residual)
                )

            })

        diagnostic_records.append({

            "node_index": node_index,

            "node_id": spatial_nodes.iloc[
                node_index
            ]["node_id"],

            "feature": feature_name,

            "original_sen_slope_per_year": (
                original_slope
            ),

            "cell23_mean_rho": float(
                cell23_row[
                    "mean_seasonal_residual_rho"
                ]
            ),

            "mean_uncentered_rho": float(
                np.nanmean(
                    monthly_rhos_uncentered
                )
            ),

            "mean_centered_rho": float(
                np.nanmean(
                    monthly_rhos_centered
                )
            ),

            "centered_minus_uncentered_rho": (
                float(
                    np.nanmean(
                        monthly_rhos_centered
                    )
                    -
                    np.nanmean(
                        monthly_rhos_uncentered
                    )
                )
            ),

            "original_fdr_significant": bool(
                trend_row["fdr_significant"]
            ),

            "cell23_fdr_significant": bool(
                cell23_row["tfpw_fdr_significant"]
            ),

            "cell23_adjusted_p": float(
                cell23_row["tfpw_fdr_adjusted_p"]
            )

        })

    print("Completed:", feature_name)


diagnostic_df = pd.DataFrame(
    diagnostic_records
)

monthly_rho_df = pd.DataFrame(
    monthly_rho_records
)

# ------------------------------------------------
# 6. FEATURE-WISE AUTOCORRELATION SUMMARY
# ------------------------------------------------

summary_records = []

for feature_name in FEATURE_NAMES:

    subset = diagnostic_df[
        diagnostic_df["feature"] == feature_name
    ]

    summary_records.append({

        "feature": feature_name,

        "nodes": len(subset),

        "mean_uncentered_rho": (
            subset["mean_uncentered_rho"].mean()
        ),

        "median_uncentered_rho": (
            subset["mean_uncentered_rho"].median()
        ),

        "mean_centered_rho": (
            subset["mean_centered_rho"].mean()
        ),

        "median_centered_rho": (
            subset["mean_centered_rho"].median()
        ),

        "mean_rho_difference": (
            subset[
                "centered_minus_uncentered_rho"
            ].mean()
        ),

        "positive_centered_rho_nodes": int(
            (
                subset["mean_centered_rho"] > 0
            ).sum()
        ),

        "negative_centered_rho_nodes": int(
            (
                subset["mean_centered_rho"] < 0
            ).sum()
        ),

        "original_significant_nodes": int(
            subset["original_fdr_significant"].sum()
        ),

        "cell23_significant_nodes": int(
            subset["cell23_fdr_significant"].sum()
        )

    })


summary_df = pd.DataFrame(
    summary_records
)

# ------------------------------------------------
# 7. PRECIPITATION SIGNIFICANCE INVESTIGATION
# ------------------------------------------------

precipitation_df = diagnostic_df[
    diagnostic_df["feature"] == "PRECTOTCORR"
].copy()

precipitation_df["significance_category"] = np.select(

    [

        (
            precipitation_df["original_fdr_significant"]
            &
            precipitation_df["cell23_fdr_significant"]
        ),

        (
            precipitation_df["original_fdr_significant"]
            &
            ~precipitation_df["cell23_fdr_significant"]
        ),

        (
            ~precipitation_df["original_fdr_significant"]
            &
            precipitation_df["cell23_fdr_significant"]
        )

    ],

    [

        "significant_in_both",

        "lost_significance",

        "newly_significant"

    ],

    default="not_significant_in_either"

)

precipitation_investigation = (
    precipitation_df.sort_values(
        by=[
            "significance_category",
            "cell23_adjusted_p"
        ],
        ascending=[True, True]
    )
)

# ------------------------------------------------
# 8. MONTHLY AUTOCORRELATION SUMMARY
# ------------------------------------------------

monthly_summary = (
    monthly_rho_df.groupby(
        ["feature", "calendar_month"]
    )
    .agg(

        mean_uncentered_rho=(
            "rho_uncentered",
            "mean"
        ),

        mean_centered_rho=(
            "rho_centered",
            "mean"
        ),

        median_centered_rho=(
            "rho_centered",
            "median"
        ),

        node_count=(
            "node_index",
            "count"
        )

    )
    .reset_index()
)

# ------------------------------------------------
# 9. SAVE RESULTS
# ------------------------------------------------

diagnostic_df.to_csv(
    DIAGNOSTIC_DIR / "node_residual_autocorrelation.csv",
    index=False
)

monthly_rho_df.to_csv(
    DIAGNOSTIC_DIR / "monthly_residual_autocorrelation.csv",
    index=False
)

summary_df.to_csv(
    DIAGNOSTIC_DIR / "feature_autocorrelation_comparison.csv",
    index=False
)

precipitation_investigation.to_csv(
    DIAGNOSTIC_DIR / "precipitation_significance_investigation.csv",
    index=False
)

monthly_summary.to_csv(
    DIAGNOSTIC_DIR / "monthly_autocorrelation_summary.csv",
    index=False
)

# ------------------------------------------------
# 10. METADATA
# ------------------------------------------------

metadata = {

    "project": "NASA Earth Systems Trend Detective",

    "analysis": (
        "Seasonal residual autocorrelation estimator comparison"
    ),

    "period": "2015-01 to 2024-12",

    "historical_shape": list(
        historical.shape
    ),

    "spatial_nodes": len(spatial_nodes),

    "features": FEATURE_NAMES,

    "annual_observations_per_calendar_month": 10,

    "estimators": {

        "uncentered": (
            "Sum(previous * current) / "
            "Sum(previous squared)"
        ),

        "centered": (
            "Apply the same estimator after subtracting "
            "the residual-series mean"
        )

    },

    "limitations": (
        "Autocorrelation estimates use only ten annual "
        "observations per calendar month. They are noisy "
        "diagnostics and do not establish valid corrected "
        "Mann-Kendall inference."
    )

}

with open(
    DIAGNOSTIC_DIR / "tfpw_diagnostic_metadata.json",
    "w"
) as file:

    json.dump(
        metadata,
        file,
        indent=4
    )

# ------------------------------------------------
# 11. FINAL REPORT
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 24 COMPLETED SUCCESSFULLY")
print("=" * 75)

print("\nFEATURE-WISE AUTOCORRELATION COMPARISON")

display(
    summary_df.round(4)
)

print("\nMONTHLY AUTOCORRELATION SUMMARY")

display(
    monthly_summary.round(4)
)

print("\nPRECIPITATION SIGNIFICANCE CATEGORIES")

display(
    precipitation_investigation[
        "significance_category"
    ].value_counts().rename_axis(
        "category"
    ).reset_index(
        name="nodes"
    )
)

print("\nSaved diagnostic files:")

for file in DIAGNOSTIC_DIR.iterdir():

    print(file)


# ============================================================
# ORIGINAL NOTEBOOK CELL 29
# Execution count: 36
# ============================================================


# ================================================================
# CELL 25: FINAL TREND ROBUSTNESS REPORT
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import json
import numpy as np
import pandas as pd

from pathlib import Path
from datetime import datetime

# ------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "final_trend_robustness"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ORIGINAL_FILE = (
    PROJECT_ROOT / "outputs" / "historical_trend_analysis"
    / "node_wise_seasonal_trends.csv"
)

INITIAL_TFPW_FILE = (
    PROJECT_ROOT / "outputs" / "tfpw_sensitivity_analysis"
    / "node_wise_tfpw_comparison.csv"
)

SEASONAL_TFPW_FILE = (
    PROJECT_ROOT / "outputs" / "seasonal_tfpw_analysis"
    / "seasonally_aligned_tfpw_nodes.csv"
)

DIAGNOSTIC_FILE = (
    PROJECT_ROOT / "outputs" / "tfpw_diagnostics"
    / "feature_autocorrelation_comparison.csv"
)

print("=" * 75)
print("CELL 25: FINAL TREND ROBUSTNESS REPORT")
print("=" * 75)


# ------------------------------------------------
# 2. LOAD FILES
# ------------------------------------------------

def load_csv(path, label, required=True):

    if not path.exists():

        if required:
            raise FileNotFoundError(
                f"{label} not found:\n{path}"
            )

        print(f"Optional file not found: {path}")
        return None

    df = pd.read_csv(path)

    print(f"\n{label}: {df.shape}")

    return df


original = load_csv(
    ORIGINAL_FILE,
    "CELL 20 ORIGINAL SEASONAL MK"
)

initial_tfpw = load_csv(
    INITIAL_TFPW_FILE,
    "CELL 22 INITIAL TFPW",
    required=False
)

seasonal_tfpw = load_csv(
    SEASONAL_TFPW_FILE,
    "CELL 23 SEASONALLY ALIGNED TFPW"
)

diagnostics = load_csv(
    DIAGNOSTIC_FILE,
    "CELL 24 AUTOCORRELATION DIAGNOSTICS",
    required=False
)


# ------------------------------------------------
# 3. COLUMN DETECTION
# ------------------------------------------------

def find_column(df, candidates, required=True):

    lookup = {
        str(c).strip().lower(): c
        for c in df.columns
    }

    for candidate in candidates:

        if candidate.lower() in lookup:
            return lookup[candidate.lower()]

    if required:

        raise KeyError(
            f"Could not find columns {candidates}\n"
            f"Available: {df.columns.tolist()}"
        )

    return None


def detect_feature_column(df):

    return find_column(
        df,
        ["feature", "variable", "parameter", "feature_name"]
    )


def detect_node_column(df):

    return find_column(
        df,
        ["node_id", "node", "node_index", "spatial_node", "grid_id"]
    )


def detect_significance_column(df):

    return find_column(
        df,
        [
            "significant_fdr",
            "tfpw_fdr_significant",
            "original_fdr_significant",
            "significant",
            "is_significant",
            "fdr_significant",
            "significant_bh"
        ],
        required=False
    )


def detect_q_column(df):

    return find_column(
        df,
        [
            "q_value",
            "qvalue",
            "tfpw_fdr_adjusted_p",
            "adjusted_p_value",
            "fdr_p_value",
            "p_adjusted",
            "p_adj"
        ],
        required=False
    )


def detect_direction_column(df):

    return find_column(
        df,
        [
            "trend_direction",
            "direction",
            "trend",
            "sen_direction"
        ],
        required=False
    )


def detect_slope_column(df):

    return find_column(
        df,
        [
            "sen_slope",
            "sen_slope_per_year",
            "original_sen_slope_per_year",
            "slope",
            "sen_slope_year"
        ],
        required=False
    )


# ------------------------------------------------
# 4. SAFE BOOLEAN CONVERSION
# ------------------------------------------------

def to_boolean(series):

    if pd.api.types.is_bool_dtype(series):

        return series.fillna(False)

    if pd.api.types.is_numeric_dtype(series):

        return (
            pd.to_numeric(series, errors="coerce")
            .fillna(0)
            .astype(float)
            .ne(0)
        )

    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin([
            "true",
            "1",
            "yes",
            "significant"
        ])
    )


# ------------------------------------------------
# 5. STANDARDIZE TREND DATA
# ------------------------------------------------

def standardize_trends(df, label):

    feature_col = detect_feature_column(df)
    node_col = detect_node_column(df)

    sig_col = detect_significance_column(df)
    q_col = detect_q_column(df)

    direction_col = detect_direction_column(df)
    slope_col = detect_slope_column(df)

    # Explicitly prioritize significance columns
    # appropriate to each source file.

    if sig_col is not None:

        significance = to_boolean(df[sig_col])

    elif q_col is not None:

        significance = (
            pd.to_numeric(
                df[q_col],
                errors="coerce"
            ) < 0.05
        )

    else:

        raise KeyError(
            f"{label}: significance column not found.\n"
            f"Available columns: {df.columns.tolist()}"
        )

    result = pd.DataFrame({

        "feature": df[feature_col].astype(str),

        "node_id": df[node_col],

        "significant": significance

    })

    # ------------------------------------------------
    # Trend slope
    # ------------------------------------------------

    if slope_col is not None:

        result["sen_slope"] = pd.to_numeric(
            df[slope_col],
            errors="coerce"
        )

    else:

        result["sen_slope"] = np.nan

    # ------------------------------------------------
    # Trend direction
    # ------------------------------------------------

    if direction_col is not None:

        result["direction"] = (
            df[direction_col]
            .apply(
                lambda x: str(x).strip().lower()
                if pd.notna(x)
                else "unknown"
            )
        )

    elif slope_col is not None:

        slope = result["sen_slope"]

        result["direction"] = np.select(

            [
                slope > 0,
                slope < 0
            ],

            [
                "increasing",
                "decreasing"
            ],

            default="no_trend"

        )

    else:

        result["direction"] = "unknown"

    result["method"] = label

    duplicates = result.duplicated(
        subset=["feature", "node_id"]
    ).sum()

    if duplicates:

        print(
            f"WARNING: {label} has {duplicates} "
            "duplicate node-feature records."
        )

        result = result.drop_duplicates(
            subset=["feature", "node_id"],
            keep="first"
        )

    print(f"\n{label} detected columns:")

    print("Feature:", feature_col)
    print("Node:", node_col)
    print("Significance:", sig_col)
    print("Adjusted p:", q_col)
    print("Direction:", direction_col)
    print("Slope:", slope_col)

    return result


# ------------------------------------------------
# 6. STANDARDIZE EACH METHOD
# ------------------------------------------------

original_std = standardize_trends(
    original,
    "Original Seasonal MK"
)

seasonal_std = standardize_trends(
    seasonal_tfpw,
    "Seasonally Aligned TFPW"
)

initial_std = None

if initial_tfpw is not None:

    initial_std = standardize_trends(
        initial_tfpw,
        "Initial TFPW"
    )


# ------------------------------------------------
# 7. VERIFY NODE-FEATURE COVERAGE
# ------------------------------------------------

print("\n" + "=" * 75)
print("NODE-FEATURE COVERAGE")
print("=" * 75)

print(
    "Original:",
    original_std.shape
)

print(
    "Seasonal TFPW:",
    seasonal_std.shape
)

if initial_std is not None:

    print(
        "Initial TFPW:",
        initial_std.shape
    )

original_keys = set(
    zip(
        original_std["feature"],
        original_std["node_id"]
    )
)

seasonal_keys = set(
    zip(
        seasonal_std["feature"],
        seasonal_std["node_id"]
    )
)

if original_keys != seasonal_keys:

    print(
        "WARNING: Original and seasonal TFPW "
        "node-feature coverage differs."
    )

    print(
        "Only original:",
        len(original_keys - seasonal_keys)
    )

    print(
        "Only TFPW:",
        len(seasonal_keys - original_keys)
    )

else:

    print(
        "All node-feature records match."
    )


# ------------------------------------------------
# 8. MERGE ORIGINAL AND SEASONAL TFPW
# ------------------------------------------------

comparison = original_std.merge(

    seasonal_std,

    on=["feature", "node_id"],

    how="outer",

    suffixes=("_original", "_tfpw"),

    indicator=True

)

comparison["original_significant"] = (
    comparison["significant_original"]
    .fillna(False)
    .astype(bool)
)

comparison["tfpw_significant"] = (
    comparison["significant_tfpw"]
    .fillna(False)
    .astype(bool)
)


# ------------------------------------------------
# 9. SIGNIFICANCE ROBUSTNESS
# ------------------------------------------------

comparison["significance_category"] = np.select(

    [

        comparison["original_significant"]
        & comparison["tfpw_significant"],

        comparison["original_significant"]
        & ~comparison["tfpw_significant"],

        ~comparison["original_significant"]
        & comparison["tfpw_significant"]

    ],

    [

        "significant_in_both",

        "lost_significance",

        "newly_significant"

    ],

    default="not_significant_in_either"

)


# ------------------------------------------------
# 10. NORMALIZE TREND DIRECTIONS
# ------------------------------------------------

def normalize_direction(value):

    if pd.isna(value):
        return "unknown"

    value = str(value).strip().lower()

    if value in [
        "increasing",
        "increase",
        "positive",
        "up",
        "upward"
    ]:
        return "increasing"

    if value in [
        "decreasing",
        "decrease",
        "negative",
        "down",
        "downward"
    ]:
        return "decreasing"

    if value in [
        "no trend",
        "no_trend",
        "none",
        "stable",
        "zero"
    ]:
        return "no_trend"

    return "unknown"


comparison["original_direction"] = (
    comparison["direction_original"]
    .apply(normalize_direction)
)

comparison["tfpw_direction"] = (
    comparison["direction_tfpw"]
    .apply(normalize_direction)
)

comparison["direction_agreement"] = (

    comparison["original_direction"]
    == comparison["tfpw_direction"]

)

comparison["significant_direction_agreement"] = (

    comparison["original_significant"]

    & comparison["tfpw_significant"]

    & comparison["direction_agreement"]

)


# ------------------------------------------------
# 11. FEATURE-WISE ROBUSTNESS SUMMARY
# ------------------------------------------------

summary_records = []

for feature, group in comparison.groupby(
    "feature",
    sort=True
):

    original_sig = group[
        "original_significant"
    ]

    tfpw_sig = group[
        "tfpw_significant"
    ]

    both = original_sig & tfpw_sig

    lost = original_sig & ~tfpw_sig

    newly = ~original_sig & tfpw_sig

    neither = ~original_sig & ~tfpw_sig

    summary_records.append({

        "feature": feature,

        "nodes": len(group),

        "original_significant_nodes": int(
            original_sig.sum()
        ),

        "tfpw_significant_nodes": int(
            tfpw_sig.sum()
        ),

        "significant_in_both": int(
            both.sum()
        ),

        "lost_significance": int(
            lost.sum()
        ),

        "newly_significant": int(
            newly.sum()
        ),

        "not_significant_in_either": int(
            neither.sum()
        ),

        "original_increasing_nodes": int(

            (
                original_sig
                & group["original_direction"].eq(
                    "increasing"
                )
            ).sum()

        ),

        "original_decreasing_nodes": int(

            (
                original_sig
                & group["original_direction"].eq(
                    "decreasing"
                )
            ).sum()

        ),

        "tfpw_increasing_nodes": int(

            (
                tfpw_sig
                & group["tfpw_direction"].eq(
                    "increasing"
                )
            ).sum()

        ),

        "tfpw_decreasing_nodes": int(

            (
                tfpw_sig
                & group["tfpw_direction"].eq(
                    "decreasing"
                )
            ).sum()

        ),

        "direction_agreement_all_nodes": int(
            group["direction_agreement"].sum()
        ),

        "direction_agreement_significant_both": int(
            (
                both
                & group["direction_agreement"]
            ).sum()
        ),

        "mean_original_sen_slope": group[
            "sen_slope_original"
        ].mean(),

        "mean_tfpw_sen_slope": group[
            "sen_slope_tfpw"
        ].mean()

    })


feature_summary = pd.DataFrame(
    summary_records
)


# ------------------------------------------------
# 12. OPTIONAL INITIAL TFPW COMPARISON
# ------------------------------------------------

initial_summary = None

if initial_std is not None:

    initial_comparison = original_std.merge(

        initial_std,

        on=["feature", "node_id"],

        how="outer",

        suffixes=("_original", "_initial")

    )

    initial_comparison[
        "original_significant"
    ] = (

        initial_comparison[
            "significant_original"
        ]

        .fillna(False)

        .astype(bool)

    )

    initial_comparison[
        "initial_significant"
    ] = (

        initial_comparison[
            "significant_initial"
        ]

        .fillna(False)

        .astype(bool)

    )

    initial_summary = (

        initial_comparison

        .groupby("feature")

        .agg(

            nodes=("node_id", "nunique"),

            original_significant_nodes=(
                "original_significant",
                "sum"
            ),

            initial_tfpw_significant_nodes=(
                "initial_significant",
                "sum"
            )

        )

        .reset_index()

    )


# ------------------------------------------------
# 13. CELL 24 AUTOCORRELATION SUMMARY
# ------------------------------------------------

if diagnostics is not None:

    diagnostic_feature_col = detect_feature_column(
        diagnostics
    )

    centered_col = find_column(

        diagnostics,

        [
            "mean_centered_rho",
            "mean_centered_residual_rho",
            "centered_rho"
        ],

        required=False

    )

    uncentered_col = find_column(

        diagnostics,

        [
            "mean_uncentered_rho",
            "mean_uncentered_residual_rho",
            "uncentered_rho"
        ],

        required=False

    )

    if centered_col is not None:

        diagnostic_summary = pd.DataFrame({

            "feature": diagnostics[
                diagnostic_feature_col
            ].astype(str),

            "mean_centered_rho": pd.to_numeric(

                diagnostics[centered_col],

                errors="coerce"

            )

        })

        if uncentered_col is not None:

            diagnostic_summary[
                "mean_uncentered_rho"
            ] = pd.to_numeric(

                diagnostics[uncentered_col],

                errors="coerce"

            )

        diagnostic_summary = (

            diagnostic_summary

            .groupby("feature")

            .mean(numeric_only=True)

            .reset_index()

        )

        feature_summary = feature_summary.merge(

            diagnostic_summary,

            on="feature",

            how="left"

        )


# ------------------------------------------------
# 14. ROBUSTNESS CLASSIFICATION
# ------------------------------------------------

def classify_robustness(row):

    both = row["significant_in_both"]

    original_count = row[
        "original_significant_nodes"
    ]

    tfpw_count = row[
        "tfpw_significant_nodes"
    ]

    if both == 0:

        return "No shared significant nodes"

    overlap = both / max(
        original_count,
        tfpw_count,
        1
    )

    if overlap >= 0.75:

        return "High node overlap"

    elif overlap >= 0.40:

        return "Moderate node overlap"

    else:

        return "Low node overlap"


feature_summary["robustness_label"] = (
    feature_summary.apply(
        classify_robustness,
        axis=1
    )
)


# ------------------------------------------------
# 15. SAVE NODE-WISE COMPARISON
# ------------------------------------------------

comparison_file = (
    OUTPUT_DIR
    / "node_wise_trend_robustness.csv"
)

comparison.to_csv(
    comparison_file,
    index=False
)


# ------------------------------------------------
# 16. SAVE FEATURE-WISE SUMMARY
# ------------------------------------------------

summary_file = (
    OUTPUT_DIR
    / "feature_wise_trend_robustness.csv"
)

feature_summary.to_csv(
    summary_file,
    index=False
)


# ------------------------------------------------
# 17. SAVE DIRECTION COMPARISON
# ------------------------------------------------

direction_summary = (

    comparison

    .groupby(

        [
            "feature",

            "original_direction",

            "tfpw_direction"

        ]

    )

    .size()

    .reset_index(name="node_count")

)

direction_file = (
    OUTPUT_DIR
    / "trend_direction_comparison.csv"
)

direction_summary.to_csv(
    direction_file,
    index=False
)


# ------------------------------------------------
# 18. SAVE SIGNIFICANCE CATEGORY SUMMARY
# ------------------------------------------------

category_summary = (

    comparison

    .groupby(
        [
            "feature",
            "significance_category"
        ]
    )

    .size()

    .reset_index(name="node_count")

)

category_file = (
    OUTPUT_DIR
    / "significance_category_summary.csv"
)

category_summary.to_csv(
    category_file,
    index=False
)


# ------------------------------------------------
# 19. SAVE METADATA
# ------------------------------------------------

metadata = {

    "project": "NASA Earth Systems Trend Detective",

    "cell": 25,

    "analysis": "Final trend robustness comparison",

    "primary_method": (
        "Original Seasonal Mann-Kendall "
        "and Sen slope"
    ),

    "sensitivity_method": (
        "Seasonally aligned TFPW"
    ),

    "initial_tfpw_included": (
        initial_std is not None
    ),

    "features": (
        feature_summary["feature"].tolist()
    ),

    "significance_threshold": 0.05,

    "fdr_method": (
        "Benjamini-Hochberg correction "
        "inherited from Cells 20 and 23"
    ),

    "important_limitations": [

        "Only ten annual observations "
        "per calendar month",

        "Autocorrelation estimates are uncertain",

        "TFPW results depend on prewhitening assumptions",

        "Spatial and temporal dependence may remain",

        "FDR significance does not establish causality",

        "Trend analysis does not establish future "
        "climate behavior"

    ],

    "created_at": datetime.now().isoformat()

}


metadata_file = (
    OUTPUT_DIR
    / "final_trend_robustness_metadata.json"
)

with open(
    metadata_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metadata,
        file,
        indent=4
    )


# ------------------------------------------------
# 20. DISPLAY FINAL RESULTS
# ------------------------------------------------

print("\n" + "=" * 75)

print("FINAL FEATURE-WISE TREND ROBUSTNESS")

print("=" * 75)

display(
    feature_summary.round(4)
)


print("\n" + "=" * 75)

print("SIGNIFICANCE ROBUSTNESS CATEGORIES")

print("=" * 75)

display(
    category_summary
)


print("\n" + "=" * 75)

print("TREND DIRECTION COMPARISON")

print("=" * 75)

display(
    direction_summary
)


if initial_summary is not None:

    print("\n" + "=" * 75)

    print("INITIAL TFPW COMPARISON")

    print("=" * 75)

    display(
        initial_summary
    )


# ------------------------------------------------
# 21. SCIENTIFIC INTERPRETATION
# ------------------------------------------------

print("\n" + "=" * 75)

print("SCIENTIFIC INTERPRETATION")

print("=" * 75)

print(
    """
1. Cell 20 remains the primary trend analysis.

2. Cell 23 is a sensitivity analysis,
   not a replacement for Cell 20.

3. Nodes significant under both methods
   show method-consistent significance.

4. Newly significant nodes are method-sensitive
   and should not be treated as confirmed discoveries.

5. Sen slopes describe estimated monotonic
   change during the 2015-2024 observation period.

6. These analyses do not establish causality,
   attribution, or future climate behavior.

7. Only ten annual observations are available
   for each calendar-month residual sequence.
"""
)


# ------------------------------------------------
# 22. FINAL OUTPUT LOCATIONS
# ------------------------------------------------

print("\n" + "=" * 75)

print("CELL 25 COMPLETED SUCCESSFULLY")

print("=" * 75)

print("\nNode-wise comparison:")
print(comparison_file)

print("\nFeature-wise summary:")
print(summary_file)

print("\nDirection comparison:")
print(direction_file)

print("\nSignificance categories:")
print(category_file)

print("\nMetadata:")
print(metadata_file)

if initial_summary is not None:

    print("\nInitial TFPW summary:")
    print(
        OUTPUT_DIR
        / "initial_tfpw_comparison_summary.csv"
    )

print("\nShare the FINAL FEATURE-WISE TREND ROBUSTNESS table.")

print("=" * 75)


# ============================================================
# ORIGINAL NOTEBOOK CELL 30
# Execution count: 37
# ============================================================


import pandas as pd
from pathlib import Path
from IPython.display import display

OUTPUT_DIR = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective\outputs\final_trend_robustness"
)

# 1. Complete feature-wise summary
print("=" * 75)
print("FINAL FEATURE-WISE TREND ROBUSTNESS")
print("=" * 75)

summary = pd.read_csv(
    OUTPUT_DIR / "feature_wise_trend_robustness.csv"
)

display(summary.to_string(index=False))

# 2. Significance categories
print("\n" + "=" * 75)
print("SIGNIFICANCE CATEGORY SUMMARY")
print("=" * 75)

categories = pd.read_csv(
    OUTPUT_DIR / "significance_category_summary.csv"
)

display(categories)

# 3. Direction comparison
print("\n" + "=" * 75)
print("TREND DIRECTION COMPARISON")
print("=" * 75)

directions = pd.read_csv(
    OUTPUT_DIR / "trend_direction_comparison.csv"
)

display(directions)

# 4. Initial TFPW comparison
initial_file = (
    OUTPUT_DIR / "initial_tfpw_comparison_summary.csv"
)

if initial_file.exists():

    print("\n" + "=" * 75)
    print("INITIAL TFPW COMPARISON")
    print("=" * 75)

    display(
        pd.read_csv(initial_file)
    )


# ============================================================
# ORIGINAL NOTEBOOK CELL 31
# Execution count: 38
# ============================================================


# ================================================================
# CELL 26: FINAL SCIENTIFIC VALIDATION AND CONSOLIDATED REPORT
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import json
import pandas as pd
import numpy as np

from pathlib import Path
from datetime import datetime

# ------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

OUTPUT_ROOT = PROJECT_ROOT / "outputs"

REPORT_DIR = OUTPUT_ROOT / "final_scientific_report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = PROJECT_ROOT / "data" / "processed"

TRAIN_DIR = OUTPUT_ROOT / "model_training"
GRAPH_DIR = OUTPUT_ROOT / "spatial_graph"
FORECAST_DIR = OUTPUT_ROOT / "future_forecasting"
TREND_DIR = OUTPUT_ROOT / "historical_trend_analysis"
TFPW_DIR = OUTPUT_ROOT / "seasonal_tfpw_analysis"
AUTO_DIR = OUTPUT_ROOT / "autocorrelation_analysis"
ROBUSTNESS_DIR = OUTPUT_ROOT / "final_trend_robustness"

FEATURES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

report = {
    "project": "NASA Earth Systems Trend Detective",
    "generated_at": datetime.now().isoformat(),
    "study_region": "India",
    "historical_period": "January 2015 - December 2024",
    "forecast_period": "January 2025 - December 2025",
    "data_source": "NASA POWER",
    "features": FEATURES,
    "validation_sections": {}
}

print("=" * 75)
print("NASA EARTH SYSTEMS TREND DETECTIVE")
print("FINAL SCIENTIFIC VALIDATION")
print("=" * 75)


# ------------------------------------------------
# 2. DATASET VALIDATION
# ------------------------------------------------

print("\n[1] DATASET VALIDATION")

tensor_path = DATA_DIR / "nasa_power_tensor.npy"
nodes_path = DATA_DIR / "spatial_nodes.csv"
time_path = DATA_DIR / "tensor_time_index.npy"

assert tensor_path.exists(), f"Missing: {tensor_path}"
assert nodes_path.exists(), f"Missing: {nodes_path}"
assert time_path.exists(), f"Missing: {time_path}"

tensor = np.load(tensor_path)
nodes = pd.read_csv(nodes_path)
time_index = np.load(time_path, allow_pickle=True)

assert tensor.ndim == 3
assert tensor.shape[1] == len(nodes)
assert tensor.shape[0] == len(time_index)
assert tensor.shape[2] == len(FEATURES)

dataset_check = {
    "tensor_shape": list(tensor.shape),
    "time_steps": int(tensor.shape[0]),
    "spatial_nodes": int(tensor.shape[1]),
    "features": int(tensor.shape[2]),
    "missing_values": int(np.isnan(tensor).sum()),
    "infinite_values": int(np.isinf(tensor).sum()),
    "all_values_finite": bool(np.isfinite(tensor).all()),
    "coordinate_columns": list(nodes.columns),
    "latitude_min": float(nodes["grid_latitude"].min()),
    "latitude_max": float(nodes["grid_latitude"].max()),
    "longitude_min": float(nodes["grid_longitude"].min()),
    "longitude_max": float(nodes["grid_longitude"].max())
}

report["validation_sections"]["dataset"] = dataset_check

print("Tensor shape:", tensor.shape)
print("Spatial nodes:", len(nodes))
print("Time steps:", len(time_index))
print("Features:", FEATURES)
print("Missing values:", dataset_check["missing_values"])
print("Infinite values:", dataset_check["infinite_values"])
print("Latitude range:",
      dataset_check["latitude_min"],
      "to",
      dataset_check["latitude_max"])
print("Longitude range:",
      dataset_check["longitude_min"],
      "to",
      dataset_check["longitude_max"])


# ------------------------------------------------
# 3. SPATIAL GRAPH VALIDATION
# ------------------------------------------------

print("\n[2] SPATIAL GRAPH VALIDATION")

adjacency_path = GRAPH_DIR / "adjacency_matrix.npz"
graph_metadata_path = GRAPH_DIR / "graph_metadata.json"

assert adjacency_path.exists(), f"Missing: {adjacency_path}"

from scipy.sparse import load_npz

adjacency = load_npz(adjacency_path).toarray()

graph_check = {
    "adjacency_shape": list(adjacency.shape),
    "node_count": int(adjacency.shape[0]),
    "symmetric": bool(np.allclose(adjacency, adjacency.T)),
    "self_loops_present": bool(np.all(np.diag(adjacency) > 0)),
    "nonzero_entries": int(np.count_nonzero(adjacency)),
    "average_degree_including_self_loops": float(
        np.count_nonzero(adjacency, axis=1).mean()
    ),
    "graph_method": "BallTree haversine K-nearest-neighbor proximity graph",
    "nearest_neighbors": 6
}

if graph_metadata_path.exists():
    with open(graph_metadata_path, "r", encoding="utf-8") as f:
        graph_check["saved_metadata"] = json.load(f)

report["validation_sections"]["spatial_graph"] = graph_check

print("Adjacency shape:", adjacency.shape)
print("Symmetric:", graph_check["symmetric"])
print("Self-loops present:", graph_check["self_loops_present"])
print("Nonzero entries:", graph_check["nonzero_entries"])
print("Average degree:", round(
    graph_check["average_degree_including_self_loops"], 2
))


# ------------------------------------------------
# 4. MODEL EVALUATION
# ------------------------------------------------

print("\n[3] MODEL EVALUATION")

# Values from the completed Cell 15 test evaluation.
# The evaluation used rolling one-step-ahead predictions
# over the 12 months of 2024.

model_metrics = {
    "T2M": {
        "unit": "degree Celsius",
        "model_mae": 1.5412,
        "model_rmse": 2.2789,
        "model_r2": 0.9714,
        "persistence_mae": 2.4534,
        "persistence_rmse": 3.3658,
        "persistence_r2": 0.9375
    },
    "PRECTOTCORR": {
        "unit": "mm/day",
        "model_mae": 1.3726,
        "model_rmse": 2.5789,
        "model_r2": 0.7317,
        "persistence_mae": 2.1343,
        "persistence_rmse": 3.7510,
        "persistence_r2": 0.4323
    },
    "RH2M": {
        "unit": "%",
        "model_mae": 4.0046,
        "model_rmse": 5.6396,
        "model_r2": 0.9052,
        "persistence_mae": 5.7333,
        "persistence_rmse": 8.3572,
        "persistence_r2": 0.7918
    },
    "WS10M": {
        "unit": "m/s",
        "model_mae": 0.5185,
        "model_rmse": 0.7100,
        "model_r2": 0.8248,
        "persistence_mae": 0.7061,
        "persistence_rmse": 1.0434,
        "persistence_r2": 0.6216
    }
}

for feature, metrics in model_metrics.items():
    mae_improvement = (
        (metrics["persistence_mae"] - metrics["model_mae"])
        / metrics["persistence_mae"]
    ) * 100

    rmse_improvement = (
        (metrics["persistence_rmse"] - metrics["model_rmse"])
        / metrics["persistence_rmse"]
    ) * 100

    metrics["mae_improvement_percent"] = round(
        mae_improvement, 2
    )
    metrics["rmse_improvement_percent"] = round(
        rmse_improvement, 2
    )

model_check = {
    "architecture": "GCN-GRU",
    "device_used": "CUDA GPU",
    "training_period": "2015-2021",
    "validation_period": "2022-2023",
    "testing_period": "2024",
    "evaluation_type": "Rolling one-step-ahead",
    "metrics": model_metrics,
    "beats_persistence_on_all_features": bool(
        all(
            m["model_mae"] < m["persistence_mae"]
            and m["model_rmse"] < m["persistence_rmse"]
            for m in model_metrics.values()
        )
    )
}

report["validation_sections"]["model_evaluation"] = model_check

for feature, metrics in model_metrics.items():
    print(
        feature,
        "| MAE:", metrics["model_mae"],
        "| RMSE:", metrics["model_rmse"],
        "| R2:", metrics["model_r2"],
        "| MAE improvement:",
        metrics["mae_improvement_percent"], "%"
    )

print(
    "Beats persistence on all features:",
    model_check["beats_persistence_on_all_features"]
)


# ------------------------------------------------
# 5. FORECAST VALIDATION
# ------------------------------------------------

print("\n[4] FORECAST VALIDATION")

forecast_path = FORECAST_DIR / "forecast_2025_physical.npy"
forecast_summary_path = (
    FORECAST_DIR / "forecast_monthly_summary_2025.csv"
)

assert forecast_path.exists(), f"Missing: {forecast_path}"
assert forecast_summary_path.exists(), (
    f"Missing: {forecast_summary_path}"
)

forecast = np.load(forecast_path)
forecast_summary = pd.read_csv(forecast_summary_path)

assert forecast.shape == (12, len(nodes), len(FEATURES))

forecast_check = {
    "forecast_shape": list(forecast.shape),
    "forecast_months": 12,
    "finite_values": bool(np.isfinite(forecast).all()),
    "feature_ranges": {}
}

for i, feature in enumerate(FEATURES):
    values = forecast[:, :, i]

    forecast_check["feature_ranges"][feature] = {
        "minimum": float(np.min(values)),
        "maximum": float(np.max(values)),
        "mean": float(np.mean(values)),
        "negative_values": int(np.sum(values < 0))
    }

print("Forecast shape:", forecast.shape)
print("All values finite:", forecast_check["finite_values"])

for feature, values in forecast_check["feature_ranges"].items():
    print(
        feature,
        "| Min:", round(values["minimum"], 4),
        "| Max:", round(values["maximum"], 4),
        "| Mean:", round(values["mean"], 4),
        "| Negative values:", values["negative_values"]
    )

report["validation_sections"]["forecast"] = forecast_check

# Precipitation plausibility
negative_precipitation = forecast_check[
    "feature_ranges"
]["PRECTOTCORR"]["negative_values"]

report["validation_sections"]["forecast"][
    "negative_precipitation_warning"
] = (
    "Negative precipitation predictions exist. "
    "Raw model outputs have not been silently clipped. "
    "A future model version should enforce nonnegative precipitation."
)

print(
    "Negative precipitation predictions:",
    negative_precipitation
)


# ------------------------------------------------
# 6. HISTORICAL TREND ROBUSTNESS
# ------------------------------------------------

print("\n[5] HISTORICAL TREND ROBUSTNESS")

trend_summary_path = TREND_DIR / "feature_trend_summary.csv"
robustness_path = (
    ROBUSTNESS_DIR / "feature_wise_trend_robustness.csv"
)
autocorrelation_path = (
    AUTO_DIR / "autocorrelation_summary.csv"
)

assert trend_summary_path.exists(), (
    f"Missing: {trend_summary_path}"
)
assert robustness_path.exists(), (
    f"Missing: {robustness_path}"
)

trend_summary = pd.read_csv(trend_summary_path)
robustness_summary = pd.read_csv(robustness_path)

trend_check = {
    "primary_method": "Seasonal Mann-Kendall with Sen's slope",
    "multiple_testing_correction": "Benjamini-Hochberg FDR",
    "total_node_feature_tests": 1020,
    "robustness_method": "Seasonally aligned TFPW sensitivity analysis",
    "primary_trend_summary": trend_summary.to_dict(
        orient="records"
    ),
    "robustness_summary": robustness_summary.to_dict(
        orient="records"
    )
}

report["validation_sections"]["historical_trends"] = trend_check

print("\nPrimary Seasonal Mann-Kendall summary:")
display(trend_summary)

print("\nTrend robustness comparison:")
display(robustness_summary)

if autocorrelation_path.exists():
    autocorrelation_summary = pd.read_csv(
        autocorrelation_path
    )

    report["validation_sections"][
        "autocorrelation"
    ] = autocorrelation_summary.to_dict(
        orient="records"
    )

    print("\nAutocorrelation summary:")
    display(autocorrelation_summary)


# ------------------------------------------------
# 7. SCIENTIFIC LIMITATIONS
# ------------------------------------------------

print("\n[6] SCIENTIFIC LIMITATIONS")

limitations = [
    "The current model uses NASA POWER data with four meteorological variables.",
    "The current analysis does not yet integrate all planned satellite and greenhouse-gas datasets.",
    "The spatial graph is a BallTree haversine proximity graph, not an exact HEALPix spherical grid.",
    "The spatial graph does not explicitly model atmospheric transport or physical conservation laws.",
    "The historical record covers only ten years, which is short for robust climate-trend attribution.",
    "Seasonal autocorrelation estimates are uncertain because each calendar-month series contains only ten annual observations.",
    "TFPW results are sensitivity analyses and are not definitive corrections for all temporal dependence.",
    "Trend detection does not establish causal relationships.",
    "The 2025 autoregressive forecast is exploratory and does not include future external forcing.",
    "The 2024 test evaluation is rolling one-step-ahead, whereas the 2025 forecast is autoregressive.",
    "Negative precipitation predictions indicate a physical plausibility limitation of the current model.",
    "The analysis should not be presented as an operational weather or climate forecasting service."
]

report["validation_sections"]["scientific_limitations"] = limitations

for number, limitation in enumerate(limitations, start=1):
    print(f"{number}. {limitation}")


# ------------------------------------------------
# 8. FINAL VALIDATION STATUS
# ------------------------------------------------

checks = {
    "dataset_dimensions_valid": (
        tensor.shape == (120, 255, 4)
    ),
    "dataset_values_finite": bool(
        np.isfinite(tensor).all()
    ),
    "graph_dimensions_valid": (
        adjacency.shape == (255, 255)
    ),
    "graph_symmetric": graph_check["symmetric"],
    "model_beats_persistence": (
        model_check["beats_persistence_on_all_features"]
    ),
    "forecast_dimensions_valid": (
        forecast.shape == (12, 255, 4)
    ),
    "forecast_values_finite": (
        forecast_check["finite_values"]
    ),
    "trend_analysis_available": (
        trend_summary_path.exists()
    ),
    "robustness_analysis_available": (
        robustness_path.exists()
    )
}

report["validation_checks"] = checks
report["all_structural_checks_passed"] = bool(
    all(checks.values())
)

print("\n" + "=" * 75)
print("FINAL VALIDATION CHECKLIST")
print("=" * 75)

for check_name, status in checks.items():
    print(
        ("PASS" if status else "FAIL"),
        "|",
        check_name
    )

print(
    "\nAll structural checks passed:",
    report["all_structural_checks_passed"]
)


# ------------------------------------------------
# 9. SAVE JSON REPORT
# ------------------------------------------------

json_path = REPORT_DIR / "final_scientific_validation.json"

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=4, default=str)


# ------------------------------------------------
# 10. GENERATE HUMAN-READABLE MARKDOWN REPORT
# ------------------------------------------------

md = []

md.append("# NASA Earth Systems Trend Detective")
md.append("## Final Scientific Validation Report")
md.append("")
md.append(f"Generated: {report['generated_at']}")
md.append("")
md.append("### 1. Project Overview")
md.append("")
md.append("- Study region: India")
md.append("- Historical period: 2015-2024")
md.append("- Forecast period: 2025")
md.append("- Data source used in current model: NASA POWER")
md.append("- Spatial nodes: 255")
md.append("- Temporal observations: 120 months")
md.append("- Variables: T2M, PRECTOTCORR, RH2M, WS10M")
md.append("")
md.append("### 2. Model Architecture")
md.append("")
md.append("- Model: GCN-GRU")
md.append("- Spatial representation: BallTree haversine proximity graph")
md.append("- Training: 2015-2021")
md.append("- Validation: 2022-2023")
md.append("- Testing: 2024")
md.append("- Evaluation: Rolling one-step-ahead")
md.append("")
md.append("### 3. Test Performance")
md.append("")
md.append("| Feature | Model MAE | Model RMSE | Model R2 | Persistence MAE | Persistence RMSE |")
md.append("|---|---:|---:|---:|---:|---:|")

for feature, m in model_metrics.items():
    md.append(
        f"| {feature} | {m['model_mae']:.4f} "
        f"| {m['model_rmse']:.4f} "
        f"| {m['model_r2']:.4f} "
        f"| {m['persistence_mae']:.4f} "
        f"| {m['persistence_rmse']:.4f} |"
    )

md.append("")
md.append("The model outperformed the persistence baseline on MAE and RMSE for all four variables in the 2024 rolling test.")
md.append("")
md.append("### 4. Historical Trend Analysis")
md.append("")
md.append("- Primary test: Seasonal Mann-Kendall")
md.append("- Trend magnitude: Sen's slope")
md.append("- Multiple testing: Benjamini-Hochberg FDR")
md.append("- Total tests: 1,020 node-feature combinations")
md.append("- Sensitivity analysis: Seasonally aligned TFPW")
md.append("")
md.append("TFPW significance results are treated as sensitivity evidence rather than independent confirmation.")
md.append("")
md.append("### 5. Forecasting")
md.append("")
md.append("- Forecast horizon: 12 months in 2025")
md.append("- Method: Autoregressive GCN-GRU")
md.append("- Forecasts are exploratory and do not include future external forcing.")
md.append("- Negative precipitation predictions require attention in future model development.")
md.append("")
md.append("### 6. Scientific Limitations")
md.append("")

for limitation in limitations:
    md.append(f"- {limitation}")

md.append("")
md.append("### 7. Validation Checklist")
md.append("")
md.append("| Validation | Status |")
md.append("|---|---|")

for name, status in checks.items():
    md.append(
        f"| {name.replace('_', ' ').title()} "
        f"| {'PASS' if status else 'FAIL'} |"
    )

md.append("")
md.append("### 8. Conclusion")
md.append("")
md.append(
    "The current implementation demonstrates a working "
    "spatiotemporal GCN-GRU pipeline for four NASA POWER "
    "meteorological variables over a 255-node India study grid. "
    "The model outperformed a persistence baseline on the "
    "2024 rolling test. Historical trend analysis and a "
    "seasonally aligned TFPW sensitivity analysis were also "
    "completed. The 2025 autoregressive output is exploratory. "
    "The current system is a research prototype, not an "
    "operational climate prediction or causal attribution system."
)

markdown_path = REPORT_DIR / "final_scientific_validation.md"

markdown_path.write_text(
    "\n".join(md),
    encoding="utf-8"
)


# ------------------------------------------------
# 11. SAVE A COMPACT METRICS CSV
# ------------------------------------------------

metrics_rows = []

for feature, m in model_metrics.items():
    metrics_rows.append({
        "feature": feature,
        "unit": m["unit"],
        "model_mae": m["model_mae"],
        "model_rmse": m["model_rmse"],
        "model_r2": m["model_r2"],
        "persistence_mae": m["persistence_mae"],
        "persistence_rmse": m["persistence_rmse"],
        "persistence_r2": m["persistence_r2"],
        "mae_improvement_percent": m[
            "mae_improvement_percent"
        ],
        "rmse_improvement_percent": m[
            "rmse_improvement_percent"
        ]
    })

metrics_path = REPORT_DIR / "final_model_metrics.csv"

pd.DataFrame(metrics_rows).to_csv(
    metrics_path,
    index=False
)


# ------------------------------------------------
# 12. COMPLETION
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 26 COMPLETED")
print("=" * 75)

print("\nReports saved to:")
print(REPORT_DIR)

print("\n1.", json_path.name)
print("2.", markdown_path.name)
print("3.", metrics_path.name)

print("\nOpen the Markdown report for the complete summary.")


# ============================================================
# ORIGINAL NOTEBOOK CELL 32
# Execution count: 39
# ============================================================


# ================================================================
# CELL 27: INDEPENDENT MODEL VERIFICATION AND ERROR ANALYSIS
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import json
import numpy as np
import pandas as pd
import torch

from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from IPython.display import display

# ------------------------------------------------
# 1. PATHS AND CONFIGURATION
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

TRAIN_DIR = PROJECT_ROOT / "outputs" / "model_training"
DATA_DIR = PROJECT_ROOT / "data" / "processed"
GRAPH_DIR = PROJECT_ROOT / "outputs" / "spatial_graph"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "independent_model_verification"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = ["T2M", "PRECTOTCORR", "RH2M", "WS10M"]

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 75)
print("INDEPENDENT GCN-GRU MODEL VERIFICATION")
print("=" * 75)

print("Device:", DEVICE)


# ------------------------------------------------
# 2. LOAD TEST SEQUENCES AND SCALER
# ------------------------------------------------

X_test = np.load(TRAIN_DIR / "X_test_seq.npy")
y_test = np.load(TRAIN_DIR / "y_test_seq.npy")

scaler_path = TRAIN_DIR / "scaler_metadata.json"

with open(scaler_path, "r", encoding="utf-8") as f:
    scaler_metadata = json.load(f)

print("\nTest input shape:", X_test.shape)
print("Test target shape:", y_test.shape)

# The model outputs normalized values.
# These are the train-only scaling parameters from Cell 9.

if "mean" in scaler_metadata:
    scaler_mean = np.array(
        scaler_metadata["mean"], dtype=np.float32
    )
    scaler_std = np.array(
        scaler_metadata["std"], dtype=np.float32
    )
elif "scaler_mean" in scaler_metadata:
    scaler_mean = np.array(
        scaler_metadata["scaler_mean"], dtype=np.float32
    )
    scaler_std = np.array(
        scaler_metadata["scaler_std"], dtype=np.float32
    )
else:
    raise KeyError(
        "Could not identify scaler mean/std keys. "
        "Inspect scaler_metadata.json before continuing."
    )

assert scaler_mean.shape == (4,)
assert scaler_std.shape == (4,)

print("Scaler means:", scaler_mean)
print("Scaler standard deviations:", scaler_std)


# ------------------------------------------------
# 3. LOAD GRAPH
# ------------------------------------------------

from scipy.sparse import load_npz

adjacency_path = GRAPH_DIR / "adjacency_matrix.npz"

adjacency = load_npz(adjacency_path).toarray()

adjacency_tensor = torch.tensor(
    adjacency,
    dtype=torch.float32,
    device=DEVICE
)

print("\nAdjacency shape:", adjacency_tensor.shape)


# ------------------------------------------------
# 4. REBUILD MODEL ARCHITECTURE
# ------------------------------------------------

# Import the exact architecture from your training code.
# If your architecture is defined in a Python module,
# update this import to its actual location.

import sys

SCIENTIFIC_ENGINE = PROJECT_ROOT / "scientific-engine"

if str(SCIENTIFIC_ENGINE) not in sys.path:
    sys.path.insert(0, str(SCIENTIFIC_ENGINE))

# IMPORTANT:
# Replace this import with the exact class/module used
# in Cell 12 if your training notebook defined it inline.

from models.gcn_gru import GCNGRU

config_path = TRAIN_DIR / "gcn_gru_config.json"

with open(config_path, "r", encoding="utf-8") as f:
    model_config = json.load(f)

print("\nModel configuration:")
print(json.dumps(model_config, indent=2))

# Inspect constructor arguments if necessary.
# These values match the architecture validated in Cell 12.

model = GCNGRU(
    input_dim=4,
    gcn_hidden_dim=32,
    gru_hidden_dim=64,
    output_dim=4,
    dropout=0.15
).to(DEVICE)

checkpoint_path = TRAIN_DIR / "best_gcn_gru_model.pth"

checkpoint = torch.load(
    checkpoint_path,
    map_location=DEVICE,
    weights_only=False
)

if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
    state_dict = checkpoint["model_state_dict"]
else:
    state_dict = checkpoint

model.load_state_dict(state_dict)
model.eval()

print("\nCheckpoint loaded successfully.")


# ------------------------------------------------
# 5. INDEPENDENT PREDICTION
# ------------------------------------------------

X_tensor = torch.tensor(
    X_test,
    dtype=torch.float32,
    device=DEVICE
)

with torch.no_grad():
    predictions_normalized = model(
        X_tensor,
        adjacency_tensor
    )

predictions_normalized = (
    predictions_normalized.detach().cpu().numpy()
)

actual_normalized = y_test

print("\nPrediction shape:", predictions_normalized.shape)
print("Actual shape:", actual_normalized.shape)

assert predictions_normalized.shape == actual_normalized.shape


# ------------------------------------------------
# 6. CONVERT TO PHYSICAL UNITS
# ------------------------------------------------

predictions = (
    predictions_normalized * scaler_std.reshape(1, 1, -1)
    + scaler_mean.reshape(1, 1, -1)
)

actual = (
    actual_normalized * scaler_std.reshape(1, 1, -1)
    + scaler_mean.reshape(1, 1, -1)
)

print("\nPhysical predictions:", predictions.shape)
print("Physical actual:", actual.shape)


# ------------------------------------------------
# 7. METRIC CALCULATION
# ------------------------------------------------

metric_rows = []

for i, feature in enumerate(FEATURES):

    y_true = actual[:, :, i].reshape(-1)
    y_pred = predictions[:, :, i].reshape(-1)

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)

    metric_rows.append({
        "feature": feature,
        "model_mae": mae,
        "model_rmse": rmse,
        "model_r2": r2
    })

independent_metrics = pd.DataFrame(metric_rows)

print("\nINDEPENDENT MODEL METRICS")
display(independent_metrics)


# ------------------------------------------------
# 8. PERSISTENCE BASELINE
# ------------------------------------------------

# Persistence predicts the next month using the final
# observation in the preceding 12-month input sequence.

persistence_normalized = X_test[:, -1, :, :]

persistence = (
    persistence_normalized
    * scaler_std.reshape(1, 1, -1)
    + scaler_mean.reshape(1, 1, -1)
)

baseline_rows = []

for i, feature in enumerate(FEATURES):

    y_true = actual[:, :, i].reshape(-1)
    y_pred = persistence[:, :, i].reshape(-1)

    baseline_rows.append({
        "feature": feature,
        "persistence_mae": mean_absolute_error(
            y_true, y_pred
        ),
        "persistence_rmse": np.sqrt(
            mean_squared_error(y_true, y_pred)
        ),
        "persistence_r2": r2_score(y_true, y_pred)
    })

baseline_metrics = pd.DataFrame(baseline_rows)

comparison = independent_metrics.merge(
    baseline_metrics,
    on="feature"
)

comparison["mae_improvement_percent"] = (
    (
        comparison["persistence_mae"]
        - comparison["model_mae"]
    )
    / comparison["persistence_mae"]
) * 100

comparison["rmse_improvement_percent"] = (
    (
        comparison["persistence_rmse"]
        - comparison["model_rmse"]
    )
    / comparison["persistence_rmse"]
) * 100

print("\nMODEL VS PERSISTENCE")
display(comparison)


# ------------------------------------------------
# 9. MONTHLY ERROR ANALYSIS
# ------------------------------------------------

monthly_rows = []

for month in range(actual.shape[0]):

    for i, feature in enumerate(FEATURES):

        y_true = actual[month, :, i]
        y_pred = predictions[month, :, i]

        monthly_rows.append({
            "month_index": month + 1,
            "feature": feature,
            "mae": mean_absolute_error(
                y_true, y_pred
            ),
            "rmse": np.sqrt(
                mean_squared_error(y_true, y_pred)
            )
        })

monthly_errors = pd.DataFrame(monthly_rows)

monthly_errors.to_csv(
    OUTPUT_DIR / "monthly_error_analysis.csv",
    index=False
)

print("\nMONTHLY ERROR ANALYSIS")
display(monthly_errors)


# ------------------------------------------------
# 10. SPATIAL NODE ERROR ANALYSIS
# ------------------------------------------------

nodes = pd.read_csv(
    DATA_DIR / "spatial_nodes.csv"
)

spatial_rows = []

for node in range(actual.shape[1]):

    for i, feature in enumerate(FEATURES):

        y_true = actual[:, node, i]
        y_pred = predictions[:, node, i]

        spatial_rows.append({
            "node_id": int(node),
            "feature": feature,
            "grid_latitude": float(
                nodes.iloc[node]["grid_latitude"]
            ),
            "grid_longitude": float(
                nodes.iloc[node]["grid_longitude"]
            ),
            "mae": mean_absolute_error(
                y_true, y_pred
            ),
            "rmse": np.sqrt(
                mean_squared_error(y_true, y_pred)
            )
        })

spatial_errors = pd.DataFrame(spatial_rows)

spatial_errors.to_csv(
    OUTPUT_DIR / "spatial_node_error_analysis.csv",
    index=False
)

print("\nWORST 10 SPATIAL NODES BY MAE")

for feature in FEATURES:

    print("\nFeature:", feature)

    worst = (
        spatial_errors[
            spatial_errors["feature"] == feature
        ]
        .sort_values("mae", ascending=False)
        .head(10)
    )

    display(worst)


# ------------------------------------------------
# 11. REPRODUCIBILITY CHECK
# ------------------------------------------------

reference_metrics = {
    "T2M": {
        "mae": 1.5412,
        "rmse": 2.2789,
        "r2": 0.9714
    },
    "PRECTOTCORR": {
        "mae": 1.3726,
        "rmse": 2.5789,
        "r2": 0.7317
    },
    "RH2M": {
        "mae": 4.0046,
        "rmse": 5.6396,
        "r2": 0.9052
    },
    "WS10M": {
        "mae": 0.5185,
        "rmse": 0.7100,
        "r2": 0.8248
    }
}

reproducibility_rows = []

for _, row in independent_metrics.iterrows():

    reference = reference_metrics[row["feature"]]

    reproducibility_rows.append({
        "feature": row["feature"],
        "mae_difference": abs(
            row["model_mae"] - reference["mae"]
        ),
        "rmse_difference": abs(
            row["model_rmse"] - reference["rmse"]
        ),
        "r2_difference": abs(
            row["model_r2"] - reference["r2"]
        )
    })

reproducibility = pd.DataFrame(
    reproducibility_rows
)

print("\nREPRODUCIBILITY CHECK")
display(reproducibility)


# ------------------------------------------------
# 12. SAVE FINAL RESULTS
# ------------------------------------------------

comparison.to_csv(
    OUTPUT_DIR / "independent_model_metrics.csv",
    index=False
)

reproducibility.to_csv(
    OUTPUT_DIR / "reproducibility_comparison.csv",
    index=False
)

np.save(
    OUTPUT_DIR / "independent_predictions_2024.npy",
    predictions
)

np.save(
    OUTPUT_DIR / "independent_actual_2024.npy",
    actual
)

verification_report = {
    "model": "GCN-GRU",
    "test_period": "2024",
    "evaluation_type": "Rolling one-step-ahead",
    "device": str(DEVICE),
    "prediction_shape": list(predictions.shape),
    "reproducibility": reproducibility.to_dict(
        orient="records"
    ),
    "all_features_beat_persistence": bool(
        (
            comparison["model_mae"]
            < comparison["persistence_mae"]
        ).all()
        and (
            comparison["model_rmse"]
            < comparison["persistence_rmse"]
        ).all()
    )
}

with open(
    OUTPUT_DIR / "verification_report.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(verification_report, f, indent=4)

print("\n" + "=" * 75)
print("CELL 27 COMPLETED")
print("=" * 75)

print("All features beat persistence:",
      verification_report["all_features_beat_persistence"])

print("\nSaved results to:")
print(OUTPUT_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 33
# Execution count: 40
# ============================================================

from pathlib import Path
import json

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

print("=" * 70)
print("SEARCHING FOR GCN-GRU MODEL DEFINITION")
print("=" * 70)

matches = []

for file in PROJECT_ROOT.rglob("*.py"):
    if any(part in {".venv", "venv", "__pycache__"} for part in file.parts):
        continue

    try:
        source = file.read_text(encoding="utf-8", errors="ignore")

        if "class GCNGRU" in source or "class GCN_GRU" in source:
            matches.append(file)
            print("\nFOUND:", file)
            for line_number, line in enumerate(source.splitlines(), 1):
                if "class GCN" in line or "def forward" in line:
                    print(f"  Line {line_number}: {line.strip()}")

    except Exception:
        pass

if not matches:
    print("\nNo GCNGRU class found in project Python files.")

config_path = (
    PROJECT_ROOT
    / "outputs"
    / "model_training"
    / "gcn_gru_config.json"
)

print("\n" + "=" * 70)
print("MODEL CONFIGURATION")
print("=" * 70)

if config_path.exists():
    print(json.dumps(
        json.loads(config_path.read_text(encoding="utf-8")),
        indent=4
    ))
else:
    print("Configuration file not found:", config_path)


# ============================================================
# ORIGINAL NOTEBOOK CELL 34
# Execution count: 41
# ============================================================

import torch
import inspect
from pathlib import Path

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

CHECKPOINT_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "model_training"
    / "best_gcn_gru_model.pth"
)

print("=" * 70)
print("CHECKING NOTEBOOK MODEL VARIABLES")
print("=" * 70)

for name, obj in list(globals().items()):
    if isinstance(obj, type):
        if "gcn" in name.lower() or "gru" in name.lower():
            print("\nMODEL CLASS VARIABLE:", name)
            print("Class:", obj)

            try:
                print(inspect.getsource(obj))
            except Exception as e:
                print("Source unavailable:", e)

    elif isinstance(obj, torch.nn.Module):
        print("\nMODEL INSTANCE VARIABLE:", name)
        print("Class:", type(obj))
        print("Parameter count:", sum(
            p.numel() for p in obj.parameters()
        ))

        try:
            print(inspect.getsource(type(obj)))
        except Exception as e:
            print("Source unavailable:", e)

print("\n" + "=" * 70)
print("CHECKPOINT PARAMETER NAMES")
print("=" * 70)

checkpoint = torch.load(
    CHECKPOINT_PATH,
    map_location="cpu",
    weights_only=False
)

if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
    state_dict = checkpoint["model_state_dict"]
elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
    state_dict = checkpoint["state_dict"]
else:
    state_dict = checkpoint

for key, value in state_dict.items():
    if torch.is_tensor(value):
        print(f"{key:45s} {tuple(value.shape)}")


# ============================================================
# ORIGINAL NOTEBOOK CELL 35
# Execution count: 43
# ============================================================


# ================================================================
# CELL 27: INDEPENDENT GCN-GRU MODEL VERIFICATION
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import json
import numpy as np
import pandas as pd
import torch

from pathlib import Path
from scipy.sparse import load_npz

# ================================================================
# 1. PROJECT PATHS
# ================================================================

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

TRAIN_DIR = PROJECT_ROOT / "outputs" / "model_training"
DATA_DIR = PROJECT_ROOT / "data" / "processed"
GRAPH_DIR = PROJECT_ROOT / "outputs" / "spatial_graph"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "independent_model_verification"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_PATH = TRAIN_DIR / "best_gcn_gru_model.pth"
SCALER_PATH = TRAIN_DIR / "scaler_metadata.json"

FEATURES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M"
]

print("=" * 75)
print("CELL 27: INDEPENDENT MODEL VERIFICATION")
print("=" * 75)

# ================================================================
# 2. CHECK REQUIRED FILES
# ================================================================

required_files = [
    TRAIN_DIR / "X_test_seq.npy",
    TRAIN_DIR / "y_test_seq.npy",
    CHECKPOINT_PATH,
    SCALER_PATH,
    GRAPH_DIR / "adjacency_matrix.npz",
    DATA_DIR / "spatial_nodes.csv"
]

for file in required_files:

    if not file.exists():
        raise FileNotFoundError(
            f"Required file missing: {file}"
        )

print("\nAll required files found.")

# ================================================================
# 3. LOAD TEST DATA
# ================================================================

X_test = np.load(
    TRAIN_DIR / "X_test_seq.npy"
)

y_test = np.load(
    TRAIN_DIR / "y_test_seq.npy"
)

print("\nTEST DATA")
print("-" * 75)

print("X_test shape:", X_test.shape)
print("y_test shape:", y_test.shape)

assert X_test.shape == (12, 12, 255, 4)
assert y_test.shape == (12, 255, 4)

assert np.isfinite(X_test).all()
assert np.isfinite(y_test).all()

# ================================================================
# 4. LOAD SCALER METADATA
# ================================================================

with open(
    SCALER_PATH,
    "r",
    encoding="utf-8"
) as f:

    scaler_metadata = json.load(f)


def find_scaler_values(data, keywords):

    if isinstance(data, dict):

        for key, value in data.items():

            key_lower = key.lower().replace("-", "_")

            if any(word in key_lower for word in keywords):

                try:

                    arr = np.asarray(
                        value,
                        dtype=np.float64
                    )

                    if arr.shape == (4,):
                        return arr

                except (ValueError, TypeError):
                    pass

        for value in data.values():

            result = find_scaler_values(
                value,
                keywords
            )

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:

            result = find_scaler_values(
                item,
                keywords
            )

            if result is not None:
                return result

    return None


scaler_mean = find_scaler_values(
    scaler_metadata,
    ["mean"]
)

scaler_std = find_scaler_values(
    scaler_metadata,
    ["std", "scale"]
)

if scaler_mean is None or scaler_std is None:

    raise ValueError(
        "Could not identify scaler mean and standard deviation.\n"
        f"Metadata keys: {list(scaler_metadata.keys())}"
    )

if np.any(scaler_std <= 0):

    raise ValueError(
        "Scaler standard deviation contains invalid values."
    )

print("\nSCALER INFORMATION")
print("-" * 75)

print("Features:", FEATURES)
print("Mean:", scaler_mean)
print("Standard deviation:", scaler_std)

# ================================================================
# 5. REUSE ORIGINAL CELL 12 MODEL
# ================================================================

if "GCNGRU" not in globals() or "model" not in globals():

    raise RuntimeError(
        "Original GCNGRU class/model not found.\n"
        "Execute Cell 12 before running Cell 27."
    )

model = globals()["model"]

parameter_count = sum(
    parameter.numel()
    for parameter in model.parameters()
)

print("\nORIGINAL MODEL")
print("-" * 75)

print("Model class:", type(model).__name__)
print("Total parameters:", parameter_count)

assert parameter_count == 20292, (
    f"Unexpected parameter count: {parameter_count}"
)

# ================================================================
# 6. LOAD SPATIAL ADJACENCY MATRIX
# ================================================================

adjacency_sparse = load_npz(
    GRAPH_DIR / "adjacency_matrix.npz"
)

adjacency = adjacency_sparse.toarray().astype(
    np.float32
)

assert adjacency.shape == (255, 255)

assert np.allclose(
    adjacency,
    adjacency.T,
    atol=1e-6
)

device = next(model.parameters()).device

adjacency_tensor = torch.tensor(
    adjacency,
    dtype=torch.float32,
    device=device
)

X_tensor = torch.tensor(
    X_test,
    dtype=torch.float32,
    device=device
)

print("\nGRAPH AND DEVICE")
print("-" * 75)

print("Adjacency shape:", adjacency_tensor.shape)
print("Device:", device)

# ================================================================
# 7. LOAD TRAINED CHECKPOINT
# ================================================================

checkpoint = torch.load(
    CHECKPOINT_PATH,
    map_location=device,
    weights_only=False
)

if (
    isinstance(checkpoint, dict)
    and "model_state_dict" in checkpoint
):

    state_dict = checkpoint["model_state_dict"]

elif (
    isinstance(checkpoint, dict)
    and "state_dict" in checkpoint
):

    state_dict = checkpoint["state_dict"]

else:

    state_dict = checkpoint


# Handle DataParallel checkpoint prefixes.

if all(
    key.startswith("module.")
    for key in state_dict.keys()
):

    state_dict = {
        key.replace("module.", "", 1): value
        for key, value in state_dict.items()
    }


model.load_state_dict(
    state_dict,
    strict=True
)

model.to(device)
model.eval()

print("\nCHECKPOINT")
print("-" * 75)

print("Checkpoint:", CHECKPOINT_PATH)
print("Strict checkpoint loading: SUCCESS")
print("Model evaluation mode:", not model.training)

# ================================================================
# 8. INDEPENDENT MODEL INFERENCE
# ================================================================

print("\nRUNNING MODEL INFERENCE")
print("-" * 75)

with torch.no_grad():

    predictions_normalized = model(
        X_tensor,
        adjacency_tensor
    )

    if isinstance(
        predictions_normalized,
        (tuple, list)
    ):

        predictions_normalized = (
            predictions_normalized[0]
        )

    predictions_normalized = (
        predictions_normalized
        .detach()
        .cpu()
        .numpy()
    )


assert predictions_normalized.shape == y_test.shape

print(
    "Normalized prediction shape:",
    predictions_normalized.shape
)

# ================================================================
# 9. INVERSE NORMALIZATION
# ================================================================

predictions_physical = (
    predictions_normalized * scaler_std
    + scaler_mean
)

actual_physical = (
    y_test * scaler_std
    + scaler_mean
)

# Persistence baseline:
# Last observed month in each input sequence.

persistence_normalized = X_test[:, -1, :, :]

persistence_physical = (
    persistence_normalized * scaler_std
    + scaler_mean
)

assert predictions_physical.shape == (12, 255, 4)
assert actual_physical.shape == (12, 255, 4)
assert persistence_physical.shape == (12, 255, 4)

assert np.isfinite(predictions_physical).all()
assert np.isfinite(actual_physical).all()
assert np.isfinite(persistence_physical).all()

print("\nPHYSICAL DATA")
print("-" * 75)

print("Predictions:", predictions_physical.shape)
print("Actual:", actual_physical.shape)
print("Persistence:", persistence_physical.shape)

# ================================================================
# 10. METRIC FUNCTIONS
# ================================================================

def calculate_metrics(actual, predicted):

    actual = np.asarray(actual).reshape(-1)
    predicted = np.asarray(predicted).reshape(-1)

    error = actual - predicted

    mae = np.mean(np.abs(error))

    rmse = np.sqrt(
        np.mean(error ** 2)
    )

    ss_res = np.sum(error ** 2)

    ss_tot = np.sum(
        (actual - np.mean(actual)) ** 2
    )

    r2 = (
        1 - ss_res / ss_tot
        if ss_tot > 0
        else np.nan
    )

    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "R2": float(r2)
    }


# ================================================================
# 11. MODEL VS PERSISTENCE METRICS
# ================================================================

metric_rows = []

for feature_index, feature in enumerate(FEATURES):

    actual = actual_physical[
        :, :, feature_index
    ]

    predicted = predictions_physical[
        :, :, feature_index
    ]

    persistence = persistence_physical[
        :, :, feature_index
    ]

    model_metrics = calculate_metrics(
        actual,
        predicted
    )

    baseline_metrics = calculate_metrics(
        actual,
        persistence
    )

    mae_improvement = (
        (
            baseline_metrics["MAE"]
            - model_metrics["MAE"]
        )
        / baseline_metrics["MAE"]
        * 100
        if baseline_metrics["MAE"] > 0
        else np.nan
    )

    rmse_improvement = (
        (
            baseline_metrics["RMSE"]
            - model_metrics["RMSE"]
        )
        / baseline_metrics["RMSE"]
        * 100
        if baseline_metrics["RMSE"] > 0
        else np.nan
    )

    metric_rows.append({

        "feature": feature,

        "model_MAE": model_metrics["MAE"],
        "model_RMSE": model_metrics["RMSE"],
        "model_R2": model_metrics["R2"],

        "persistence_MAE": baseline_metrics["MAE"],
        "persistence_RMSE": baseline_metrics["RMSE"],
        "persistence_R2": baseline_metrics["R2"],

        "MAE_improvement_percent": mae_improvement,
        "RMSE_improvement_percent": rmse_improvement
    })


metrics_df = pd.DataFrame(metric_rows)

metrics_df.to_csv(
    OUTPUT_DIR / "independent_model_metrics.csv",
    index=False
)

print("\n" + "=" * 75)
print("INDEPENDENT MODEL EVALUATION")
print("=" * 75)

print(
    metrics_df.round(5).to_string(index=False)
)

# ================================================================
# 12. COMPARE AGAINST CELL 15 REFERENCE METRICS
# ================================================================

reference_metrics = {

    "T2M": {
        "MAE": 1.5412,
        "RMSE": 2.2789,
        "R2": 0.9714
    },

    "PRECTOTCORR": {
        "MAE": 1.3726,
        "RMSE": 2.5789,
        "R2": 0.7317
    },

    "RH2M": {
        "MAE": 4.0046,
        "RMSE": 5.6396,
        "R2": 0.9052
    },

    "WS10M": {
        "MAE": 0.5185,
        "RMSE": 0.7100,
        "R2": 0.8248
    }
}

comparison_rows = []

for _, row in metrics_df.iterrows():

    feature = row["feature"]

    reference = reference_metrics[feature]

    comparison_rows.append({

        "feature": feature,

        "recomputed_MAE": row["model_MAE"],
        "reference_MAE": reference["MAE"],

        "recomputed_RMSE": row["model_RMSE"],
        "reference_RMSE": reference["RMSE"],

        "recomputed_R2": row["model_R2"],
        "reference_R2": reference["R2"],

        "MAE_absolute_difference": abs(
            row["model_MAE"] - reference["MAE"]
        ),

        "RMSE_absolute_difference": abs(
            row["model_RMSE"] - reference["RMSE"]
        ),

        "R2_absolute_difference": abs(
            row["model_R2"] - reference["R2"]
        )
    })


comparison_df = pd.DataFrame(comparison_rows)

comparison_df.to_csv(
    OUTPUT_DIR / "cell15_metric_comparison.csv",
    index=False
)

print("\n" + "=" * 75)
print("CELL 15 VS CELL 27 METRIC COMPARISON")
print("=" * 75)

print(
    comparison_df.round(6).to_string(index=False)
)

# ================================================================
# 13. MONTHLY ERROR ANALYSIS
# ================================================================

monthly_rows = []

month_names = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]

for month_index in range(12):

    for feature_index, feature in enumerate(FEATURES):

        actual = actual_physical[
            month_index, :, feature_index
        ]

        predicted = predictions_physical[
            month_index, :, feature_index
        ]

        persistence = persistence_physical[
            month_index, :, feature_index
        ]

        model_metrics = calculate_metrics(
            actual,
            predicted
        )

        baseline_metrics = calculate_metrics(
            actual,
            persistence
        )

        monthly_rows.append({

            "month_index": month_index + 1,
            "month": month_names[month_index],
            "feature": feature,

            "model_MAE": model_metrics["MAE"],
            "model_RMSE": model_metrics["RMSE"],

            "persistence_MAE": baseline_metrics["MAE"],
            "persistence_RMSE": baseline_metrics["RMSE"]
        })


monthly_df = pd.DataFrame(monthly_rows)

monthly_df.to_csv(
    OUTPUT_DIR / "monthly_error_analysis.csv",
    index=False
)

print("\nMONTHLY ERROR ANALYSIS")
print("-" * 75)

print(
    monthly_df.round(4).to_string(index=False)
)

# ================================================================
# 14. SPATIAL NODE-WISE ERROR ANALYSIS
# ================================================================

nodes_df = pd.read_csv(
    DATA_DIR / "spatial_nodes.csv"
)

assert len(nodes_df) == 255

spatial_rows = []

for node_index in range(255):

    for feature_index, feature in enumerate(FEATURES):

        actual = actual_physical[
            :, node_index, feature_index
        ]

        predicted = predictions_physical[
            :, node_index, feature_index
        ]

        persistence = persistence_physical[
            :, node_index, feature_index
        ]

        model_metrics = calculate_metrics(
            actual,
            predicted
        )

        baseline_metrics = calculate_metrics(
            actual,
            persistence
        )

        spatial_rows.append({

            "node_id": int(
                nodes_df.iloc[node_index]["node_id"]
            ),

            "grid_latitude": float(
                nodes_df.iloc[node_index]["grid_latitude"]
            ),

            "grid_longitude": float(
                nodes_df.iloc[node_index]["grid_longitude"]
            ),

            "feature": feature,

            "model_MAE": model_metrics["MAE"],
            "model_RMSE": model_metrics["RMSE"],

            "persistence_MAE": baseline_metrics["MAE"],
            "persistence_RMSE": baseline_metrics["RMSE"]
        })


spatial_df = pd.DataFrame(spatial_rows)

spatial_df.to_csv(
    OUTPUT_DIR / "spatial_node_error_analysis.csv",
    index=False
)

print("\nSPATIAL ERROR ANALYSIS")
print("-" * 75)

for feature in FEATURES:

    feature_data = spatial_df[
        spatial_df["feature"] == feature
    ]

    print(
        f"{feature}: "
        f"Mean node MAE = "
        f"{feature_data['model_MAE'].mean():.5f}, "
        f"Median node MAE = "
        f"{feature_data['model_MAE'].median():.5f}"
    )

# ================================================================
# 15. BEST AND WORST SPATIAL NODES
# ================================================================

spatial_ranking = []

for feature in FEATURES:

    feature_data = spatial_df[
        spatial_df["feature"] == feature
    ].sort_values("model_MAE")

    best = feature_data.iloc[0]

    worst = feature_data.iloc[-1]

    spatial_ranking.append({

        "feature": feature,

        "best_node": int(best["node_id"]),
        "best_latitude": float(best["grid_latitude"]),
        "best_longitude": float(best["grid_longitude"]),
        "best_MAE": float(best["model_MAE"]),

        "worst_node": int(worst["node_id"]),
        "worst_latitude": float(worst["grid_latitude"]),
        "worst_longitude": float(worst["grid_longitude"]),
        "worst_MAE": float(worst["model_MAE"])
    })


spatial_ranking_df = pd.DataFrame(
    spatial_ranking
)

spatial_ranking_df.to_csv(
    OUTPUT_DIR / "best_worst_spatial_nodes.csv",
    index=False
)

print("\nBEST AND WORST SPATIAL NODES")
print("-" * 75)

print(
    spatial_ranking_df.round(5).to_string(index=False)
)

# ================================================================
# 16. SAVE PREDICTIONS AND ACTUAL VALUES
# ================================================================

np.save(
    OUTPUT_DIR / "independent_predictions_normalized.npy",
    predictions_normalized
)

np.save(
    OUTPUT_DIR / "independent_predictions_physical.npy",
    predictions_physical
)

np.save(
    OUTPUT_DIR / "actual_test_physical.npy",
    actual_physical
)

np.save(
    OUTPUT_DIR / "persistence_predictions_physical.npy",
    persistence_physical
)

# ================================================================
# 17. VERIFICATION CHECKLIST
# ================================================================

checks = {

    "test_input_shape_valid":
        X_test.shape == (12, 12, 255, 4),

    "test_target_shape_valid":
        y_test.shape == (12, 255, 4),

    "model_parameter_count_valid":
        parameter_count == 20292,

    "checkpoint_loaded_strictly":
        True,

    "adjacency_shape_valid":
        adjacency.shape == (255, 255),

    "adjacency_symmetric":
        np.allclose(
            adjacency,
            adjacency.T,
            atol=1e-6
        ),

    "prediction_shape_valid":
        predictions_physical.shape == (12, 255, 4),

    "predictions_finite":
        np.isfinite(predictions_physical).all(),

    "actual_values_finite":
        np.isfinite(actual_physical).all(),

    "persistence_values_finite":
        np.isfinite(persistence_physical).all(),

    "metrics_available":
        len(metrics_df) == 4
}

print("\n" + "=" * 75)
print("INDEPENDENT VERIFICATION CHECKLIST")
print("=" * 75)

for name, passed in checks.items():

    status = (
        "PASS"
        if bool(passed)
        else "FAIL"
    )

    print(
        f"{name:40s}: {status}"
    )

# ================================================================
# 18. JSON SERIALIZATION HELPER
# ================================================================

def make_json_serializable(obj):

    if isinstance(obj, dict):

        return {
            str(key): make_json_serializable(value)
            for key, value in obj.items()
        }

    if isinstance(obj, (list, tuple)):

        return [
            make_json_serializable(value)
            for value in obj
        ]

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    if isinstance(obj, torch.Tensor):

        return obj.detach().cpu().tolist()

    return obj


# ================================================================
# 19. SAVE INDEPENDENT VERIFICATION REPORT
# ================================================================

verification_report = {

    "project": "NASA Earth Systems Trend Detective",

    "verification_type":
        "Independent GCN-GRU test evaluation",

    "model_architecture": "GCN-GRU",

    "parameter_count": int(parameter_count),

    "device": str(device),

    "test_input_shape": list(X_test.shape),

    "test_target_shape": list(y_test.shape),

    "prediction_shape": list(
        predictions_physical.shape
    ),

    "features": FEATURES,

    "test_period": "January 2024 - December 2024",

    "evaluation_method": (
        "Rolling one-step-ahead evaluation using "
        "the observed preceding 12 months"
    ),

    "metrics": metrics_df.to_dict(
        orient="records"
    ),

    "cell15_comparison": comparison_df.to_dict(
        orient="records"
    ),

    "verification_checks": checks,

    "all_checks_passed": all(
        bool(value)
        for value in checks.values()
    ),

    "limitations": [

        "Test evaluation covers only 12 months in 2024.",

        "Evaluation is rolling one-step-ahead, "
        "not free-running.",

        "The spatial graph represents geographic proximity.",

        "The model does not establish causal climate relationships.",

        "Results are based on NASA POWER meteorological variables."
    ]
}

verification_report = make_json_serializable(
    verification_report
)

report_path = (
    OUTPUT_DIR
    / "independent_verification_report.json"
)

with open(
    report_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        verification_report,
        f,
        indent=4,
        allow_nan=False
    )

print("\nJSON report saved:", report_path)

# ================================================================
# 20. FINAL SUMMARY
# ================================================================

print("\n" + "=" * 75)
print("CELL 27 COMPLETED")
print("=" * 75)

print("Model:", type(model).__name__)
print("Parameters:", parameter_count)
print("Device:", device)

print("Test samples:", X_test.shape[0])
print("Spatial nodes:", X_test.shape[2])
print("Features:", len(FEATURES))

beats_persistence = bool(
    (
        metrics_df["MAE_improvement_percent"] > 0
    ).all()
)

print(
    "Model beats persistence for all features:",
    beats_persistence
)

print("\nVERIFICATION CHECKLIST")

for name, passed in checks.items():

    print(
        f"{name:40s}: "
        f"{'PASS' if bool(passed) else 'FAIL'}"
    )

print("\nSAVED OUTPUTS")

for file in sorted(OUTPUT_DIR.iterdir()):

    print(file.name)

print("\nOutput directory:")
print(OUTPUT_DIR)

print("\nIndependent verification completed.")


# ============================================================
# ORIGINAL NOTEBOOK CELL 36
# Execution count: 44
# ============================================================


# ================================================================
# CELL 27A: INVESTIGATE CELL 15 VS CELL 27 DISCREPANCY
# ================================================================

import numpy as np
import torch
from scipy.sparse import load_npz
from pathlib import Path

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

GRAPH_DIR = PROJECT_ROOT / "outputs" / "spatial_graph"

raw_adjacency = load_npz(
    GRAPH_DIR / "adjacency_matrix.npz"
).toarray().astype(np.float32)

print("=" * 75)
print("1. RAW ADJACENCY MATRIX")
print("=" * 75)

print("Shape:", raw_adjacency.shape)
print("Minimum:", raw_adjacency.min())
print("Maximum:", raw_adjacency.max())
print("Mean:", raw_adjacency.mean())
print("Diagonal mean:", np.diag(raw_adjacency).mean())
print("Symmetric:", np.allclose(raw_adjacency, raw_adjacency.T))

print("\n" + "=" * 75)
print("2. SEARCHING NOTEBOOK VARIABLES")
print("=" * 75)

candidate_matrices = []

for name, obj in list(globals().items()):

    if any(term in name.lower() for term in [
        "adj", "graph", "norm"
    ]):

        try:

            if isinstance(obj, torch.Tensor):

                arr = obj.detach().cpu().numpy()

            elif isinstance(obj, np.ndarray):

                arr = obj

            elif hasattr(obj, "toarray"):

                arr = obj.toarray()

            else:
                continue

            if arr.shape == (255, 255):

                print("\nVariable:", name)
                print("Shape:", arr.shape)
                print("Minimum:", np.nanmin(arr))
                print("Maximum:", np.nanmax(arr))
                print("Mean:", np.nanmean(arr))
                print(
                    "Diagonal mean:",
                    np.diag(arr).mean()
                )
                print(
                    "Symmetric:",
                    np.allclose(arr, arr.T, atol=1e-6)
                )
                print(
                    "Equal to raw adjacency:",
                    np.allclose(arr, raw_adjacency, atol=1e-6)
                )

                candidate_matrices.append(name)

        except Exception:
            pass


print("\n" + "=" * 75)
print("3. SEARCHING PREVIOUS NOTEBOOK CELLS")
print("=" * 75)

try:

    history = get_ipython().user_ns.get("In", [])

    for cell_index, source in enumerate(history):

        lines = source.splitlines()

        matching_lines = [
            (line_number, line.strip())
            for line_number, line in enumerate(lines, 1)
            if any(term in line.lower() for term in [
                "adjacency",
                "normalized_adj",
                "normalize_adj",
                "model(",
                "predictions =",
                "load_state_dict"
            ])
        ]

        if matching_lines:

            print(f"\nNOTEBOOK CELL In[{cell_index}]")

            for line_number, line in matching_lines:

                print(f"  {line_number}: {line[:220]}")

except Exception as e:

    print("Notebook history inspection failed:", e)


print("\n" + "=" * 75)
print("4. CURRENT MODEL STATUS")
print("=" * 75)

print("Model:", type(model).__name__)
print("Parameters:", sum(
    p.numel() for p in model.parameters()
))
print("Device:", next(model.parameters()).device)

print("\nCandidate adjacency variables:", candidate_matrices)

print("\nDiagnostic completed.")


# ============================================================
# ORIGINAL NOTEBOOK CELL 37
# Execution count: 45
# ============================================================

# ================================================================
# CELL 27B: VERIFY ADJACENCY NORMALIZATION AND MODEL CALLS
# ================================================================

import numpy as np

print("=" * 75)
print("1. NORMALIZED ADJACENCY")
print("=" * 75)

if "normalized_adjacency" in globals():
    norm_adj = normalized_adjacency

    if hasattr(norm_adj, "detach"):
        norm_adj = norm_adj.detach().cpu().numpy()
    elif hasattr(norm_adj, "toarray"):
        norm_adj = norm_adj.toarray()

    norm_adj = np.asarray(norm_adj)

    print("Shape:", norm_adj.shape)
    print("Minimum:", float(norm_adj.min()))
    print("Maximum:", float(norm_adj.max()))
    print("Mean:", float(norm_adj.mean()))
    print("Diagonal mean:", float(np.diag(norm_adj).mean()))
    print("Symmetric:", np.allclose(norm_adj, norm_adj.T))
    print("Equal to raw:", np.allclose(norm_adj, adjacency))

    print("\nFirst 5x5 normalized adjacency:")
    print(np.round(norm_adj[:5, :5], 5))
else:
    print("normalized_adjacency not found.")

print("\n" + "=" * 75)
print("2. NOTEBOOK HISTORY: TRAINING AND EVALUATION")
print("=" * 75)

keywords = [
    "normalized_adjacency",
    "ADJACENCY_TENSOR",
    "adjacency_tensor",
    "model(",
    "model.forward",
    "best_gcn_gru_model",
    "load_state_dict",
    "y_pred",
    "predictions"
]

for i, source in enumerate(In):
    if any(word in source for word in keywords):
        relevant_lines = [
            line.strip()
            for line in source.splitlines()
            if any(word in line for word in keywords)
        ]

        if relevant_lines:
            print(f"\n--- Notebook cell In[{i}] ---")
            for line in relevant_lines[:15]:
                print(line[:250])

print("\n" + "=" * 75)
print("3. ADJACENCY-RELATED GLOBAL VARIABLES")
print("=" * 75)

for name in [
    "normalized_adjacency",
    "ADJACENCY_TENSOR",
    "adjacency_tensor",
    "adjacency_sparse"
]:
    if name in globals():
        value = globals()[name]
        print(
            name,
            "| type:", type(value),
            "| shape:", getattr(value, "shape", "not available")
        )

print("\nDiagnostic completed.")


# ============================================================
# ORIGINAL NOTEBOOK CELL 38
# Execution count: 46
# ============================================================

# ================================================================
# CELL 27C: CORRECTED INDEPENDENT MODEL VERIFICATION
# NASA EARTH SYSTEMS TREND DETECTIVE
# Uses the SAME normalized adjacency as original training
# ================================================================

import json
import numpy as np
import pandas as pd
import torch

from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ------------------------------------------------
# 1. PATHS AND CONFIGURATION
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

TRAIN_DIR = PROJECT_ROOT / "outputs" / "model_training"

CHECKPOINT_PATH = TRAIN_DIR / "best_gcn_gru_model.pth"
X_TEST_PATH = TRAIN_DIR / "X_test_seq.npy"
Y_TEST_PATH = TRAIN_DIR / "y_test_seq.npy"
SCALER_PATH = TRAIN_DIR / "scaler_metadata.json"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "independent_model_verification_corrected"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = ["T2M", "PRECTOTCORR", "RH2M", "WS10M"]

UNITS = {
    "T2M": "°C",
    "PRECTOTCORR": "mm/day",
    "RH2M": "%",
    "WS10M": "m/s"
}

# ------------------------------------------------
# 2. VALIDATE NOTEBOOK MODEL AND NORMALIZED GRAPH
# ------------------------------------------------

assert "model" in globals(), "Run the model-definition cell first."
assert "ADJACENCY_TENSOR" in globals(), "Original normalized adjacency missing."

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

model = globals()["model"].to(device)

adjacency_tensor = ADJACENCY_TENSOR.to(
    device=device,
    dtype=torch.float32
)

assert adjacency_tensor.shape == (255, 255)

print("=" * 75)
print("CORRECTED MODEL VERIFICATION")
print("=" * 75)

print("Device:", device)
print("Model:", model.__class__.__name__)
print("Parameters:", sum(p.numel() for p in model.parameters()))

print("\nNormalized adjacency:")
print("Shape:", tuple(adjacency_tensor.shape))
print("Maximum:", adjacency_tensor.max().item())
print("Mean:", adjacency_tensor.mean().item())

# ------------------------------------------------
# 3. LOAD TEST DATA
# ------------------------------------------------

X_test = np.load(X_TEST_PATH).astype(np.float32)
y_test = np.load(Y_TEST_PATH).astype(np.float32)

print("\nTest input shape:", X_test.shape)
print("Test target shape:", y_test.shape)

assert X_test.shape == (12, 12, 255, 4)
assert y_test.shape == (12, 255, 4)

# ------------------------------------------------
# 4. LOAD SCALER
# ------------------------------------------------

with open(SCALER_PATH, "r", encoding="utf-8") as f:
    scaler_data = json.load(f)

scaler_mean = np.array(
    [19.03649712, 3.18354273, 63.72987366, 3.98562574],
    dtype=np.float32
)

scaler_std = np.array(
    [13.48452568, 4.81103802, 19.04921341, 1.66794741],
    dtype=np.float32
)

print("\nScaler values:")
print("Mean:", scaler_mean)
print("Std:", scaler_std)

# ------------------------------------------------
# 5. LOAD BEST CHECKPOINT STRICTLY
# ------------------------------------------------

checkpoint = torch.load(
    CHECKPOINT_PATH,
    map_location=device,
    weights_only=False
)

if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
    state_dict = checkpoint["model_state_dict"]

elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
    state_dict = checkpoint["state_dict"]

else:
    state_dict = checkpoint

model.load_state_dict(state_dict, strict=True)
model.eval()

print("\nStrict checkpoint loading: SUCCESS")

# ------------------------------------------------
# 6. RUN MODEL WITH NORMALIZED ADJACENCY
# ------------------------------------------------

X_tensor = torch.tensor(
    X_test,
    dtype=torch.float32,
    device=device
)

with torch.no_grad():
    predictions_normalized = model(
        X_tensor,
        adjacency_tensor
    )

if isinstance(predictions_normalized, (tuple, list)):
    predictions_normalized = predictions_normalized[0]

predictions_normalized = (
    predictions_normalized.detach().cpu().numpy()
)

assert predictions_normalized.shape == y_test.shape

print("\nNormalized prediction shape:", predictions_normalized.shape)

# ------------------------------------------------
# 7. CONVERT TO PHYSICAL UNITS
# ------------------------------------------------

predictions_physical = (
    predictions_normalized * scaler_std.reshape(1, 1, -1)
    + scaler_mean.reshape(1, 1, -1)
)

actual_physical = (
    y_test * scaler_std.reshape(1, 1, -1)
    + scaler_mean.reshape(1, 1, -1)
)

# Persistence: last observed month in each test input
persistence_normalized = X_test[:, -1, :, :]

persistence_physical = (
    persistence_normalized * scaler_std.reshape(1, 1, -1)
    + scaler_mean.reshape(1, 1, -1)
)

assert np.isfinite(predictions_physical).all()
assert np.isfinite(actual_physical).all()

# ------------------------------------------------
# 8. CALCULATE METRICS
# ------------------------------------------------

results = []

for i, feature in enumerate(FEATURES):

    y_true = actual_physical[:, :, i].reshape(-1)

    y_model = predictions_physical[:, :, i].reshape(-1)

    y_persistence = persistence_physical[:, :, i].reshape(-1)

    model_mae = mean_absolute_error(y_true, y_model)
    model_rmse = np.sqrt(mean_squared_error(y_true, y_model))
    model_r2 = r2_score(y_true, y_model)

    persistence_mae = mean_absolute_error(
        y_true, y_persistence
    )

    persistence_rmse = np.sqrt(
        mean_squared_error(y_true, y_persistence)
    )

    persistence_r2 = r2_score(
        y_true, y_persistence
    )

    mae_improvement = (
        (persistence_mae - model_mae)
        / persistence_mae
    ) * 100

    rmse_improvement = (
        (persistence_rmse - model_rmse)
        / persistence_rmse
    ) * 100

    results.append({
        "Feature": feature,
        "Unit": UNITS[feature],
        "Model_MAE": model_mae,
        "Model_RMSE": model_rmse,
        "Model_R2": model_r2,
        "Persistence_MAE": persistence_mae,
        "Persistence_RMSE": persistence_rmse,
        "Persistence_R2": persistence_r2,
        "MAE_Improvement_Percent": mae_improvement,
        "RMSE_Improvement_Percent": rmse_improvement,
        "Model_Beats_Persistence": model_mae < persistence_mae
    })

metrics_df = pd.DataFrame(results)

print("\n" + "=" * 75)
print("CORRECTED TEST METRICS")
print("=" * 75)

print(metrics_df.round(5).to_string(index=False))

# ------------------------------------------------
# 9. COMPARE AGAINST ORIGINAL CELL 15
# ------------------------------------------------

original_cell15 = {
    "T2M": [1.5412, 2.2789, 0.9714],
    "PRECTOTCORR": [1.3726, 2.5789, 0.7317],
    "RH2M": [4.0046, 5.6396, 0.9052],
    "WS10M": [0.5185, 0.7100, 0.8248]
}

print("\n" + "=" * 75)
print("COMPARISON WITH ORIGINAL CELL 15")
print("=" * 75)

for _, row in metrics_df.iterrows():

    feature = row["Feature"]
    old = original_cell15[feature]

    print(f"\n{feature}")
    print(
        f"Cell 15 MAE: {old[0]:.4f} | "
        f"Corrected MAE: {row['Model_MAE']:.4f}"
    )
    print(
        f"Cell 15 RMSE: {old[1]:.4f} | "
        f"Corrected RMSE: {row['Model_RMSE']:.4f}"
    )
    print(
        f"Cell 15 R2: {old[2]:.4f} | "
        f"Corrected R2: {row['Model_R2']:.4f}"
    )

# ------------------------------------------------
# 10. SAVE VERIFICATION OUTPUTS
# ------------------------------------------------

metrics_df.to_csv(
    OUTPUT_DIR / "corrected_test_metrics.csv",
    index=False
)

np.save(
    OUTPUT_DIR / "corrected_predictions_normalized.npy",
    predictions_normalized
)

np.save(
    OUTPUT_DIR / "corrected_predictions_physical.npy",
    predictions_physical
)

np.save(
    OUTPUT_DIR / "actual_test_physical.npy",
    actual_physical
)

np.save(
    OUTPUT_DIR / "persistence_predictions_physical.npy",
    persistence_physical
)

summary = {
    "model": "GCN-GRU",
    "evaluation": "2024 rolling one-step-ahead test",
    "graph_input": "Original normalized adjacency tensor",
    "checkpoint": str(CHECKPOINT_PATH),
    "test_input_shape": list(X_test.shape),
    "test_target_shape": list(y_test.shape),
    "prediction_shape": list(predictions_physical.shape),
    "all_predictions_finite": bool(
        np.isfinite(predictions_physical).all()
    ),
    "model_beats_persistence_all_features": bool(
        metrics_df["Model_Beats_Persistence"].all()
    ),
    "metrics": metrics_df.to_dict(orient="records")
}

with open(
    OUTPUT_DIR / "corrected_verification_report.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(summary, f, indent=4)

print("\n" + "=" * 75)
print("FINAL VERIFICATION")
print("=" * 75)

print(
    "Model beats persistence on all features:",
    metrics_df["Model_Beats_Persistence"].all()
)

print("Finite predictions:", np.isfinite(predictions_physical).all())

print("\nSaved outputs:")
print(OUTPUT_DIR)

print("\nCell 27C completed.")


# ============================================================
# ORIGINAL NOTEBOOK CELL 39
# Execution count: 48
# ============================================================


# ================================================================
# CELL 28: INDEPENDENT 2025 FORECAST VERIFICATION
# CORRECTED FOR 3D GCN-GRU OUTPUT
# ================================================================

import json
import numpy as np
import pandas as pd
import torch

from pathlib import Path

# ------------------------------------------------
# 1. PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

TRAIN_DIR = PROJECT_ROOT / "outputs" / "model_training"
FORECAST_DIR = PROJECT_ROOT / "outputs" / "future_forecasting"
GRAPH_DIR = PROJECT_ROOT / "outputs" / "spatial_graph"

CHECKPOINT_PATH = TRAIN_DIR / "best_gcn_gru_model.pth"
TENSOR_PATH = PROJECT_ROOT / "data" / "processed" / "nasa_power_tensor.npy"
SCALER_PATH = TRAIN_DIR / "scaler_metadata.json"

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "forecast_verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

FEATURES = ["T2M", "PRECTOTCORR", "RH2M", "WS10M"]

print("=" * 75)
print("INDEPENDENT 2025 FORECAST VERIFICATION")
print("=" * 75)

# ------------------------------------------------
# 2. LOAD MODEL
# ------------------------------------------------

assert "GCNGRU" in globals(), "Run the model definition cell first."

model = GCNGRU(
    input_features=4,
    gcn_hidden=32,
    gru_hidden=64,
    output_features=4,
    dropout=0.15
).to(DEVICE)

checkpoint = torch.load(
    CHECKPOINT_PATH,
    map_location=DEVICE,
    weights_only=False
)

state_dict = checkpoint.get("model_state_dict", checkpoint)

model.load_state_dict(state_dict, strict=True)
model.eval()

print("Model:", model.__class__.__name__)
print("Parameters:", sum(p.numel() for p in model.parameters()))
print("Device:", DEVICE)
print("Checkpoint loading: SUCCESS")

# ------------------------------------------------
# 3. LOAD HISTORICAL DATA AND SCALER
# ------------------------------------------------

historical = np.load(TENSOR_PATH).astype(np.float32)

with open(SCALER_PATH, "r") as f:
    scaler = json.load(f)

scaler_mean = np.asarray(scaler["mean"], dtype=np.float32)
scaler_std = np.asarray(scaler["std"], dtype=np.float32)

assert historical.shape == (120, 255, 4)
assert np.isfinite(historical).all()
assert np.all(scaler_std > 0)

print("\nHistorical tensor:", historical.shape)
print("Scaler mean:", scaler_mean)
print("Scaler std:", scaler_std)

# ------------------------------------------------
# 4. LOAD NORMALIZED ADJACENCY
# ------------------------------------------------

assert "normalized_adjacency" in globals()

normalized_adj = np.asarray(
    normalized_adjacency,
    dtype=np.float32
)

assert normalized_adj.shape == (255, 255)
assert np.isfinite(normalized_adj).all()
assert np.allclose(normalized_adj, normalized_adj.T)

adjacency_tensor = torch.tensor(
    normalized_adj,
    dtype=torch.float32,
    device=DEVICE
)

print("\nNormalized adjacency:", normalized_adj.shape)

# ------------------------------------------------
# 5. PREPARE FINAL 12 MONTHS OF 2024
# ------------------------------------------------

historical_normalized = (
    historical - scaler_mean.reshape(1, 1, 4)
) / scaler_std.reshape(1, 1, 4)

rolling_input = torch.tensor(
    historical_normalized[-12:],
    dtype=torch.float32,
    device=DEVICE
).unsqueeze(0)

assert rolling_input.shape == (1, 12, 255, 4)

print("\nInitial input shape:", tuple(rolling_input.shape))

# ------------------------------------------------
# 6. CHECK MODEL OUTPUT DIMENSIONS
# ------------------------------------------------

with torch.no_grad():
    sample_output = model(
        rolling_input,
        adjacency_tensor
    )

if isinstance(sample_output, (tuple, list)):
    sample_output = sample_output[0]

print("Model output shape:", tuple(sample_output.shape))

assert sample_output.ndim == 3, (
    "Unexpected model output dimensions. "
    "Expected (batch, nodes, features)."
)

assert sample_output.shape == (1, 255, 4)

# ------------------------------------------------
# 7. AUTOREGRESSIVE FORECAST
# ------------------------------------------------

forecast_normalized = []

with torch.no_grad():

    for month in range(12):

        output = model(
            rolling_input,
            adjacency_tensor
        )

        if isinstance(output, (tuple, list)):
            output = output[0]

        assert output.shape == (1, 255, 4)

        # Model output: (1, 255, 4)
        # Convert to: (1, 1, 255, 4)
        next_prediction = output.unsqueeze(1)

        forecast_normalized.append(
            output.squeeze(0).cpu().numpy()
        )

        # Remove oldest month and append predicted month
        rolling_input = torch.cat(
            [
                rolling_input[:, 1:, :, :],
                next_prediction
            ],
            dim=1
        )

        print(f"Forecast month {month + 1}/12 completed.")

forecast_normalized = np.stack(
    forecast_normalized,
    axis=0
)

# ------------------------------------------------
# 8. INVERSE NORMALIZATION
# ------------------------------------------------

forecast_physical = (
    forecast_normalized *
    scaler_std.reshape(1, 1, 4)
    +
    scaler_mean.reshape(1, 1, 4)
)

print("\nNormalized forecast:", forecast_normalized.shape)
print("Physical forecast:", forecast_physical.shape)

assert forecast_physical.shape == (12, 255, 4)
assert np.isfinite(forecast_physical).all()

# ------------------------------------------------
# 9. COMPARE WITH ORIGINAL SAVED FORECAST
# ------------------------------------------------

saved_path = FORECAST_DIR / "forecast_2025_physical.npy"

if saved_path.exists():

    saved_forecast = np.load(saved_path)

    print("\nSaved forecast shape:", saved_forecast.shape)

    if saved_forecast.shape == forecast_physical.shape:

        difference = np.abs(
            saved_forecast - forecast_physical
        )

        print(
            "Maximum absolute difference:",
            float(difference.max())
        )

        print(
            "Mean absolute difference:",
            float(difference.mean())
        )

        print(
            "Reproduces saved forecast:",
            np.allclose(
                saved_forecast,
                forecast_physical,
                rtol=1e-4,
                atol=1e-4
            )
        )

    else:
        print("WARNING: Saved forecast dimensions differ.")

else:
    print("Original saved forecast not found.")

# ------------------------------------------------
# 10. FEATURE-WISE SUMMARY
# ------------------------------------------------

rows = []

for i, feature in enumerate(FEATURES):

    values = forecast_physical[:, :, i]

    rows.append({
        "Feature": feature,
        "Minimum": float(values.min()),
        "Maximum": float(values.max()),
        "Mean": float(values.mean()),
        "Standard_Deviation": float(values.std()),
        "Negative_Values": int((values < 0).sum())
    })

summary = pd.DataFrame(rows)

print("\n2025 FORECAST SUMMARY")
print(summary.to_string(index=False))

# ------------------------------------------------
# 11. SAVE VERIFICATION OUTPUTS
# ------------------------------------------------

np.save(
    OUTPUT_DIR / "independent_forecast_2025.npy",
    forecast_physical
)

np.save(
    OUTPUT_DIR / "independent_forecast_2025_normalized.npy",
    forecast_normalized
)

summary.to_csv(
    OUTPUT_DIR / "forecast_feature_summary.csv",
    index=False
)

metadata = {
    "forecast_year": 2025,
    "model": "GCN-GRU",
    "checkpoint": str(CHECKPOINT_PATH),
    "historical_period": "2015-01 to 2024-12",
    "input_period": "2024-01 to 2024-12",
    "forecast_months": 12,
    "spatial_nodes": 255,
    "features": FEATURES,
    "adjacency": "Normalized symmetric adjacency",
    "forecast_method": "Autoregressive",
    "forecast_shape": list(forecast_physical.shape),
    "finite_predictions": bool(
        np.isfinite(forecast_physical).all()
    )
}

with open(
    OUTPUT_DIR / "forecast_verification_metadata.json",
    "w"
) as f:
    json.dump(metadata, f, indent=4)

print("\n" + "=" * 75)
print("CELL 28 COMPLETED")
print("=" * 75)
print("Saved:", OUTPUT_DIR)


# ============================================================
# ORIGINAL NOTEBOOK CELL 40
# Execution count: 49
# ============================================================


# ================================================================
# CELL 29: FORECAST REPRODUCIBILITY DIFFERENCE ANALYSIS
# ================================================================

import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

FORECAST_DIR = PROJECT_ROOT / "outputs" / "future_forecasting"
VERIFY_DIR = PROJECT_ROOT / "outputs" / "forecast_verification"

FEATURES = ["T2M", "PRECTOTCORR", "RH2M", "WS10M"]

independent = np.load(
    VERIFY_DIR / "independent_forecast_2025.npy"
)

original = np.load(
    FORECAST_DIR / "forecast_2025_physical.npy"
)

difference = np.abs(independent - original)

print("=" * 75)
print("1. OVERALL DIFFERENCE DIAGNOSTICS")
print("=" * 75)

print("Maximum difference:", difference.max())
print("Mean difference:", difference.mean())
print("Median difference:", np.median(difference))
print("95th percentile:", np.percentile(difference, 95))
print("99th percentile:", np.percentile(difference, 99))

for tolerance in [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]:
    percentage = (
        np.sum(difference <= tolerance) /
        difference.size
    ) * 100

    print(
        f"Values within {tolerance}: {percentage:.4f}%"
    )

# ------------------------------------------------
# 2. FEATURE-WISE DIFFERENCES
# ------------------------------------------------

print("\n" + "=" * 75)
print("2. FEATURE-WISE DIFFERENCES")
print("=" * 75)

rows = []

for i, feature in enumerate(FEATURES):

    d = difference[:, :, i]

    rows.append({
        "Feature": feature,
        "Max_Difference": d.max(),
        "Mean_Difference": d.mean(),
        "Median_Difference": np.median(d),
        "RMSE_Difference": np.sqrt(np.mean(d ** 2)),
        "Values_Above_1e-4": int((d > 1e-4).sum())
    })

feature_diff = pd.DataFrame(rows)
print(feature_diff.to_string(index=False))

# ------------------------------------------------
# 3. IDENTIFY LARGEST DIFFERENCES
# ------------------------------------------------

print("\n" + "=" * 75)
print("3. LARGEST DIFFERENCE LOCATIONS")
print("=" * 75)

top_indices = np.argsort(
    difference.reshape(-1)
)[-10:][::-1]

top_rows = []

for flat_index in top_indices:

    month, node, feature_index = np.unravel_index(
        flat_index,
        difference.shape
    )

    top_rows.append({
        "Forecast_Month": month + 1,
        "Node_Index": node,
        "Feature": FEATURES[feature_index],
        "Original": original[month, node, feature_index],
        "Independent": independent[month, node, feature_index],
        "Absolute_Difference": difference[
            month, node, feature_index
        ]
    })

top_df = pd.DataFrame(top_rows)
print(top_df.to_string(index=False))

# ------------------------------------------------
# 4. CHECK SAVED NORMALIZED FORECAST
# ------------------------------------------------

print("\n" + "=" * 75)
print("4. SAVED FORECAST FILES")
print("=" * 75)

for path in sorted(FORECAST_DIR.glob("*.npy")):

    arr = np.load(path)

    print(
        path.name,
        "| shape:", arr.shape,
        "| dtype:", arr.dtype,
        "| finite:", np.isfinite(arr).all()
    )

# ------------------------------------------------
# 5. CHECK PRECIPITATION PHYSICAL VALIDITY
# ------------------------------------------------

print("\n" + "=" * 75)
print("5. PRECIPITATION VALIDITY")
print("=" * 75)

precip = independent[:, :, 1]

print("Minimum:", precip.min())
print("Negative count:", (precip < 0).sum())
print("Zero or positive count:", (precip >= 0).sum())
print("Negative percentage:", (precip < 0).mean() * 100)

# ------------------------------------------------
# 6. SAVE DIAGNOSTICS
# ------------------------------------------------

feature_diff.to_csv(
    VERIFY_DIR / "forecast_difference_by_feature.csv",
    index=False
)

top_df.to_csv(
    VERIFY_DIR / "largest_forecast_differences.csv",
    index=False
)

print("\n" + "=" * 75)
print("CELL 29 COMPLETED")
print("=" * 75)


# ============================================================
# ORIGINAL NOTEBOOK CELL 41
# Execution count: 50
# ============================================================


# ================================================================
# CELL 30: FINAL 2025 FORECAST INTEGRITY REPORT
# ================================================================

import json
import numpy as np
import pandas as pd

from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

VERIFY_DIR = PROJECT_ROOT / "outputs" / "forecast_verification"
FORECAST_DIR = PROJECT_ROOT / "outputs" / "future_forecasting"
TRAIN_DIR = PROJECT_ROOT / "outputs" / "model_training"

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "final_forecast_integrity"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = ["T2M", "PRECTOTCORR", "RH2M", "WS10M"]

# ------------------------------------------------
# 1. LOAD FORECASTS
# ------------------------------------------------

original = np.load(
    FORECAST_DIR / "forecast_2025_physical.npy"
)

independent = np.load(
    VERIFY_DIR / "independent_forecast_2025.npy"
)

historical = np.load(
    PROJECT_ROOT / "data" / "processed" / "nasa_power_tensor.npy"
)

assert original.shape == independent.shape == (12, 255, 4)
assert historical.shape == (120, 255, 4)

assert np.isfinite(original).all()
assert np.isfinite(independent).all()
assert np.isfinite(historical).all()

# ------------------------------------------------
# 2. REPRODUCIBILITY
# ------------------------------------------------

difference = np.abs(original - independent)

reproducibility = {
    "maximum_absolute_difference": float(difference.max()),
    "mean_absolute_difference": float(difference.mean()),
    "median_absolute_difference": float(np.median(difference)),
    "percentile_95": float(np.percentile(difference, 95)),
    "percentile_99": float(np.percentile(difference, 99)),
    "within_1e-4_percent": float(
        np.mean(difference <= 1e-4) * 100
    ),
    "within_1e-3_percent": float(
        np.mean(difference <= 1e-3) * 100
    ),
    "exact_match": bool(np.array_equal(original, independent))
}

# ------------------------------------------------
# 3. FEATURE-WISE FORECAST STATISTICS
# ------------------------------------------------

feature_rows = []

for i, feature in enumerate(FEATURES):

    values = original[:, :, i]
    historical_values = historical[:, :, i]

    feature_rows.append({
        "Feature": feature,
        "Historical_Min": float(historical_values.min()),
        "Historical_Max": float(historical_values.max()),
        "Forecast_Min": float(values.min()),
        "Forecast_Max": float(values.max()),
        "Forecast_Mean": float(values.mean()),
        "Forecast_Std": float(values.std()),
        "Negative_Count": int((values < 0).sum())
    })

feature_df = pd.DataFrame(feature_rows)

# ------------------------------------------------
# 4. PRECIPITATION VALIDATION
# ------------------------------------------------

precip = original[:, :, 1]

negative_precip = int((precip < 0).sum())
total_precip = int(precip.size)

precipitation_validation = {
    "negative_predictions": negative_precip,
    "total_predictions": total_precip,
    "negative_percentage": float(
        negative_precip / total_precip * 100
    ),
    "minimum_prediction_mm_per_day": float(precip.min()),
    "physical_constraint_satisfied": bool(
        np.all(precip >= 0)
    )
}

# ------------------------------------------------
# 5. FINAL VALIDATION CHECKS
# ------------------------------------------------

checks = {
    "historical_tensor_valid": historical.shape == (120, 255, 4),
    "original_forecast_valid": original.shape == (12, 255, 4),
    "independent_forecast_valid": independent.shape == (12, 255, 4),
    "original_forecast_finite": bool(np.isfinite(original).all()),
    "independent_forecast_finite": bool(np.isfinite(independent).all()),
    "numerical_agreement_within_0_001": bool(
        np.mean(difference <= 0.001) >= 0.99
    ),
    "precipitation_nonnegative": bool(np.all(precip >= 0))
}

# ------------------------------------------------
# 6. REPORT
# ------------------------------------------------

report = {
    "project": "NASA Earth Systems Trend Detective",
    "report": "2025 Forecast Integrity Verification",
    "generated_at": datetime.now().isoformat(),
    "model": "GCN-GRU",
    "historical_period": "2015-01 to 2024-12",
    "forecast_period": "2025-01 to 2025-12",
    "spatial_nodes": 255,
    "features": FEATURES,
    "forecast_method": "12-month autoregressive forecasting",
    "adjacency": "Normalized symmetric spatial adjacency",
    "reproducibility": reproducibility,
    "precipitation_validation": precipitation_validation,
    "validation_checks": checks,
    "scientific_limitations": [
        "The forecast is exploratory and is not an operational climate prediction.",
        "The model uses a limited 10-year historical period.",
        "External climate forcing is not included.",
        "Negative precipitation predictions violate physical non-negativity.",
        "Numerical reproduction is close but not bit-for-bit identical.",
        "Forecast uncertainty has not been fully quantified."
    ]
}

with open(
    OUTPUT_DIR / "final_forecast_integrity_report.json",
    "w"
) as f:
    json.dump(report, f, indent=4)

feature_df.to_csv(
    OUTPUT_DIR / "forecast_feature_integrity.csv",
    index=False
)

# ------------------------------------------------
# 7. HUMAN-READABLE REPORT
# ------------------------------------------------

lines = [
    "NASA EARTH SYSTEMS TREND DETECTIVE",
    "FINAL 2025 FORECAST INTEGRITY REPORT",
    "=" * 65,
    "",
    "MODEL: GCN-GRU",
    "HISTORICAL PERIOD: January 2015 - December 2024",
    "FORECAST PERIOD: January 2025 - December 2025",
    "SPATIAL NODES: 255",
    "FEATURES: T2M, PRECTOTCORR, RH2M, WS10M",
    "",
    "1. FORECAST DIMENSIONS",
    "-" * 65,
    f"Historical tensor: {historical.shape}",
    f"Original forecast: {original.shape}",
    f"Independent forecast: {independent.shape}",
    "",
    "2. REPRODUCIBILITY",
    "-" * 65,
    f"Maximum difference: {difference.max():.9f}",
    f"Mean difference: {difference.mean():.9f}",
    f"95th percentile: {np.percentile(difference, 95):.9f}",
    f"99th percentile: {np.percentile(difference, 99):.9f}",
    f"Within 0.001: {reproducibility['within_1e-3_percent']:.4f}%",
    f"Exact match: {reproducibility['exact_match']}",
    "",
    "3. FEATURE STATISTICS",
    "-" * 65,
    feature_df.to_string(index=False),
    "",
    "4. PRECIPITATION PHYSICAL VALIDATION",
    "-" * 65,
    f"Negative predictions: {negative_precip}",
    f"Total predictions: {total_precip}",
    f"Negative percentage: {precipitation_validation['negative_percentage']:.4f}%",
    f"Minimum precipitation: {precip.min():.6f} mm/day",
    f"Non-negativity satisfied: {precipitation_validation['physical_constraint_satisfied']}",
    "",
    "5. VALIDATION CHECKS",
    "-" * 65,
]

for name, status in checks.items():
    lines.append(f"{name}: {'PASS' if status else 'FAIL'}")

lines += [
    "",
    "6. SCIENTIFIC LIMITATIONS",
    "-" * 65,
]

for limitation in report["scientific_limitations"]:
    lines.append("- " + limitation)

lines += [
    "",
    "CONCLUSION",
    "-" * 65,
    "The independent 2025 forecast closely reproduces the saved forecast.",
    "The model output is finite and has the expected dimensions.",
    "However, precipitation non-negativity is not enforced.",
    "The forecast should be interpreted as an exploratory model scenario,",
    "not as an operational or causal climate prediction.",
]

report_text = "\n".join(lines)

with open(
    OUTPUT_DIR / "final_forecast_integrity_report.txt",
    "w",
    encoding="utf-8"
) as f:
    f.write(report_text)

print(report_text)

print("\nSaved report directory:")
print(OUTPUT_DIR)

print("\nCELL 30 COMPLETED")


# ============================================================
# ORIGINAL NOTEBOOK CELL 42
# Execution count: 51
# ============================================================


# ================================================================
# CELL 31: MASTER SCIENTIFIC VALIDATION REPORT
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import json
import numpy as np
import pandas as pd

from pathlib import Path
from datetime import datetime

# ------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------

ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

DATA_DIR = ROOT / "data" / "processed"
TRAIN_DIR = ROOT / "outputs" / "model_training"
GRAPH_DIR = ROOT / "outputs" / "spatial_graph"

EVAL_DIR = ROOT / "outputs" / "model_evaluation"
TREND_DIR = ROOT / "outputs" / "historical_trend_analysis"
ROBUSTNESS_DIR = ROOT / "outputs" / "final_trend_robustness"
FORECAST_DIR = ROOT / "outputs" / "future_forecasting"
FORECAST_VERIFY_DIR = ROOT / "outputs" / "forecast_verification"

OUTPUT_DIR = ROOT / "outputs" / "master_scientific_validation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = ["T2M", "PRECTOTCORR", "RH2M", "WS10M"]

UNITS = {
    "T2M": "°C",
    "PRECTOTCORR": "mm/day",
    "RH2M": "%",
    "WS10M": "m/s"
}

print("=" * 75)
print("MASTER SCIENTIFIC VALIDATION")
print("=" * 75)

# ------------------------------------------------
# 2. LOAD CORE DATA
# ------------------------------------------------

tensor_path = DATA_DIR / "nasa_power_tensor.npy"
nodes_path = DATA_DIR / "spatial_nodes.csv"
time_path = DATA_DIR / "tensor_time_index.npy"

assert tensor_path.exists(), f"Missing: {tensor_path}"
assert nodes_path.exists(), f"Missing: {nodes_path}"
assert time_path.exists(), f"Missing: {time_path}"

historical = np.load(tensor_path)
nodes = pd.read_csv(nodes_path)
time_index = np.load(time_path, allow_pickle=True)

assert historical.shape == (120, 255, 4)

print("\nDATA")
print("Historical tensor:", historical.shape)
print("Spatial nodes:", len(nodes))
print("Time steps:", len(time_index))
print("Features:", FEATURES)

# ------------------------------------------------
# 3. LOAD MODEL PERFORMANCE
# ------------------------------------------------

possible_metric_files = [
    EVAL_DIR / "model_performance_metrics.csv",
    EVAL_DIR / "evaluation_metrics.csv",
    EVAL_DIR / "gcn_gru_metrics.csv",
    ROOT / "outputs" / "independent_model_verification_corrected"
        / "independent_model_metrics.csv"
]

metric_path = next(
    (p for p in possible_metric_files if p.exists()),
    None
)

metrics = None

if metric_path is not None:
    metrics = pd.read_csv(metric_path)
    print("\nLoaded model metrics:", metric_path)
    print(metrics.to_string(index=False))
else:
    print("\nWARNING: No recognized model metrics CSV found.")
    print("Search the evaluation output folder for the correct file.")

# ------------------------------------------------
# 4. LOAD TREND ANALYSIS
# ------------------------------------------------

trend_files = list(TREND_DIR.glob("*.csv"))

trend_data = {}

for path in trend_files:
    try:
        df = pd.read_csv(path)
        trend_data[path.name] = df
    except Exception as e:
        print("Could not load:", path.name, e)

print("\nTREND FILES FOUND:")
for name, df in trend_data.items():
    print(name, df.shape)

# ------------------------------------------------
# 5. LOAD ROBUSTNESS SUMMARY
# ------------------------------------------------

robustness_files = list(ROBUSTNESS_DIR.glob("*.csv"))

robustness_data = {}

for path in robustness_files:
    try:
        df = pd.read_csv(path)
        robustness_data[path.name] = df
    except Exception as e:
        print("Could not load:", path.name, e)

print("\nROBUSTNESS FILES FOUND:")
for name, df in robustness_data.items():
    print(name, df.shape)

# ------------------------------------------------
# 6. LOAD FORECAST RESULTS
# ------------------------------------------------

original_forecast = np.load(
    FORECAST_DIR / "forecast_2025_physical.npy"
)

independent_forecast = np.load(
    FORECAST_VERIFY_DIR / "independent_forecast_2025.npy"
)

assert original_forecast.shape == (12, 255, 4)
assert independent_forecast.shape == (12, 255, 4)

forecast_difference = np.abs(
    original_forecast - independent_forecast
)

forecast_rows = []

for i, feature in enumerate(FEATURES):

    values = original_forecast[:, :, i]

    forecast_rows.append({
        "Feature": feature,
        "Unit": UNITS[feature],
        "Minimum": float(values.min()),
        "Maximum": float(values.max()),
        "Mean": float(values.mean()),
        "Standard_Deviation": float(values.std()),
        "Negative_Count": int((values < 0).sum())
    })

forecast_summary = pd.DataFrame(forecast_rows)

forecast_summary.to_csv(
    OUTPUT_DIR / "master_forecast_summary.csv",
    index=False
)

# ------------------------------------------------
# 7. LOAD FINAL SCIENTIFIC VALIDATION
# ------------------------------------------------

validation_path = (
    ROOT / "outputs" /
    "final_scientific_validation.json"
)

validation_text_path = (
    ROOT / "outputs" /
    "final_scientific_validation.md"
)

if validation_path.exists():
    with open(validation_path, "r") as f:
        final_validation = json.load(f)
else:
    final_validation = None

# ------------------------------------------------
# 8. COMPUTE DATASET AND GRAPH STATISTICS
# ------------------------------------------------

adjacency_path = GRAPH_DIR / "adjacency_matrix.npz"

from scipy.sparse import load_npz

raw_adjacency = load_npz(adjacency_path).toarray()

normalized_adjacency = np.asarray(
    globals().get("normalized_adjacency"),
    dtype=np.float32
)

assert normalized_adjacency.shape == (255, 255)

graph_stats = {
    "nodes": int(raw_adjacency.shape[0]),
    "edges_directed": int(np.count_nonzero(raw_adjacency)),
    "raw_adjacency_symmetric": bool(
        np.allclose(raw_adjacency, raw_adjacency.T)
    ),
    "normalized_adjacency_symmetric": bool(
        np.allclose(normalized_adjacency, normalized_adjacency.T)
    ),
    "normalized_adjacency_max": float(
        normalized_adjacency.max()
    )
}

# ------------------------------------------------
# 9. SCIENTIFIC CHECKS
# ------------------------------------------------

precipitation = original_forecast[:, :, 1]

checks = {
    "historical_tensor_dimensions": historical.shape == (120, 255, 4),
    "historical_tensor_finite": bool(np.isfinite(historical).all()),
    "spatial_nodes_valid": len(nodes) == 255,
    "graph_dimensions_valid": raw_adjacency.shape == (255, 255),
    "graph_symmetric": graph_stats["raw_adjacency_symmetric"],
    "normalized_graph_symmetric": graph_stats[
        "normalized_adjacency_symmetric"
    ],
    "forecast_dimensions_valid": original_forecast.shape == (12, 255, 4),
    "forecast_finite": bool(np.isfinite(original_forecast).all()),
    "forecast_reproducibility_99_percent": bool(
        np.mean(forecast_difference <= 0.001) >= 0.99
    ),
    "precipitation_nonnegative": bool(
        np.all(precipitation >= 0)
    )
}

# ------------------------------------------------
# 10. BUILD PROJECT REPORT
# ------------------------------------------------

report = {
    "project": "NASA Earth Systems Trend Detective",
    "report_type": "Master Scientific Validation",
    "generated_at": datetime.now().isoformat(),
    "study_region": "India",
    "historical_period": "2015-01 to 2024-12",
    "forecast_period": "2025-01 to 2025-12",
    "data_source": "NASA POWER",
    "features": FEATURES,
    "feature_units": UNITS,
    "historical_tensor_shape": list(historical.shape),
    "spatial_nodes": len(nodes),
    "graph": graph_stats,
    "model": {
        "architecture": "GCN-GRU",
        "parameters": 20292,
        "gcn_hidden": 32,
        "gru_hidden": 64,
        "dropout": 0.15,
        "sequence_length": 12
    },
    "forecast": {
        "shape": list(original_forecast.shape),
        "method": "Autoregressive",
        "maximum_reproduction_difference": float(
            forecast_difference.max()
        ),
        "mean_reproduction_difference": float(
            forecast_difference.mean()
        ),
        "within_0_001_percent": float(
            np.mean(forecast_difference <= 0.001) * 100
        ),
        "negative_precipitation_count": int(
            (precipitation < 0).sum()
        ),
        "negative_precipitation_percentage": float(
            np.mean(precipitation < 0) * 100
        )
    },
    "validation_checks": checks,
    "scientific_limitations": [
        "The analysis uses a 10-year historical period.",
        "The study uses four NASA POWER meteorological variables.",
        "The spatial graph represents geographic proximity, not atmospheric transport.",
        "The model does not explicitly incorporate external climate forcing.",
        "The 2025 forecast is exploratory, not operational.",
        "2025 forecast accuracy cannot be established without independent observations.",
        "Negative precipitation predictions violate physical non-negativity.",
        "Trend significance is subject to autocorrelation and short-record uncertainty.",
        "Trend analysis does not establish causal attribution."
    ]
}

# ------------------------------------------------
# 11. SAVE CSV AND JSON OUTPUTS
# ------------------------------------------------

if metrics is not None:
    metrics.to_csv(
        OUTPUT_DIR / "master_model_performance.csv",
        index=False
    )

with open(
    OUTPUT_DIR / "master_scientific_validation.json",
    "w"
) as f:
    json.dump(report, f, indent=4, default=str)

# ------------------------------------------------
# 12. CREATE MARKDOWN REPORT
# ------------------------------------------------

lines = [
    "# NASA Earth Systems Trend Detective",
    "",
    "## Master Scientific Validation Report",
    "",
    f"Generated: {report['generated_at']}",
    "",
    "## 1. Project Overview",
    "",
    "This project analyzes historical meteorological variability across India "
    "using NASA POWER data and a spatial-temporal GCN-GRU model.",
    "",
    "The workflow includes spatial aggregation, graph construction, "
    "model training, historical trend analysis, and exploratory forecasting.",
    "",
    "## 2. Dataset",
    "",
    "| Property | Value |",
    "|---|---|",
    f"| Data source | {report['data_source']} |",
    f"| Study region | {report['study_region']} |",
    f"| Historical period | {report['historical_period']} |",
    f"| Monthly time steps | {historical.shape[0]} |",
    f"| Spatial nodes | {len(nodes)} |",
    f"| Tensor shape | {historical.shape} |",
    "",
    "### Variables",
    "",
    "| Variable | Unit |",
    "|---|---|",
]

for feature in FEATURES:
    lines.append(f"| {feature} | {UNITS[feature]} |")

lines += [
    "",
    "## 3. Spatial Graph",
    "",
    "A symmetric geographic K-nearest-neighbor graph was constructed "
    "using a BallTree with haversine distances, K=6, self-loops, "
    "and Gaussian distance weighting.",
    "",
    f"- Spatial nodes: {graph_stats['nodes']}",
    f"- Directed nonzero entries: {graph_stats['edges_directed']}",
    f"- Raw adjacency symmetric: {graph_stats['raw_adjacency_symmetric']}",
    f"- Normalized adjacency symmetric: {graph_stats['normalized_adjacency_symmetric']}",
    "",
    "The graph represents geographic proximity. It does not model "
    "atmospheric circulation or physical transport.",
    "",
    "## 4. Model Architecture",
    "",
    "| Property | Value |",
    "|---|---|",
    "| Architecture | GCN-GRU |",
    "| GCN hidden dimensions | 32 |",
    "| GRU hidden dimensions | 64 |",
    "| Input features | 4 |",
    "| Output features | 4 |",
    "| Sequence length | 12 months |",
    "| Dropout | 0.15 |",
    "| Parameters | 20,292 |",
    "",
    "Training used chronological train, validation, and test periods:",
    "",
    "- Training: January 2015 – December 2021",
    "- Validation: January 2022 – December 2023",
    "- Testing: January 2024 – December 2024",
    "",
    "## 5. Model Evaluation",
    "",
]

if metrics is not None:
    lines.append(metrics.to_markdown(index=False))
else:
    lines.append(
        "Model evaluation CSV was not found in the expected locations. "
        "See the independently verified model evaluation outputs."
    )

lines += [
    "",
    "The 2024 test evaluation used rolling one-step-ahead predictions. "
    "The model outperformed the persistence baseline on all four variables "
    "in the independently verified evaluation.",
    "",
    "## 6. Historical Trend Analysis",
    "",
    "Seasonal Mann-Kendall testing and Sen slope estimation were performed "
    "for the four variables across the spatial nodes, with Benjamini-Hochberg "
    "false-discovery-rate adjustment.",
    "",
    "Autocorrelation diagnostics and trend-free pre-whitening sensitivity "
    "analyses were also conducted.",
    "",
    "The short 10-year record and residual dependence mean that trend "
    "significance should be interpreted cautiously.",
    "",
    "### Trend output files",
    ""
]

for filename in trend_data:
    lines.append(f"- `{filename}`")

lines += [
    "",
    "### Robustness output files",
    ""
]

for filename in robustness_data:
    lines.append(f"- `{filename}`")

lines += [
    "",
    "## 7. Exploratory 2025 Forecast",
    "",
    "A 12-month autoregressive forecast was generated using the final "
    "12 historical months as input.",
    "",
    f"- Forecast dimensions: {original_forecast.shape}",
    f"- Maximum independent reproduction difference: "
    f"{forecast_difference.max():.9f}",
    f"- Mean independent reproduction difference: "
    f"{forecast_difference.mean():.9f}",
    f"- Values within 0.001: "
    f"{np.mean(forecast_difference <= 0.001) * 100:.4f}%",
    "",
    "### Forecast summary",
    "",
    forecast_summary.to_markdown(index=False),
    "",
    "### Physical plausibility",
    "",
    f"The forecast contains {int((precipitation < 0).sum())} negative "
    f"precipitation values out of {precipitation.size} predictions "
    f"({np.mean(precipitation < 0) * 100:.4f}%). "
    "This violates precipitation non-negativity and must be disclosed.",
    "",
    "The 2025 forecast has not been validated against independent 2025 "
    "observations. Reproducing the saved forecast is not the same as "
    "demonstrating forecast accuracy.",
    "",
    "## 8. Validation Checklist",
    "",
    "| Check | Result |",
    "|---|---|"
]

for name, status in checks.items():
    lines.append(
        f"| {name.replace('_', ' ').title()} | "
        f"{'PASS' if status else 'FAIL'} |"
    )

lines += [
    "",
    "## 9. Scientific Limitations",
    ""
]

for limitation in report["scientific_limitations"]:
    lines.append(f"- {limitation}")

lines += [
    "",
    "## 10. Conclusion",
    "",
    "The project establishes a reproducible spatial-temporal modeling "
    "workflow for analyzing four NASA POWER meteorological variables "
    "over India from 2015 through 2024.",
    "",
    "The GCN-GRU model outperformed a persistence baseline on all four "
    "variables in the held-out 2024 evaluation. Historical trend analysis "
    "provides spatially resolved estimates, with autocorrelation and "
    "short-record limitations requiring cautious interpretation.",
    "",
    "The 2025 autoregressive forecast is numerically reproducible to a "
    "close tolerance but is exploratory and has not been independently "
    "validated against 2025 observations. Negative precipitation outputs "
    "remain a physical plausibility limitation.",
    "",
    "The results should therefore be presented as a research prototype "
    "for Earth-system trend exploration, not as an operational climate "
    "forecasting or causal-attribution system.",
    ""
]

markdown_report = "\n".join(lines)

with open(
    OUTPUT_DIR / "master_scientific_validation_report.md",
    "w",
    encoding="utf-8"
) as f:
    f.write(markdown_report)

# ------------------------------------------------
# 13. FINAL SUMMARY
# ------------------------------------------------

print("\n" + "=" * 75)
print("MASTER VALIDATION SUMMARY")
print("=" * 75)

for name, status in checks.items():
    print(f"{name}: {'PASS' if status else 'FAIL'}")

print("\nForecast mean difference:", forecast_difference.mean())
print("Forecast maximum difference:", forecast_difference.max())

print("\nGenerated files:")

for path in sorted(OUTPUT_DIR.iterdir()):
    print(path.name)

print("\nMASTER REPORT DIRECTORY:")
print(OUTPUT_DIR)

print("\nCELL 31 COMPLETED")


# ============================================================
# ORIGINAL NOTEBOOK CELL 43
# Execution count: 52
# ============================================================


# ================================================================
# CELL 32: FIND MODEL METRICS AND INSPECT TREND REPORTS
# ================================================================

from pathlib import Path
import pandas as pd

ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

OUTPUTS = ROOT / "outputs"

print("=" * 75)
print("CELL 32: OUTPUT DISCOVERY AND REPORT DIAGNOSTICS")
print("=" * 75)

# ------------------------------------------------
# 1. SEARCH ALL CSV FILES FOR MODEL METRICS
# ------------------------------------------------

print("\n[1] SEARCHING FOR MODEL EVALUATION CSV FILES")

metric_candidates = []

for path in OUTPUTS.rglob("*.csv"):
    try:
        df = pd.read_csv(path, nrows=5)

        columns = [
            str(c).lower().replace(" ", "_")
            for c in df.columns
        ]

        has_error_metric = any(
            "mae" in c or "rmse" in c
            for c in columns
        )

        has_model_context = any(
            word in str(path).lower()
            for word in [
                "model", "evaluation", "metric",
                "performance", "verification"
            ]
        )

        if has_error_metric or has_model_context:
            metric_candidates.append(path)

    except Exception:
        pass

for i, path in enumerate(metric_candidates, 1):
    print(f"\n{i}. {path.relative_to(ROOT)}")

    try:
        df = pd.read_csv(path)
        print("Columns:", df.columns.tolist())
        print(df.head(5).to_string(index=False))
    except Exception as e:
        print("Read error:", e)

if not metric_candidates:
    print("No possible model metric CSV files found.")

# ------------------------------------------------
# 2. INSPECT FEATURE-WISE TREND SUMMARY
# ------------------------------------------------

print("\n" + "=" * 75)
print("[2] FEATURE-WISE TREND SUMMARY")
print("=" * 75)

trend_path = (
    OUTPUTS / "historical_trend_analysis"
    / "feature_trend_summary.csv"
)

if trend_path.exists():
    trend_df = pd.read_csv(trend_path)

    print("File:", trend_path)
    print("Shape:", trend_df.shape)
    print("Columns:", trend_df.columns.tolist())
    print("\nFull feature-wise summary:")
    print(trend_df.to_string(index=False))
else:
    print("Feature-wise trend summary not found:", trend_path)

# ------------------------------------------------
# 3. INSPECT TREND ROBUSTNESS SUMMARY
# ------------------------------------------------

print("\n" + "=" * 75)
print("[3] FEATURE-WISE TREND ROBUSTNESS")
print("=" * 75)

robust_path = (
    OUTPUTS / "final_trend_robustness"
    / "feature_wise_trend_robustness.csv"
)

if robust_path.exists():
    robust_df = pd.read_csv(robust_path)

    print("File:", robust_path)
    print("Shape:", robust_df.shape)
    print("Columns:", robust_df.columns.tolist())
    print("\nFull robustness summary:")
    print(robust_df.to_string(index=False))
else:
    print("Robustness summary not found:", robust_path)

# ------------------------------------------------
# 4. INSPECT SIGNIFICANCE CATEGORY SUMMARY
# ------------------------------------------------

print("\n" + "=" * 75)
print("[4] SIGNIFICANCE CATEGORY SUMMARY")
print("=" * 75)

significance_path = (
    OUTPUTS / "final_trend_robustness"
    / "significance_category_summary.csv"
)

if significance_path.exists():
    significance_df = pd.read_csv(significance_path)

    print("Columns:", significance_df.columns.tolist())
    print(significance_df.to_string(index=False))
else:
    print("Significance summary not found.")

# ------------------------------------------------
# 5. INSPECT FORECAST INTEGRITY REPORT
# ------------------------------------------------

print("\n" + "=" * 75)
print("[5] FORECAST INTEGRITY REPORT")
print("=" * 75)

integrity_path = (
    OUTPUTS / "final_forecast_integrity"
    / "final_forecast_integrity_report.json"
)

if integrity_path.exists():
    import json

    with open(integrity_path, "r") as f:
        integrity = json.load(f)

    print(json.dumps(integrity, indent=2))
else:
    print("Forecast integrity JSON not found.")

# ------------------------------------------------
# 6. COMPLETION
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 32 COMPLETED")
print("=" * 75)

print(
    "\nShare the output, especially the model metric candidates, "
    "trend summary, and robustness summary."
)


# ============================================================
# ORIGINAL NOTEBOOK CELL 44
# Execution count: 53
# ============================================================


# ================================================================
# CELL 33: FINAL MASTER SCIENTIFIC REPORT - CORRECTED
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import json
import numpy as np
import pandas as pd

from pathlib import Path
from datetime import datetime

# ------------------------------------------------
# 1. PATHS
# ------------------------------------------------

ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

OUTPUTS = ROOT / "outputs"

METRIC_PATH = (
    OUTPUTS / "evaluation" / "evaluation_metrics_2024.csv"
)

TREND_PATH = (
    OUTPUTS / "historical_trend_analysis"
    / "feature_trend_summary.csv"
)

ROBUSTNESS_PATH = (
    OUTPUTS / "final_trend_robustness"
    / "feature_wise_trend_robustness.csv"
)

SIGNIFICANCE_PATH = (
    OUTPUTS / "final_trend_robustness"
    / "significance_category_summary.csv"
)

FORECAST_PATH = (
    OUTPUTS / "future_forecasting"
    / "forecast_2025_physical.npy"
)

FORECAST_INTEGRITY_PATH = (
    OUTPUTS / "final_forecast_integrity"
    / "final_forecast_integrity_report.json"
)

TRAINING_HISTORY_PATH = (
    OUTPUTS / "model_training" / "training_history.csv"
)

REPORT_DIR = OUTPUTS / "master_scientific_validation"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------
# 2. VERIFY REQUIRED FILES
# ------------------------------------------------

required_files = [
    METRIC_PATH,
    TREND_PATH,
    ROBUSTNESS_PATH,
    SIGNIFICANCE_PATH,
    FORECAST_PATH,
    FORECAST_INTEGRITY_PATH,
    TRAINING_HISTORY_PATH
]

missing = [str(p) for p in required_files if not p.exists()]

if missing:
    raise FileNotFoundError(
        "Required report files are missing:\n" +
        "\n".join(missing)
    )

# ------------------------------------------------
# 3. LOAD SOURCE RESULTS
# ------------------------------------------------

metrics = pd.read_csv(METRIC_PATH)
trends = pd.read_csv(TREND_PATH)
robustness = pd.read_csv(ROBUSTNESS_PATH)
significance = pd.read_csv(SIGNIFICANCE_PATH)
training_history = pd.read_csv(TRAINING_HISTORY_PATH)

forecast = np.load(FORECAST_PATH)

with open(FORECAST_INTEGRITY_PATH, "r") as f:
    forecast_integrity = json.load(f)

# ------------------------------------------------
# 4. NORMALIZE COLUMN NAMES
# ------------------------------------------------

metrics.columns = [
    c.strip() for c in metrics.columns
]

trends.columns = [
    c.strip() for c in trends.columns
]

robustness.columns = [
    c.strip() for c in robustness.columns
]

significance.columns = [
    c.strip() for c in significance.columns
]

# ------------------------------------------------
# 5. VALIDATE SOURCE CONTENT
# ------------------------------------------------

FEATURES = ["T2M", "PRECTOTCORR", "RH2M", "WS10M"]

assert len(metrics) == 4
assert len(trends) == 4
assert len(robustness) == 4
assert forecast.shape == (12, 255, 4)

assert set(metrics["Feature"]) == set(FEATURES)
assert set(trends["feature"]) == set(FEATURES)
assert set(robustness["feature"]) == set(FEATURES)

assert np.isfinite(forecast).all()

# Confirm model outperforms persistence.
assert (
    metrics["GCN_GRU_MAE"] <
    metrics["Persistence_MAE"]
).all()

assert (
    metrics["GCN_GRU_RMSE"] <
    metrics["Persistence_RMSE"]
).all()

# ------------------------------------------------
# 6. TRAINING SUMMARY
# ------------------------------------------------

best_epoch_row = training_history.loc[
    training_history["validation_loss"].idxmin()
]

training_summary = {
    "epochs_completed": int(len(training_history)),
    "best_validation_epoch": int(best_epoch_row["epoch"]),
    "best_validation_loss": float(
        best_epoch_row["validation_loss"]
    ),
    "final_training_loss": float(
        training_history.iloc[-1]["train_loss"]
    ),
    "final_validation_loss": float(
        training_history.iloc[-1]["validation_loss"]
    )
}

# ------------------------------------------------
# 7. FORECAST SUMMARY
# ------------------------------------------------

forecast_rows = []

units = {
    "T2M": "°C",
    "PRECTOTCORR": "mm/day",
    "RH2M": "%",
    "WS10M": "m/s"
}

for i, feature in enumerate(FEATURES):

    values = forecast[:, :, i]

    forecast_rows.append({
        "Feature": feature,
        "Unit": units[feature],
        "Minimum": float(values.min()),
        "Maximum": float(values.max()),
        "Mean": float(values.mean()),
        "Standard_Deviation": float(values.std()),
        "Negative_Values": int((values < 0).sum())
    })

forecast_summary = pd.DataFrame(forecast_rows)

forecast_summary.to_csv(
    REPORT_DIR / "master_forecast_summary.csv",
    index=False
)

# ------------------------------------------------
# 8. TREND ROBUSTNESS SUMMARY
# ------------------------------------------------

# Only significance overlap is reported.
# Direction agreement fields are deliberately excluded.

robustness_columns = [
    "feature",
    "nodes",
    "original_significant_nodes",
    "tfpw_significant_nodes",
    "significant_in_both",
    "lost_significance",
    "newly_significant",
    "not_significant_in_either",
    "mean_centered_rho",
    "mean_uncentered_rho",
    "robustness_label"
]

robustness_report = robustness[
    robustness_columns
].copy()

robustness_report.to_csv(
    REPORT_DIR / "master_trend_robustness_summary.csv",
    index=False
)

trends.to_csv(
    REPORT_DIR / "master_historical_trend_summary.csv",
    index=False
)

metrics.to_csv(
    REPORT_DIR / "master_model_performance.csv",
    index=False
)

# ------------------------------------------------
# 9. SCIENTIFIC VALIDATION CHECKS
# ------------------------------------------------

reproducibility = forecast_integrity["reproducibility"]
precipitation_validation = (
    forecast_integrity["precipitation_validation"]
)

checks = {
    "four_variables_evaluated": len(metrics) == 4,
    "model_beats_persistence_mae": bool(
        (
            metrics["GCN_GRU_MAE"] <
            metrics["Persistence_MAE"]
        ).all()
    ),
    "model_beats_persistence_rmse": bool(
        (
            metrics["GCN_GRU_RMSE"] <
            metrics["Persistence_RMSE"]
        ).all()
    ),
    "trend_results_cover_255_nodes": bool(
        (trends["spatial_nodes"] == 255).all()
    ),
    "forecast_dimensions_valid": forecast.shape == (12, 255, 4),
    "forecast_finite": bool(np.isfinite(forecast).all()),
    "forecast_reproduction_within_0_001": (
        reproducibility["within_1e-3_percent"] >= 99
    ),
    "precipitation_nonnegative": (
        precipitation_validation["physical_constraint_satisfied"]
    )
}

# ------------------------------------------------
# 10. BUILD MASTER JSON
# ------------------------------------------------

master = {
    "project": "NASA Earth Systems Trend Detective",
    "report": "Corrected Master Scientific Validation",
    "generated_at": datetime.now().isoformat(),
    "study_region": "India",
    "historical_period": "January 2015 - December 2024",
    "forecast_period": "January 2025 - December 2025",
    "data_source": "NASA POWER",
    "dataset": {
        "historical_tensor_shape": [120, 255, 4],
        "spatial_nodes": 255,
        "monthly_time_steps": 120,
        "features": FEATURES
    },
    "model": {
        "architecture": "GCN-GRU",
        "parameters": 20292,
        "sequence_length": 12,
        "gcn_hidden": 32,
        "gru_hidden": 64,
        "dropout": 0.15,
        "training_period": "2015-2021",
        "validation_period": "2022-2023",
        "test_period": "2024",
        "training_summary": training_summary
    },
    "model_metrics": metrics.to_dict(orient="records"),
    "historical_trends": trends.to_dict(orient="records"),
    "trend_robustness": robustness_report.to_dict(
        orient="records"
    ),
    "significance_categories": significance.to_dict(
        orient="records"
    ),
    "forecast": {
        "shape": list(forecast.shape),
        "method": "12-month autoregressive",
        "integrity": forecast_integrity,
        "feature_summary": forecast_summary.to_dict(
            orient="records"
        )
    },
    "validation_checks": checks,
    "interpretation_warnings": [
        "The 2024 test results measure historical held-out performance.",
        "The 2025 forecast has not been validated against observed 2025 data.",
        "Forecast numerical reproducibility does not establish forecast accuracy.",
        "Negative precipitation values violate physical non-negativity.",
        "The TFPW analysis is a sensitivity analysis, not a definitive correction.",
        "Direction-agreement columns from the earlier robustness output "
        "are excluded because their calculation is not an independent "
        "direction comparison.",
        "The historical record covers only ten years.",
        "Trend significance is subject to temporal autocorrelation and "
        "short-record uncertainty.",
        "Trend associations do not establish causal attribution.",
        "The geographic graph does not represent atmospheric transport.",
        "The model does not explicitly incorporate external climate forcing.",
        "The analysis uses four NASA POWER variables, not a comprehensive "
        "multi-source Earth-system dataset."
    ]
}

with open(
    REPORT_DIR / "master_scientific_validation.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(master, f, indent=4, default=str)

# ------------------------------------------------
# 11. GENERATE MARKDOWN REPORT
# ------------------------------------------------

lines = [
    "# NASA Earth Systems Trend Detective",
    "",
    "## Corrected Master Scientific Validation Report",
    "",
    f"Generated: {master['generated_at']}",
    "",
    "## 1. Executive Summary",
    "",
    "This project analyzes monthly meteorological conditions across "
    "255 spatial grid nodes covering India from 2015 to 2024.",
    "",
    "A spatial-temporal GCN-GRU model was trained to model four "
    "meteorological variables. Historical test performance was evaluated "
    "against a persistence baseline using the held-out 2024 period.",
    "",
    "The project also performs spatial trend analysis, autocorrelation "
    "diagnostics, TFPW sensitivity analysis, and exploratory 2025 forecasting.",
    "",
    "## 2. Dataset",
    "",
    "| Property | Value |",
    "|---|---|",
    "| Source | NASA POWER |",
    "| Region | India |",
    "| Period | 2015-2024 |",
    "| Monthly observations | 120 |",
    "| Spatial nodes | 255 |",
    "| Features | 4 |",
    "| Tensor shape | (120, 255, 4) |",
    "",
    "### Variables",
    "",
    "| Feature | Unit |",
    "|---|---|",
    "| T2M | °C |",
    "| PRECTOTCORR | mm/day |",
    "| RH2M | % |",
    "| WS10M | m/s |",
    "",
    "PRECTOTCORR represents monthly mean daily precipitation, "
    "not monthly accumulated precipitation.",
    "",
    "## 3. Spatial Graph",
    "",
    "The graph uses a BallTree haversine K-nearest-neighbor construction "
    "with K=6, bidirectional connections, self-loops, and Gaussian "
    "distance weighting.",
    "",
    "The model uses normalized symmetric adjacency during inference.",
    "The graph describes geographic proximity and does not represent "
    "atmospheric transport.",
    "",
    "## 4. GCN-GRU Model",
    "",
    "| Property | Value |",
    "|---|---|",
    "| Architecture | GCN-GRU |",
    "| Parameters | 20,292 |",
    "| GCN hidden dimension | 32 |",
    "| GRU hidden dimension | 64 |",
    "| Sequence length | 12 months |",
    "| Dropout | 0.15 |",
    "| Training | 2015-2021 |",
    "| Validation | 2022-2023 |",
    "| Testing | 2024 |",
    "",
    f"Completed epochs: {training_summary['epochs_completed']}",
    "",
    f"Best validation epoch: {training_summary['best_validation_epoch']}",
    "",
    f"Best validation loss: {training_summary['best_validation_loss']:.6f}",
    "",
    "## 5. Held-Out 2024 Model Evaluation",
    "",
    metrics.to_markdown(index=False),
    "",
    "The GCN-GRU outperformed the persistence baseline on MAE and RMSE "
    "for all four variables.",
    "",
    "The 2024 evaluation uses rolling one-step-ahead predictions. "
    "It should not be confused with a 12-month free-running forecast.",
    "",
    "## 6. Historical Trend Analysis",
    "",
    "Seasonal Mann-Kendall testing, Sen slope estimation, and "
    "Benjamini-Hochberg FDR correction were applied across the "
    "255 spatial nodes.",
    "",
    trends.to_markdown(index=False),
    "",
    "The Sen slope values are reproduced as stored in the source report. "
    "Their exact time-unit convention should be confirmed from the "
    "trend-analysis implementation before assigning a per-year label.",
    "",
    "### Interpretation",
    "",
    "- T2M: 48 nodes were significant after FDR correction.",
    "- PRECTOTCORR: 3 nodes were significant.",
    "- RH2M: 74 nodes were significant.",
    "- WS10M: 17 nodes were significant, all classified as decreasing "
    "in the original trend analysis.",
    "",
    "These counts describe spatial nodes, not land-area percentages.",
    "",
    "## 7. Autocorrelation and Trend Robustness",
    "",
    "Lag-1 and seasonal lag-12 autocorrelation diagnostics indicated "
    "temporal dependence in the variables.",
    "",
    "The following table compares significance overlap between the "
    "original analysis and the TFPW sensitivity analysis.",
    "",
    robustness_report.to_markdown(index=False),
    "",
    "### Important interpretation",
    "",
    "TFPW results are sensitivity results. Newly significant nodes "
    "must not be interpreted as stronger or more reliable trends.",
    "",
    "Direction-agreement fields from the earlier robustness calculation "
    "are intentionally excluded because the direction comparison "
    "was not independent of the original Sen slope.",
    "",
    "Only ten annual observations are available for each calendar month. "
    "Autocorrelation estimates and pre-whitening results therefore "
    "remain uncertain.",
    "",
    "## 8. Exploratory 2025 Forecast",
    "",
    f"Forecast shape: {forecast.shape}",
    "",
    "Method: 12-month autoregressive GCN-GRU forecasting.",
    "",
    forecast_summary.to_markdown(index=False),
    "",
    "### Numerical reproduction",
    "",
    f"- Maximum absolute difference: "
    f"{reproducibility['maximum_absolute_difference']:.9f}",
    f"- Mean absolute difference: "
    f"{reproducibility['mean_absolute_difference']:.9f}",
    f"- Values within 0.001: "
    f"{reproducibility['within_1e-3_percent']:.4f}%",
    f"- Bit-for-bit identical: "
    f"{reproducibility['exact_match']}",
    "",
    "### Physical plausibility",
    "",
    f"Negative precipitation predictions: "
    f"{precipitation_validation['negative_predictions']} / "
    f"{precipitation_validation['total_predictions']} "
    f"({precipitation_validation['negative_percentage']:.4f}%).",
    "",
    "The minimum precipitation prediction is "
    f"{precipitation_validation['minimum_prediction_mm_per_day']:.6f} "
    "mm/day.",
    "",
    "This violates physical non-negativity. The original model output "
    "is retained and the limitation is disclosed rather than silently "
    "clipping the predictions.",
    "",
    "No independent 2025 observational dataset has been used to "
    "establish future forecast accuracy.",
    "",
    "## 9. Validation Checklist",
    "",
    "| Validation | Result |",
    "|---|---|"
]

for name, status in checks.items():
    lines.append(
        f"| {name.replace('_', ' ').title()} | "
        f"{'PASS' if status else 'FAIL'} |"
    )

lines += [
    "",
    "## 10. Scientific Limitations",
    ""
]

for item in master["interpretation_warnings"]:
    lines.append(f"- {item}")

lines += [
    "",
    "## 11. Conclusion",
    "",
    "The project demonstrates a spatial-temporal GCN-GRU workflow "
    "for analyzing four NASA POWER meteorological variables across "
    "India using a 255-node geographic graph.",
    "",
    "The model outperformed persistence on the held-out 2024 evaluation. "
    "The trend analysis identifies spatially varying statistical "
    "patterns, while autocorrelation and short-record limitations "
    "require cautious interpretation.",
    "",
    "The 2025 forecast is exploratory, numerically reproducible "
    "within a close tolerance, and not independently validated "
    "against observed 2025 data. Negative precipitation predictions "
    "remain an unresolved physical constraint violation.",
    "",
    "The appropriate scientific description is a research prototype "
    "for spatial-temporal meteorological trend exploration, not an "
    "operational climate prediction or causal-attribution system.",
    ""
]

report_text = "\n".join(lines)

report_path = (
    REPORT_DIR / "master_scientific_validation_report.md"
)

with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_text)

# ------------------------------------------------
# 12. FINAL SUMMARY
# ------------------------------------------------

print("=" * 75)
print("CELL 33: CORRECTED MASTER REPORT COMPLETED")
print("=" * 75)

print("\nMODEL PERFORMANCE:")
print(
    metrics[
        [
            "Feature",
            "GCN_GRU_MAE",
            "Persistence_MAE",
            "MAE_Improvement_Percent"
        ]
    ].to_string(index=False)
)

print("\nHISTORICAL TREND COUNTS:")
print(
    trends[
        [
            "feature",
            "significant_nodes_after_fdr",
            "increasing_nodes_after_fdr",
            "decreasing_nodes_after_fdr"
        ]
    ].to_string(index=False)
)

print("\nVALIDATION CHECKS:")

for name, status in checks.items():
    print(f"{name}: {'PASS' if status else 'FAIL'}")

print("\nREPORT FILES:")

for path in sorted(REPORT_DIR.iterdir()):
    print(path.name)

print("\nFINAL REPORT:")
print(report_path)

print("\nCELL 33 COMPLETED")


# ============================================================
# ORIGINAL NOTEBOOK CELL 45
# Execution count: 54
# ============================================================


# ================================================================
# CELL 34: FINAL NASA SPACE APPS PROJECT READINESS AUDIT
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

import json
import pandas as pd

from pathlib import Path
from datetime import datetime

# ------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------

ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

OUTPUTS = ROOT / "outputs"
DATA = ROOT / "data"
PROCESSED = DATA / "processed"

AUDIT_DIR = OUTPUTS / "final_project_readiness"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 75)
print("NASA SPACE APPS - FINAL PROJECT READINESS AUDIT")
print("=" * 75)

# ------------------------------------------------
# 2. DEFINE REQUIRED ARTIFACTS
# ------------------------------------------------

artifacts = {
    "Dataset": {
        "Historical tensor": PROCESSED / "nasa_power_tensor.npy",
        "Spatial nodes": PROCESSED / "spatial_nodes.csv",
        "Tensor metadata": PROCESSED / "tensor_metadata.json",
        "Time index": PROCESSED / "tensor_time_index.npy",
        "Processed spatial dataset": PROCESSED / "nasa_power_grid_2deg.parquet"
    },

    "Model": {
        "Best model checkpoint": (
            OUTPUTS / "model_training" /
            "best_gcn_gru_model.pth"
        ),
        "Model configuration": (
            OUTPUTS / "model_training" /
            "gcn_gru_config.json"
        ),
        "Training history": (
            OUTPUTS / "model_training" /
            "training_history.csv"
        ),
        "Training report": (
            OUTPUTS / "model_training" /
            "training_report.json"
        )
    },

    "Spatial graph": {
        "Raw adjacency": (
            OUTPUTS / "spatial_graph" /
            "adjacency_matrix.npz"
        ),
        "Graph edges": (
            OUTPUTS / "spatial_graph" /
            "edge_index.npy"
        ),
        "Graph weights": (
            OUTPUTS / "spatial_graph" /
            "edge_weights.npy"
        ),
        "Graph metadata": (
            OUTPUTS / "spatial_graph" /
            "graph_metadata.json"
        ),
        "Graph visualization": (
            OUTPUTS / "spatial_graph" /
            "spatial_graph.png"
        )
    },

    "Evaluation": {
        "2024 model metrics": (
            OUTPUTS / "evaluation" /
            "evaluation_metrics_2024.csv"
        ),
        "Node-wise predictions": (
            OUTPUTS / "evaluation" /
            "node_wise_predictions_2024.csv"
        ),
        "Corrected independent verification": (
            OUTPUTS / "independent_model_verification_corrected" /
            "corrected_test_metrics.csv"
        )
    },

    "Trend analysis": {
        "Feature trend summary": (
            OUTPUTS / "historical_trend_analysis" /
            "feature_trend_summary.csv"
        ),
        "Node-wise trends": (
            OUTPUTS / "historical_trend_analysis" /
            "node_wise_seasonal_trends.csv"
        ),
        "Trend robustness": (
            OUTPUTS / "final_trend_robustness" /
            "feature_wise_trend_robustness.csv"
        ),
        "Significance summary": (
            OUTPUTS / "final_trend_robustness" /
            "significance_category_summary.csv"
        )
    },

    "Forecast": {
        "2025 physical forecast": (
            OUTPUTS / "future_forecasting" /
            "forecast_2025_physical.npy"
        ),
        "2025 normalized forecast": (
            OUTPUTS / "future_forecasting" /
            "forecast_2025_normalized.npy"
        ),
        "Forecast integrity report": (
            OUTPUTS / "final_forecast_integrity" /
            "final_forecast_integrity_report.json"
        )
    },

    "Final reports": {
        "Master scientific report": (
            OUTPUTS / "master_scientific_validation" /
            "master_scientific_validation_report.md"
        ),
        "Master scientific JSON": (
            OUTPUTS / "master_scientific_validation" /
            "master_scientific_validation.json"
        ),
        "Master model metrics": (
            OUTPUTS / "master_scientific_validation" /
            "master_model_performance.csv"
        ),
        "Master trend summary": (
            OUTPUTS / "master_scientific_validation" /
            "master_historical_trend_summary.csv"
        )
    }
}

# ------------------------------------------------
# 3. CHECK ARTIFACT EXISTENCE
# ------------------------------------------------

artifact_results = []

for category, files in artifacts.items():

    for name, path in files.items():

        exists = path.exists()

        size_mb = (
            round(path.stat().st_size / (1024 * 1024), 3)
            if exists and path.is_file()
            else None
        )

        artifact_results.append({
            "Category": category,
            "Artifact": name,
            "Exists": exists,
            "Size_MB": size_mb,
            "Path": str(path)
        })

artifact_df = pd.DataFrame(artifact_results)

artifact_df.to_csv(
    AUDIT_DIR / "artifact_inventory.csv",
    index=False
)

# ------------------------------------------------
# 4. CHECK SUBMISSION DOCUMENTATION
# ------------------------------------------------

documentation_candidates = {
    "README": [
        ROOT / "README.md",
        ROOT / "README.txt"
    ],
    "Requirements": [
        ROOT / "requirements.txt"
    ],
    "License": [
        ROOT / "LICENSE",
        ROOT / "LICENSE.md"
    ],
    "Project description": [
        ROOT / "PROJECT_DESCRIPTION.md",
        ROOT / "docs" / "PROJECT_DESCRIPTION.md"
    ],
    "Methodology": [
        ROOT / "METHODOLOGY.md",
        ROOT / "docs" / "METHODOLOGY.md"
    ],
    "Data provenance": [
        ROOT / "DATA_SOURCES.md",
        ROOT / "docs" / "DATA_SOURCES.md"
    ],
    "Presentation": [
        ROOT / "presentation.pptx",
        ROOT / "NASA_Earth_Systems_Presentation.pptx"
    ]
}

documentation_results = {}

for name, candidates in documentation_candidates.items():

    found = [
        str(path.relative_to(ROOT))
        for path in candidates
        if path.exists()
    ]

    documentation_results[name] = {
        "found": bool(found),
        "paths": found
    }

# ------------------------------------------------
# 5. CHECK NOTEBOOKS AND SOURCE CODE
# ------------------------------------------------

notebooks = list(ROOT.rglob("*.ipynb"))

excluded_parts = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "node_modules"
}

notebooks = [
    p for p in notebooks
    if not any(part in excluded_parts for part in p.parts)
]

source_extensions = [
    "*.py", "*.js", "*.html", "*.css"
]

source_files = []

for extension in source_extensions:
    source_files.extend(ROOT.rglob(extension))

source_files = [
    p for p in source_files
    if not any(part in excluded_parts for part in p.parts)
]

code_inventory = {
    "notebook_count": len(notebooks),
    "notebooks": [
        str(p.relative_to(ROOT))
        for p in notebooks[:100]
    ],
    "source_file_count": len(source_files)
}

# ------------------------------------------------
# 6. READ FORECAST PHYSICAL VALIDITY
# ------------------------------------------------

forecast_integrity_path = (
    OUTPUTS / "final_forecast_integrity" /
    "final_forecast_integrity_report.json"
)

forecast_physical_valid = None
negative_precipitation_count = None
negative_precipitation_percentage = None

if forecast_integrity_path.exists():

    with open(forecast_integrity_path, "r") as f:
        forecast_report = json.load(f)

    precipitation = forecast_report[
        "precipitation_validation"
    ]

    forecast_physical_valid = precipitation[
        "physical_constraint_satisfied"
    ]

    negative_precipitation_count = precipitation[
        "negative_predictions"
    ]

    negative_precipitation_percentage = precipitation[
        "negative_percentage"
    ]

# ------------------------------------------------
# 7. CREATE READINESS CHECKLIST
# ------------------------------------------------

artifact_pass = bool(artifact_df["Exists"].all())

documentation_pass = all(
    item["found"]
    for item in documentation_results.values()
)

code_pass = (
    len(notebooks) > 0 and
    len(source_files) > 0
)

readiness_checks = {
    "all_core_artifacts_present": artifact_pass,
    "all_submission_documents_present": documentation_pass,
    "notebook_and_source_code_present": code_pass,
    "forecast_physical_constraints_satisfied": (
        forecast_physical_valid
    )
}

# ------------------------------------------------
# 8. IDENTIFY MISSING ITEMS
# ------------------------------------------------

missing_artifacts = artifact_df[
    ~artifact_df["Exists"]
]

missing_documentation = [
    name
    for name, result in documentation_results.items()
    if not result["found"]
]

recommendations = []

if not artifact_pass:
    recommendations.append(
        "Restore or regenerate missing core scientific artifacts."
    )

if "README" in missing_documentation:
    recommendations.append(
        "Create a README explaining the project, installation, "
        "dataset, methodology, results, and limitations."
    )

if "Requirements" in missing_documentation:
    recommendations.append(
        "Create a requirements.txt with tested dependency versions."
    )

if "Data provenance" in missing_documentation:
    recommendations.append(
        "Document NASA POWER variables, retrieval dates, "
        "spatial coverage, temporal coverage, and preprocessing."
    )

if "Methodology" in missing_documentation:
    recommendations.append(
        "Document graph construction, normalization, model architecture, "
        "training splits, evaluation, and trend tests."
    )

if "License" in missing_documentation:
    recommendations.append(
        "Choose an appropriate project license and verify dataset "
        "and dependency licensing before public release."
    )

if "Presentation" in missing_documentation:
    recommendations.append(
        "Prepare a concise judge-facing presentation with results, "
        "visualizations, limitations, and a live demo."
    )

if forecast_physical_valid is False:
    recommendations.append(
        "Disclose negative precipitation predictions. Do not silently "
        "overwrite the original forecast; consider a separately labelled "
        "physically constrained output for visualization."
    )

# ------------------------------------------------
# 9. BUILD AUDIT JSON
# ------------------------------------------------

audit = {
    "project": "NASA Earth Systems Trend Detective",
    "audit_type": "Final project readiness",
    "generated_at": datetime.now().isoformat(),
    "artifact_inventory": artifact_results,
    "documentation": documentation_results,
    "code_inventory": code_inventory,
    "readiness_checks": readiness_checks,
    "missing_artifacts": missing_artifacts[
        ["Category", "Artifact", "Path"]
    ].to_dict(orient="records"),
    "missing_documentation": missing_documentation,
    "forecast_physical_validity": forecast_physical_valid,
    "negative_precipitation_count": negative_precipitation_count,
    "negative_precipitation_percentage": (
        negative_precipitation_percentage
    ),
    "recommendations": recommendations
}

with open(
    AUDIT_DIR / "project_readiness_audit.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(audit, f, indent=4, default=str)

# ------------------------------------------------
# 10. GENERATE MARKDOWN REPORT
# ------------------------------------------------

lines = [
    "# NASA Earth Systems Trend Detective",
    "",
    "## Final Project Readiness Audit",
    "",
    f"Generated: {audit['generated_at']}",
    "",
    "## 1. Scientific Artifact Inventory",
    "",
    artifact_df[
        ["Category", "Artifact", "Exists", "Size_MB"]
    ].to_markdown(index=False),
    "",
    "## 2. Documentation Readiness",
    "",
    "| Document | Available |",
    "|---|---|"
]

for name, result in documentation_results.items():
    lines.append(
        f"| {name} | {'Yes' if result['found'] else 'No'} |"
    )

lines += [
    "",
    "## 3. Code Inventory",
    "",
    f"- Jupyter notebooks found: {len(notebooks)}",
    f"- Source files found: {len(source_files)}",
    "",
    "## 4. Readiness Checks",
    "",
    "| Check | Result |",
    "|---|---|"
]

for name, status in readiness_checks.items():
    if status is None:
        result = "NOT CHECKED"
    else:
        result = "PASS" if status else "FAIL"

    lines.append(
        f"| {name.replace('_', ' ').title()} | {result} |"
    )

lines += [
    "",
    "## 5. Missing Artifacts",
    ""
]

if missing_artifacts.empty:
    lines.append("No missing core artifacts were detected.")
else:
    for _, row in missing_artifacts.iterrows():
        lines.append(
            f"- {row['Category']}: {row['Artifact']}"
        )

lines += [
    "",
    "## 6. Missing Documentation",
    ""
]

if not missing_documentation:
    lines.append("All checked documentation files were found.")
else:
    for item in missing_documentation:
        lines.append(f"- {item}")

lines += [
    "",
    "## 7. Forecast Physical Constraint",
    "",
    f"- Physical validity: {forecast_physical_valid}",
    f"- Negative precipitation predictions: "
    f"{negative_precipitation_count}",
    f"- Percentage: {negative_precipitation_percentage}",
    "",
    "## 8. Recommended Actions",
    ""
]

if recommendations:
    for item in recommendations:
        lines.append(f"- {item}")
else:
    lines.append(
        "No additional actions were identified by this automated audit."
    )

lines += [
    "",
    "## 9. Submission Guidance",
    "",
    "Before submission, manually verify:",
    "",
    "- The NASA Space Apps challenge requirements are addressed.",
    "- All dataset sources and licenses are documented.",
    "- The project can be reproduced using documented commands.",
    "- Figures and metrics match the generated scientific reports.",
    "- The limitations are clearly communicated.",
    "- The demonstration works from a clean environment.",
    "- No credentials, API keys, or private data are committed.",
    "",
    "This automated audit checks file presence and selected validation "
    "conditions. It does not certify scientific correctness, deployment "
    "quality, or NASA Space Apps submission compliance.",
    ""
]

with open(
    AUDIT_DIR / "project_readiness_report.md",
    "w",
    encoding="utf-8"
) as f:
    f.write("\n".join(lines))

# ------------------------------------------------
# 11. PRINT FINAL AUDIT
# ------------------------------------------------

print("\n" + "=" * 75)
print("ARTIFACT INVENTORY")
print("=" * 75)

print(
    artifact_df[
        ["Category", "Artifact", "Exists"]
    ].to_string(index=False)
)

print("\n" + "=" * 75)
print("DOCUMENTATION STATUS")
print("=" * 75)

for name, result in documentation_results.items():
    print(
        f"{name}: "
        f"{'FOUND' if result['found'] else 'MISSING'}"
    )

print("\n" + "=" * 75)
print("FINAL READINESS CHECKS")
print("=" * 75)

for name, status in readiness_checks.items():

    if status is None:
        label = "NOT CHECKED"
    else:
        label = "PASS" if status else "FAIL"

    print(f"{name}: {label}")

print("\nRecommendations:")

for recommendation in recommendations:
    print("-", recommendation)

print("\nGenerated reports:")

for path in sorted(AUDIT_DIR.iterdir()):
    print(path.name)

print("\nAUDIT DIRECTORY:")
print(AUDIT_DIR)

print("\nCELL 34 COMPLETED")


# ============================================================
# ORIGINAL NOTEBOOK CELL 46
# Execution count: 55
# ============================================================

# ================================================================
# CELL 35: PROJECT STRUCTURE AND SUBMISSION FILE INSPECTION
# NASA EARTH SYSTEMS TREND DETECTIVE
# ================================================================

from pathlib import Path
import json

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

print("=" * 75)
print("CELL 35: PROJECT STRUCTURE INSPECTION")
print("=" * 75)

if not PROJECT_ROOT.exists():
    raise FileNotFoundError(f"Project folder not found: {PROJECT_ROOT}")

# ------------------------------------------------
# 1. TOP-LEVEL PROJECT CONTENTS
# ------------------------------------------------

print("\n[1] TOP-LEVEL PROJECT CONTENTS")

for path in sorted(PROJECT_ROOT.iterdir()):
    kind = "DIR " if path.is_dir() else "FILE"
    print(f"{kind}  {path.name}")

# ------------------------------------------------
# 2. NOTEBOOK DISCOVERY
# ------------------------------------------------

print("\n[2] JUPYTER NOTEBOOKS")

notebooks = [
    p for p in PROJECT_ROOT.rglob("*.ipynb")
    if not any(
        part in {".venv", "venv", "node_modules", "__pycache__"}
        for part in p.parts
    )
]

if notebooks:
    for p in notebooks:
        print(f"FOUND: {p.relative_to(PROJECT_ROOT)}")
else:
    print("No .ipynb files found.")

# ------------------------------------------------
# 3. SOURCE CODE DISCOVERY
# ------------------------------------------------

print("\n[3] SOURCE CODE FILES")

source_extensions = {
    ".py", ".js", ".mjs", ".cjs", ".html",
    ".css", ".ipynb", ".sh", ".bat"
}

excluded_dirs = {
    ".venv", "venv", "node_modules", "__pycache__",
    ".git", ".ipynb_checkpoints"
}

source_files = [
    p for p in PROJECT_ROOT.rglob("*")
    if p.is_file()
    and p.suffix.lower() in source_extensions
    and not any(part in excluded_dirs for part in p.parts)
]

for p in source_files[:150]:
    print(p.relative_to(PROJECT_ROOT))

print(f"\nTotal source/notebook files: {len(source_files)}")

if len(source_files) > 150:
    print(f"Additional files not displayed: {len(source_files) - 150}")

# ------------------------------------------------
# 4. DOCUMENTATION DISCOVERY
# ------------------------------------------------

print("\n[4] DOCUMENTATION FILES")

documentation_names = [
    "README.md",
    "requirements.txt",
    "LICENSE",
    "PROJECT_DESCRIPTION.md",
    "METHODOLOGY.md",
    "DATA_PROVENANCE.md",
    "PRESENTATION.pptx",
    "PRESENTATION.pdf"
]

for name in documentation_names:
    matches = list(PROJECT_ROOT.rglob(name))
    if matches:
        for p in matches:
            print(f"FOUND: {p.relative_to(PROJECT_ROOT)}")
    else:
        print(f"MISSING: {name}")

# ------------------------------------------------
# 5. README PREVIEW
# ------------------------------------------------

print("\n[5] README PREVIEW")

readme_path = PROJECT_ROOT / "README.md"

if readme_path.exists():
    print(readme_path.read_text(encoding="utf-8", errors="replace")[:5000])
else:
    print("README.md not found at project root.")

# ------------------------------------------------
# 6. REQUIREMENTS PREVIEW
# ------------------------------------------------

print("\n[6] REQUIREMENTS PREVIEW")

requirements_path = PROJECT_ROOT / "requirements.txt"

if requirements_path.exists():
    print(requirements_path.read_text(encoding="utf-8", errors="replace")[:5000])
else:
    print("requirements.txt not found at project root.")

# ------------------------------------------------
# 7. SAVE INSPECTION REPORT
# ------------------------------------------------

inspection = {
    "project_root": str(PROJECT_ROOT),
    "notebooks": [
        str(p.relative_to(PROJECT_ROOT)) for p in notebooks
    ],
    "source_files": [
        str(p.relative_to(PROJECT_ROOT)) for p in source_files
    ],
    "source_file_count": len(source_files),
    "documentation": {
        name: [
            str(p.relative_to(PROJECT_ROOT))
            for p in PROJECT_ROOT.rglob(name)
        ]
        for name in documentation_names
    }
}

output_dir = PROJECT_ROOT / "outputs" / "final_project_readiness"
output_dir.mkdir(parents=True, exist_ok=True)

report_path = output_dir / "cell35_project_structure.json"

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(inspection, f, indent=4)

print("\n" + "=" * 75)
print("CELL 35 COMPLETED")
print("=" * 75)
print(f"Notebook count: {len(notebooks)}")
print(f"Source/notebook file count: {len(source_files)}")
print(f"Inspection report: {report_path}")


# ============================================================
# ORIGINAL NOTEBOOK CELL 47
# Execution count: 56
# ============================================================

# ================================================================
# CELL 36: SCIENTIFIC IMPLEMENTATION AND DATA PROVENANCE INSPECTION
# ================================================================

from pathlib import Path
import json

ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

FILES_TO_INSPECT = [
    "README.md",
    "pyproject.toml",
    "package.json",
    "scientific-engine/config.py",
    "scientific-engine/constants.py",
    "scientific-engine/main.py",
    "scripts/download_all.py",
    "scripts/preprocess_all.py",
    "scripts/build_global_grid.py",
    "scripts/build_graph.py",
    "scripts/train_model.py",
    "scripts/evaluate_model.py",
    "scripts/run_trend_analysis.py",
    "scripts/generate_report.py",
    "configs",
    "data/processed/tensor_metadata.json",
    "data/processed/spatial_nodes.csv",
    "outputs/spatial_graph/graph_metadata.json",
    "outputs/model_training/gcn_gru_config.json",
    "outputs/model_training/training_report.json",
    "outputs/evaluation/evaluation_metrics_2024.csv",
    "outputs/historical_trend_analysis/feature_trend_summary.csv",
    "outputs/final_forecast_integrity/final_forecast_integrity_report.json",
]

MAX_CHARS = 6500

print("=" * 75)
print("CELL 36: IMPLEMENTATION INSPECTION")
print("=" * 75)

for relative_path in FILES_TO_INSPECT:
    path = ROOT / relative_path

    print("\n" + "=" * 75)
    print(f"FILE: {relative_path}")
    print("=" * 75)

    if not path.exists():
        print("NOT FOUND")
        continue

    if path.is_dir():
        files = sorted(
            p for p in path.rglob("*")
            if p.is_file()
            and not any(
                part in {".venv", "node_modules", "__pycache__"}
                for part in p.parts
            )
        )

        for p in files[:40]:
            print(p.relative_to(ROOT))

        if len(files) > 40:
            print(f"... {len(files) - 40} additional files")

        continue

    if path.suffix.lower() == ".csv":
        import pandas as pd

        df = pd.read_csv(path)
        print("Columns:", list(df.columns))
        print(df.head(8).to_string(index=False))
        print("Rows:", len(df))
        continue

    if path.suffix.lower() == ".json":
        try:
            content = json.loads(
                path.read_text(encoding="utf-8")
            )
            print(json.dumps(content, indent=2)[:MAX_CHARS])
        except Exception as exc:
            print("JSON read error:", exc)
        continue

    try:
        content = path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        if not content.strip():
            print("[EMPTY FILE]")
        else:
            print(content[:MAX_CHARS])

            if len(content) > MAX_CHARS:
                print("\n[TRUNCATED FOR DISPLAY]")

    except Exception as exc:
        print("Read error:", exc)

print("\n" + "=" * 75)
print("CELL 36 COMPLETED")
print("=" * 75)


# ============================================================
# ORIGINAL NOTEBOOK CELL 48
# Execution count: 57
# ============================================================

# ================================================================
# CELL 37: SOURCE CODE COMPLETENESS AND CONFIGURATION AUDIT
# ================================================================

from pathlib import Path
import subprocess

ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

print("=" * 75)
print("CELL 37: SOURCE CODE COMPLETENESS AUDIT")
print("=" * 75)

# ------------------------------------------------
# 1. CHECK IMPORTANT SOURCE FILE SIZES
# ------------------------------------------------

important_files = [
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "scientific-engine/config.py",
    "scientific-engine/constants.py",
    "scientific-engine/main.py",
    "scripts/download_all.py",
    "scripts/preprocess_all.py",
    "scripts/build_global_grid.py",
    "scripts/build_graph.py",
    "scripts/train_model.py",
    "scripts/evaluate_model.py",
    "scripts/run_trend_analysis.py",
    "scripts/generate_report.py",
    "backend/server.js",
    "backend/app.js",
    "frontend/index.html",
]

print("\n[1] IMPORTANT FILE SIZES")

for relative in important_files:
    path = ROOT / relative

    if not path.exists():
        print(f"MISSING | {relative}")
    else:
        size = path.stat().st_size
        status = "EMPTY" if size == 0 else "NONEMPTY"
        print(f"{status:8} | {size:10} bytes | {relative}")

# ------------------------------------------------
# 2. INSPECT CONFIGURATION FILES
# ------------------------------------------------

print("\n[2] CONFIGURATION FILE CONTENTS")

config_dir = ROOT / "configs"

if config_dir.exists():
    for path in sorted(config_dir.glob("*")):
        if not path.is_file():
            continue

        print("\n" + "-" * 65)
        print(f"CONFIG: {path.name}")
        print("-" * 65)

        content = path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        if content.strip():
            print(content[:5000])
        else:
            print("[EMPTY CONFIGURATION FILE]")

# ------------------------------------------------
# 3. CHECK GIT STATUS
# ------------------------------------------------

print("\n[3] GIT STATUS")

try:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20
    )

    print(result.stdout[:10000] or "No uncommitted changes reported.")

    if result.stderr:
        print("Git stderr:", result.stderr[:2000])

except Exception as exc:
    print("Git status could not be checked:", exc)

# ------------------------------------------------
# 4. CHECK TRACKED FILES
# ------------------------------------------------

print("\n[4] TRACKED SCIENTIFIC FILES")

try:
    result = subprocess.run(
        [
            "git", "ls-files",
            "README.md",
            "pyproject.toml",
            "package.json",
            "scientific-engine",
            "scripts",
            "configs"
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20
    )

    tracked = [
        line for line in result.stdout.splitlines()
        if line.strip()
    ]

    for item in tracked[:100]:
        print(item)

    print("Tracked files displayed:", min(len(tracked), 100))
    print("Total tracked matching files:", len(tracked))

except Exception as exc:
    print("Git file listing failed:", exc)

# ------------------------------------------------
# 5. SUMMARY
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 37 COMPLETED")
print("=" * 75)


# ============================================================
# ORIGINAL NOTEBOOK CELL 49
# Execution count: 58
# ============================================================

# ================================================================
# CELL 38: ORIGINAL NOTEBOOK AND SOURCE RECOVERY DISCOVERY
# ================================================================

from pathlib import Path
import subprocess

ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

SEARCH_ROOT = ROOT.parent

EXCLUDED = {
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".git",
    "site-packages"
}

print("=" * 75)
print("CELL 38: ORIGINAL NOTEBOOK AND SOURCE RECOVERY")
print("=" * 75)

# ------------------------------------------------
# 1. SEARCH FOR NOTEBOOKS IN NASA PROJECT PARENT
# ------------------------------------------------

print("\n[1] JUPYTER NOTEBOOK SEARCH")

notebooks = []

for path in SEARCH_ROOT.rglob("*.ipynb"):
    if not any(part in EXCLUDED for part in path.parts):
        notebooks.append(path)

if notebooks:
    for path in sorted(notebooks):
        print(
            f"{path.stat().st_size:12,} bytes | "
            f"{path}"
        )
else:
    print("No notebooks found in the NASA parent directory.")

# ------------------------------------------------
# 2. INSPECT ALL PYTHON SOURCE FILES
# ------------------------------------------------

print("\n[2] PYTHON SOURCE FILE STATUS")

python_files = [
    p for p in ROOT.rglob("*.py")
    if not any(part in EXCLUDED for part in p.parts)
]

empty_python = []
nonempty_python = []

for path in python_files:
    if path.stat().st_size == 0:
        empty_python.append(path)
    else:
        nonempty_python.append(path)

print("Total Python files:", len(python_files))
print("Empty Python files:", len(empty_python))
print("Non-empty Python files:", len(nonempty_python))

print("\nNON-EMPTY PYTHON FILES:")

for path in sorted(nonempty_python):
    print(
        f"{path.stat().st_size:10,} bytes | "
        f"{path.relative_to(ROOT)}"
    )

# ------------------------------------------------
# 3. INSPECT OTHER SOURCE FILES
# ------------------------------------------------

print("\n[3] OTHER SOURCE FILE STATUS")

extensions = {
    ".js", ".mjs", ".cjs", ".html", ".css",
    ".yaml", ".yml", ".toml"
}

other_files = [
    p for p in ROOT.rglob("*")
    if p.is_file()
    and p.suffix.lower() in extensions
    and not any(part in EXCLUDED for part in p.parts)
]

empty_other = [
    p for p in other_files if p.stat().st_size == 0
]

nonempty_other = [
    p for p in other_files if p.stat().st_size > 0
]

print("Total other source/config files:", len(other_files))
print("Empty files:", len(empty_other))
print("Non-empty files:", len(nonempty_other))

print("\nNON-EMPTY SOURCE/CONFIG FILES:")

for path in sorted(nonempty_other)[:100]:
    print(
        f"{path.stat().st_size:10,} bytes | "
        f"{path.relative_to(ROOT)}"
    )

# ------------------------------------------------
# 4. CHECK GIT HISTORY
# ------------------------------------------------

print("\n[4] GIT HISTORY")

commands = [
    ["git", "rev-parse", "--is-inside-work-tree"],
    ["git", "log", "--oneline", "-10"],
    ["git", "branch", "-a"],
    ["git", "remote", "-v"]
]

for command in commands:
    print("\nCOMMAND:", " ".join(command))

    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15
        )

        print(result.stdout.strip() or "[NO OUTPUT]")

        if result.stderr.strip():
            print("ERROR:", result.stderr.strip()[:1000])

    except Exception as exc:
        print("Could not execute:", exc)

# ------------------------------------------------
# 5. CHECK RECENTLY MODIFIED PROJECT FILES
# ------------------------------------------------

print("\n[5] RECENTLY MODIFIED NON-EMPTY FILES")

all_files = [
    p for p in ROOT.rglob("*")
    if p.is_file()
    and not any(part in EXCLUDED for part in p.parts)
    and p.stat().st_size > 0
]

recent_files = sorted(
    all_files,
    key=lambda p: p.stat().st_mtime,
    reverse=True
)

for path in recent_files[:30]:
    print(
        f"{path.stat().st_size:10,} bytes | "
        f"{path.relative_to(ROOT)}"
    )

# ------------------------------------------------
# 6. FINAL SUMMARY
# ------------------------------------------------

print("\n" + "=" * 75)
print("CELL 38 COMPLETED")
print("=" * 75)

print("Notebooks discovered:", len(notebooks))
print("Non-empty Python files:", len(nonempty_python))
print("Non-empty other source/config files:", len(nonempty_other))
print("Non-empty project files:", len(all_files))


# ============================================================
# ORIGINAL NOTEBOOK CELL 50
# Execution count: 59
# ============================================================

# ================================================================
# CELL 39: RECOVERED NOTEBOOK STRUCTURAL ANALYSIS
# ================================================================

from pathlib import Path
import json
import ast
import re

NOTEBOOK_PATH = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\model.ipynb"
)

OUTPUT_DIR = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa"
) / "earth-systems-trend-detective" / "outputs" / "source_recovery"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 75)
print("CELL 39: RECOVERED NOTEBOOK ANALYSIS")
print("=" * 75)

if not NOTEBOOK_PATH.exists():
    raise FileNotFoundError(NOTEBOOK_PATH)

with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
    notebook = json.load(f)

cells = notebook.get("cells", [])

code_cells = []
markdown_cells = []

for index, cell in enumerate(cells):
    source = cell.get("source", [])

    if isinstance(source, list):
        source = "".join(source)

    if cell.get("cell_type") == "code" and source.strip():
        code_cells.append((index, source))

    elif cell.get("cell_type") == "markdown" and source.strip():
        markdown_cells.append((index, source))

print("\n[1] NOTEBOOK METADATA")
print("Notebook:", NOTEBOOK_PATH)
print("Notebook size (MB):", round(NOTEBOOK_PATH.stat().st_size / 1024**2, 2))
print("Total cells:", len(cells))
print("Non-empty code cells:", len(code_cells))
print("Non-empty markdown cells:", len(markdown_cells))
print("Kernel:", notebook.get("metadata", {}).get("kernelspec", {}))

# ------------------------------------------------
# 2. MARKDOWN HEADINGS
# ------------------------------------------------

print("\n[2] NOTEBOOK SECTION HEADINGS")

headings = []

for index, source in markdown_cells:
    for line in source.splitlines():
        line = line.strip()

        if re.match(r"^#{1,6}\s+", line):
            headings.append({
                "cell": index,
                "heading": line
            })
            print(f"Cell {index}: {line}")

# ------------------------------------------------
# 3. CODE CELL STRUCTURE
# ------------------------------------------------

print("\n[3] CODE CELL INVENTORY")

cell_inventory = []
all_imports = set()
all_definitions = []
syntax_errors = []

for index, source in code_cells:
    lines = source.splitlines()

    imports = []
    definitions = []
    syntax_error = None

    try:
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definitions.append(
                    f"function: {node.name} (line {node.lineno})"
                )

            elif isinstance(node, ast.ClassDef):
                definitions.append(
                    f"class: {node.name} (line {node.lineno})"
                )

    except SyntaxError as exc:
        syntax_error = (
            f"{exc.msg}, line {exc.lineno}"
        )
        syntax_errors.append({
            "cell": index,
            "error": syntax_error
        })

    all_imports.update(imports)

    all_definitions.extend([
        {
            "cell": index,
            "definition": item
        }
        for item in definitions
    ])

    cell_inventory.append({
        "cell": index,
        "line_count": len(lines),
        "character_count": len(source),
        "imports": sorted(set(imports)),
        "definitions": definitions,
        "syntax_error": syntax_error
    })

    print(
        f"Cell {index:3} | "
        f"{len(lines):5} lines | "
        f"{len(source):7} characters | "
        f"Definitions: {len(definitions)}"
    )

    for definition in definitions:
        print("    ", definition)

    if syntax_error:
        print("     SYNTAX ISSUE:", syntax_error)

# ------------------------------------------------
# 4. IMPORTANT SCIENTIFIC COMPONENT SEARCH
# ------------------------------------------------

print("\n[4] SCIENTIFIC IMPLEMENTATION KEYWORD SEARCH")

keywords = [
    "GCNGRU",
    "GCN-GRU",
    "class GCN",
    "GRU",
    "BallTree",
    "haversine",
    "adjacency",
    "normalized_adjacency",
    "Gaussian",
    "DataLoader",
    "AdamW",
    "ReduceLROnPlateau",
    "persistence",
    "autoregressive",
    "Sen slope",
    "seasonal",
    "Mann-Kendall",
    "TFPW",
    "NASA POWER",
    "POWER"
]

for keyword in keywords:
    matching_cells = []

    for index, source in code_cells:
        if keyword.lower() in source.lower():
            matching_cells.append(index)

    print(
        f"{keyword:25} : "
        f"{matching_cells[:30]}"
    )

# ------------------------------------------------
# 5. IMPORT INVENTORY
# ------------------------------------------------

print("\n[5] IMPORTED LIBRARIES")

for name in sorted(all_imports):
    print(name)

# ------------------------------------------------
# 6. OUTPUT AND EXECUTION COUNTS
# ------------------------------------------------

print("\n[6] NOTEBOOK EXECUTION INFORMATION")

execution_counts = []
output_count = 0

for index, cell in enumerate(cells):
    if cell.get("cell_type") != "code":
        continue

    execution_counts.append(
        cell.get("execution_count")
    )

    output_count += len(cell.get("outputs", []))

executed = sum(
    value is not None for value in execution_counts
)

print("Executed code cells:", executed)
print("Code cells with outputs:", output_count)
print("Syntax errors:", len(syntax_errors))

# ------------------------------------------------
# 7. SAVE STRUCTURAL REPORT
# ------------------------------------------------

report = {
    "notebook_path": str(NOTEBOOK_PATH),
    "total_cells": len(cells),
    "code_cells": len(code_cells),
    "markdown_cells": len(markdown_cells),
    "headings": headings,
    "cell_inventory": cell_inventory,
    "imports": sorted(all_imports),
    "definitions": all_definitions,
    "syntax_errors": syntax_errors,
    "executed_code_cells": executed,
    "output_count": output_count
}

report_path = OUTPUT_DIR / "notebook_structure_report.json"

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=4)

print("\n" + "=" * 75)
print("CELL 39 COMPLETED")
print("=" * 75)
print("Structural report:", report_path)


# ============================================================
# ORIGINAL NOTEBOOK CELL 51
# Execution count: 60
# ============================================================


# ================================================================
# CELL 40: INSPECT ORIGINAL NOTEBOOK SETUP AND DATA PIPELINE
# ================================================================

import json
import re
from pathlib import Path

NOTEBOOK_PATH = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\model.ipynb"
)

with NOTEBOOK_PATH.open("r", encoding="utf-8") as f:
    notebook = json.load(f)

def redact_sensitive_text(text):
    """Mask common credentials before displaying notebook source."""

    patterns = [
        r'(?i)(api[_-]?key|access[_-]?token|secret|password|client[_-]?secret)'
        r'(\s*[:=]\s*)["\'][^"\']+["\']',

        r'(?i)(Bearer\s+)[A-Za-z0-9._\-]+',

        r'(?i)(https?://[^?\s]+)\?[^ \n]+',
    ]

    for pattern in patterns:
        text = re.sub(
            pattern,
            lambda m: (
                m.group(1)
                + (m.group(2) if m.lastindex and m.lastindex >= 2 else "")
                + "[REDACTED]"
            ),
            text
        )

    return text


print("=" * 75)
print("CELL 40: ORIGINAL NOTEBOOK SOURCE INSPECTION")
print("=" * 75)

for cell_index in range(0, 7):

    cell = notebook["cells"][cell_index]

    source = cell.get("source", "")
    if isinstance(source, list):
        source = "".join(source)

    source = redact_sensitive_text(source)

    print("\n" + "=" * 75)
    print(f"ORIGINAL NOTEBOOK CELL {cell_index}")
    print("=" * 75)

    lines = source.splitlines()

    # Limit display to avoid flooding the notebook output.
    max_lines = 100

    for line_number, line in enumerate(lines[:max_lines], start=1):
        print(f"{line_number:03d}: {line}")

    if len(lines) > max_lines:
        print(
            f"\n... {len(lines) - max_lines} additional lines omitted."
        )

    print(f"\nTotal lines: {len(lines)}")

print("\n" + "=" * 75)
print("CELL 40 COMPLETED")
print("=" * 75)


# ============================================================
# ORIGINAL NOTEBOOK CELL 52
# Execution count: None
# ============================================================


# ================================================================
# CELL 41: EXPORT ORIGINAL NOTEBOOK SOURCE
# ================================================================

import json
import hashlib
from pathlib import Path
from datetime import datetime

# ------------------------------------------------
# 1. PATHS
# ------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective"
)

NOTEBOOK_PATH = Path(
    r"C:\Users\piyus\OneDrive\Desktop\nasa\model.ipynb"
)

RECOVERY_DIR = PROJECT_ROOT / "outputs" / "source_recovery"
RECOVERY_DIR.mkdir(parents=True, exist_ok=True)

PYTHON_EXPORT = RECOVERY_DIR / "recovered_notebook_source.py"
JSON_EXPORT = RECOVERY_DIR / "notebook_code_archive.json"

# ------------------------------------------------
# 2. VERIFY ORIGINAL NOTEBOOK
# ------------------------------------------------

if not NOTEBOOK_PATH.exists():
    raise FileNotFoundError(
        f"Original notebook not found: {NOTEBOOK_PATH}"
    )

original_bytes = NOTEBOOK_PATH.read_bytes()
original_hash_before = hashlib.sha256(original_bytes).hexdigest()

with NOTEBOOK_PATH.open("r", encoding="utf-8") as f:
    notebook = json.load(f)

# ------------------------------------------------
# 3. COLLECT CODE CELLS WITHOUT EXECUTING THEM
# ------------------------------------------------

code_cells = []
python_parts = []

for index, cell in enumerate(notebook.get("cells", [])):

    if cell.get("cell_type") != "code":
        continue

    source = cell.get("source", "")

    if isinstance(source, list):
        source = "".join(source)

    if not source.strip():
        continue

    execution_count = cell.get("execution_count")

    code_cells.append({
        "cell_index": index,
        "execution_count": execution_count,
        "source": source
    })

    python_parts.append(
        f"\n# ============================================================\n"
        f"# ORIGINAL NOTEBOOK CELL {index}\n"
        f"# Execution count: {execution_count}\n"
        f"# ============================================================\n\n"
        f"{source.rstrip()}\n"
    )

# ------------------------------------------------
# 4. WRITE PYTHON SOURCE ARCHIVE
# ------------------------------------------------

header = (
    "# RECOVERED SOURCE ARCHIVE\n"
    "# Source: model.ipynb\n"
    "# This is an archival export, not a standalone executable script.\n"
    "# Jupyter magics and notebook-dependent variables may remain.\n"
    "# Review credentials and paths before sharing or committing.\n\n"
)

PYTHON_EXPORT.write_text(
    header + "\n".join(python_parts),
    encoding="utf-8"
)

# ------------------------------------------------
# 5. WRITE STRUCTURED JSON ARCHIVE
# ------------------------------------------------

archive = {
    "source_notebook": str(NOTEBOOK_PATH),
    "project_root": str(PROJECT_ROOT),
    "export_timestamp": datetime.now().isoformat(),
    "notebook_sha256": original_hash_before,
    "total_notebook_cells": len(notebook.get("cells", [])),
    "exported_code_cells": len(code_cells),
    "cells": code_cells
}

JSON_EXPORT.write_text(
    json.dumps(archive, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# ------------------------------------------------
# 6. VERIFY EXPORT AND ORIGINAL NOTEBOOK
# ------------------------------------------------

exported_bytes = PYTHON_EXPORT.read_bytes()
json_bytes = JSON_EXPORT.read_bytes()

original_hash_after = hashlib.sha256(
    NOTEBOOK_PATH.read_bytes()
).hexdigest()

assert original_hash_before == original_hash_after
assert len(code_cells) == len(python_parts)
assert len(code_cells) > 0
assert PYTHON_EXPORT.exists()
assert JSON_EXPORT.exists()

# Reopen JSON archive and verify cell count.
with JSON_EXPORT.open("r", encoding="utf-8") as f:
    verification_archive = json.load(f)

assert len(verification_archive["cells"]) == len(code_cells)

# ------------------------------------------------
# 7. REPORT
# ------------------------------------------------

print("=" * 75)
print("CELL 41: NOTEBOOK SOURCE RECOVERY")
print("=" * 75)

print("Original notebook:", NOTEBOOK_PATH)
print("Original SHA256:", original_hash_before)

print("\nExported code cells:", len(code_cells))
print("Python archive size:", len(exported_bytes), "bytes")
print("JSON archive size:", len(json_bytes), "bytes")

print("\nPython source archive:")
print(PYTHON_EXPORT)

print("\nStructured JSON archive:")
print(JSON_EXPORT)

print("\nOriginal notebook unchanged:",
      original_hash_before == original_hash_after)

print("JSON archive verified:",
      len(verification_archive["cells"]) == len(code_cells))

print("\nCELL 41 COMPLETED")
print("=" * 75)
