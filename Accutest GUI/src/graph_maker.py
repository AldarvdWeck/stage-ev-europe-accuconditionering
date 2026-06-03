import shutil
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, date2num
from matplotlib.lines import Line2D


COMBINED_PLOT_TITLE = "Temperatuur spanning test"
DEFAULT_SENSOR_LABELS = {
    "sensor1": "Sensor 1",
    "sensor2": "Sensor 2",
    "sensor3": "Sensor 3",
    "sensor4": "Sensor 4",
}


def _safe_filename(title: str, default_name: str = COMBINED_PLOT_TITLE) -> str:
    name = title.strip() or default_name
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", "_", name)
    name = name.strip("._ ")

    if not name:
        name = default_name.replace(" ", "_")

    return name


@dataclass
class GraphResult:
    output_folder: Path
    graph_path: Path
    data_folder: Path
    combined_csv_path: Path


def _parse_time(value, name: str) -> pd.Timestamp:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"{name} is geen geldige datum/tijd: {value}")
    return parsed


def _find_file(folder: Path, names: list[str]) -> Path:
    for name in names:
        path = folder / name
        if path.exists():
            return path
    lowered = {name.lower() for name in names}
    for path in folder.iterdir():
        if path.is_file() and path.name.lower() in lowered:
            return path
    raise FileNotFoundError(f"Bestand niet gevonden in {folder}: {', '.join(names)}")


def read_voltage_times_from_mode(voltage_file: Path) -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Bepaal start- en eindtijd op basis van de BATT-periode
    in het elektriciteitsbestand.
    """
    df = pd.read_csv(voltage_file)
    df.columns = [col.strip() for col in df.columns]

    if "MODE" not in df.columns:
        raise ValueError("Elektriciteitsmeting bevat geen MODE-kolom.")

    if "TIME" in df.columns:
        time_col = "TIME"
    elif "time" in df.columns:
        time_col = "time"
    elif "Time" in df.columns:
        time_col = "Time"
    else:
        raise ValueError("Elektriciteitsmeting bevat geen TIME-kolom.")

    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col, "MODE"]).sort_values(time_col)

    df["MODE_clean"] = df["MODE"].astype(str).str.strip().str.upper()

    batt_rows = df[df["MODE_clean"] == "BATT"]

    if batt_rows.empty:
        raise ValueError("Geen MODE='BATT' gevonden in elektriciteitsmeting.")

    start_time = batt_rows.iloc[0][time_col]
    end_time = batt_rows.iloc[-1][time_col]

    return start_time, end_time


def read_sensor_labels(test_conditions_file: Path) -> dict[str, str]:
    """
    Leest alleen de namen/locaties van de sensoren uit testcondities.csv.
    Deze functie gebruikt dus GEEN gestart/gestopt status.
    """
    labels = DEFAULT_SENSOR_LABELS.copy()

    try:
        df = pd.read_csv(test_conditions_file)
    except Exception:
        return labels

    df.columns = [col.strip() for col in df.columns]

    if df.empty:
        return labels

    row = df.iloc[0]

    for i in range(1, 5):
        col = f"locsensor{i}"

        if col in df.columns:
            value = str(row.get(col, "")).strip()

            if value and value.lower() != "nan":
                labels[f"sensor{i}"] = value

    return labels


def read_test_times_or_fallback(test_conditions_file: Path, voltage_file: Path) -> tuple[pd.Timestamp, pd.Timestamp, dict[str, str]]:
    """Try to read test times from testcondities.csv with 'gestart'/'gestopt' markers.
    If not found, fall back to determining times from voltage file MODE transitions."""
    try:
        # Try primary method: read from testcondities markers
        return read_test_times(test_conditions_file)
    except (ValueError, KeyError) as e:
        try:
            # Fallback: use voltage MODE BAT transitions
            start_time, end_time = read_voltage_times_from_mode(voltage_file)
            labels = DEFAULT_SENSOR_LABELS.copy()
            # Try to extract sensor labels from testcondities if available
            try:
                df = pd.read_csv(test_conditions_file)
                df.columns = [col.strip() for col in df.columns]
                if len(df) > 0:
                    for i in range(1, 5):
                        col = f"locsensor{i}"
                        if col in df.columns:
                            value = str(df.iloc[0].get(col, "")).strip()
                            if value and value.lower() != "nan":
                                labels[f"sensor{i}"] = value
            except:
                pass
            return start_time, end_time, labels
        except Exception as fallback_error:
            raise ValueError(
                f"Kan testcondities niet bepalen.\n"
                f"Primaire methode (testcondities.csv met 'gestart'/'gestopt'): {str(e)}\n"
                f"Fallback methode (MODE BATT→OFF in spanning): {str(fallback_error)}"
            )



def load_voltage_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [col.strip() for col in df.columns]

    if "TIME" in df.columns:
        time_col = "TIME"
    elif "time" in df.columns:
        time_col = "time"
    else:
        raise ValueError("Geen tijdkolom gevonden in voltage-bestand.")

    if "VOLTage(V)" in df.columns:
        voltage_col = "VOLTage(V)"
    elif "Voltage" in df.columns:
        voltage_col = "Voltage"
    else:
        raise ValueError("Geen voltagekolom gevonden in voltage-bestand.")

    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col, voltage_col])
    df = df.sort_values(by=time_col)
    df = df.drop_duplicates(subset=[time_col, voltage_col])
    return df[[time_col, voltage_col]].rename(columns={time_col: "time", voltage_col: "voltage"})


def load_sensor_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [col.strip() for col in df.columns]

    if "timestamp" not in df.columns:
        raise ValueError("Geen timestampkolom gevonden in metingen-bestand.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    sensor_cols = [col for col in df.columns if col.lower().startswith("sensor")]

    if not sensor_cols:
        raise ValueError("Geen sensor-kolommen gevonden in metingen-bestand.")

    df = df.dropna(subset=["timestamp"] + sensor_cols)
    df = df.sort_values(by="timestamp")
    df = df.drop_duplicates(subset=["timestamp"] + sensor_cols)
    return df.rename(columns={"timestamp": "time"})[["time"] + sensor_cols]


def plot_voltage(df: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df["voltage"], linestyle="-", color="tab:blue")
    plt.title("Voltage over tijd")
    plt.xlabel("Tijd")
    plt.ylabel("Voltage (V)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_sensors(df: pd.DataFrame, output_path: Path, sensor_labels: dict[str, str]) -> None:
    plt.figure(figsize=(12, 6))
    for sensor in df.columns:
        if sensor == "time":
            continue
        plt.plot(df["time"], df[sensor], linestyle="-", label=sensor_labels.get(sensor, sensor))

    plt.title("Temperatuur van vier sensoren over tijd")
    plt.xlabel("Tijd")
    plt.ylabel("Temperatuur (°C)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_combined_measurements(df: pd.DataFrame, output_path: Path, sensor_labels: dict[str, str], title: str) -> None:
    fig, ax1 = plt.subplots(figsize=(14, 7))
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.9)#0.98

    red_colors = ["#8B0000", "#B22222", "#DC143C", "#FF6347"]
    sensor_cols = ["sensor1", "sensor2", "sensor3", "sensor4"]

    for idx, sensor in enumerate(sensor_cols):
        ax1.plot(df["time"], df[sensor], linestyle="-", color=red_colors[idx], label=sensor_labels.get(sensor, sensor))

    ax1.set_xlabel("Tijd", color="black")
    ax1.set_ylabel("Temperatuur (°C)", color="black")
    ax1.tick_params(axis="y", labelcolor="black")
    ax1.tick_params(axis="x", labelcolor="black")
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    ax2 = ax1.twinx()
    ax2.plot(df["time"], df["Voltage"], linestyle="-", color="tab:blue", label="Spanning")
    ax2.set_ylabel("Spanning (V)", color="black")
    ax2.tick_params(axis="y", labelcolor="black")

    temp_min = df[sensor_cols].min().min()
    temp_max = df[sensor_cols].max().max()
    volt_min = df["Voltage"].min()
    volt_max = df["Voltage"].max()
    time_min = df["time"].min()
    time_max = df["time"].max()

    current_xlim = ax1.get_xlim()
    extra_xticks = [date2num(time_min), date2num(time_max)]
    extra_xticks = [tick for tick in extra_xticks if current_xlim[0] <= tick <= current_xlim[1]]
    ax1.set_xticks(sorted(set(list(ax1.get_xticks()) + extra_xticks)))

    current_y1 = ax1.get_yticks()
    extra_y1 = [tick for tick in [temp_min, temp_max] if current_y1.min() <= tick <= current_y1.max()]
    ax1.set_yticks(sorted(set(list(current_y1) + extra_y1)))

    current_y2 = ax2.get_yticks()
    extra_y2 = [tick for tick in [volt_min, volt_max] if current_y2.min() <= tick <= current_y2.max()]
    ax2.set_yticks(sorted(set(list(current_y2) + extra_y2)))

    legend_handles = [
        Line2D(
            [0], [0],
            color=red_colors[idx],
            marker="o",
            linestyle="-",
            markersize=6,
            markerfacecolor=red_colors[idx],
            label=sensor_labels.get(sensor, sensor),
        )
        for idx, sensor in enumerate(sensor_cols)
    ]
    legend_handles.append(
        Line2D([0], [0], color="tab:blue", marker="o", linestyle="-", markersize=6, markerfacecolor="tab:blue", label="Spanning")
    )

    ax1.legend(
        legend_handles,
        [h.get_label() for h in legend_handles],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.14),
        ncol=5,
        frameon=True,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.autofmt_xdate()
    fig.savefig(output_path)
    plt.close(fig)


def load_sensor_rows_per_elapsed_second(csv_path: Path, start_time, end_time) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [col.strip() for col in df.columns]

    if "timestamp" not in df.columns:
        raise ValueError("Geen timestampkolom gevonden in metingen-bestand.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    sensor_cols = [col for col in df.columns if col.lower().startswith("sensor")]

    if not sensor_cols:
        raise ValueError("Geen sensor-kolommen gevonden in metingen-bestand.")

    start = _parse_time(start_time, "SENSOR_COPY_START")
    end = _parse_time(end_time, "SENSOR_COPY_END")

    df = df.dropna(subset=["timestamp"] + sensor_cols)
    df = df[df["timestamp"] >= start].copy()
    df = df[df["timestamp"] <= end].copy()

    df["elapsed_seconds"] = ((df["timestamp"] - start).dt.total_seconds()).astype(int)
    df = df[df["elapsed_seconds"] >= 0].copy()
    df = df.sort_values(by=["elapsed_seconds", "timestamp"])
    df = df.drop_duplicates(subset=["elapsed_seconds"], keep="first")
    df["time"] = start + pd.to_timedelta(df["elapsed_seconds"], unit="s")

    return df[["elapsed_seconds", "time"] + sensor_cols]


def load_voltage_rows_per_elapsed_second(csv_path: Path, start_time, end_time) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [col.strip() for col in df.columns]

    if "TIME" in df.columns:
        time_col = "TIME"
    elif "time" in df.columns:
        time_col = "time"
    else:
        raise ValueError("Geen tijdkolom gevonden in voltage-bestand.")

    if "VOLTage(V)" in df.columns:
        voltage_col = "VOLTage(V)"
    elif "Voltage" in df.columns:
        voltage_col = "Voltage"
    else:
        raise ValueError("Geen voltagekolom gevonden in voltage-bestand.")

    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    start = _parse_time(start_time, "VOLTAGE_COPY_START")
    end = _parse_time(end_time, "VOLTAGE_COPY_END")

    df = df.dropna(subset=[time_col, voltage_col])
    df = df[df[time_col] >= start].copy()
    df = df[df[time_col] <= end].copy()

    df["elapsed_seconds"] = ((df[time_col] - start).dt.total_seconds()).astype(int)
    df = df[df["elapsed_seconds"] >= 0].copy()
    df = df.sort_values(by=["elapsed_seconds", time_col])
    df = df.drop_duplicates(subset=["elapsed_seconds"], keep="first")

    return df[["elapsed_seconds", voltage_col]].rename(columns={voltage_col: "Voltage"})


def create_combined_csv(
    sensor_file: Path,
    voltage_file: Path,
    output_file: Path,
    sensor_start,
    sensor_end,
    voltage_start,
    voltage_end,
) -> pd.DataFrame:
    sensor_df = load_sensor_rows_per_elapsed_second(sensor_file, sensor_start, sensor_end)
    voltage_df = load_voltage_rows_per_elapsed_second(voltage_file, voltage_start, voltage_end)

    combined = pd.merge(sensor_df, voltage_df, on="elapsed_seconds", how="inner")
    combined = combined.sort_values(by="elapsed_seconds").reset_index(drop=True)

    if combined.empty:
        raise ValueError("Geen overlappende seconden gevonden tussen temperatuur- en spanningsmeting.")

    combined["Time"] = combined["time"].dt.strftime("%Y/%m/%d %H:%M:%S")
    combined.to_csv(
        output_file,
        index=False,
        columns=["Time", "elapsed_seconds", "sensor1", "sensor2", "sensor3", "sensor4", "Voltage"],
    )

    return combined


def make_graph_from_files(temperature_folder: Path, voltage_file: Path, output_base_dir: Path, title: str = COMBINED_PLOT_TITLE) -> GraphResult:
    temperature_folder = Path(temperature_folder)
    voltage_file = Path(voltage_file)
    output_base_dir = Path(output_base_dir)

    if not temperature_folder.exists() or not temperature_folder.is_dir():
        raise FileNotFoundError("De gekozen temperatuurmeting is geen geldige folder.")
    if not voltage_file.exists() or not voltage_file.is_file():
        raise FileNotFoundError("Het gekozen elektriciteitsbestand bestaat niet.")
    if not output_base_dir.exists() or not output_base_dir.is_dir():
        raise FileNotFoundError("De gekozen opslaglocatie bestaat niet.")

    sensor_file = _find_file(temperature_folder, ["metingen.csv"])
    test_conditions_file = _find_file(temperature_folder, ["testcondities.csv"])

    # # Use flexible time detection: try testcondities markers first, then fallback to voltage MODE
    # sensor_start, sensor_end, sensor_labels = read_test_times_or_fallback(test_conditions_file, voltage_file)
    
    # # Times are now synchronized - use same timestamps for both measurements
    # voltage_start = sensor_start
    # voltage_end = sensor_end
    
    # Bepaal de testperiode uit het elektriciteitsbestand:
    # vanaf de eerste BATT-regel tot de laatste BATT-regel.
    # De BATT-periode uit het elektriciteitsbestand is leidend.
    batt_start, batt_end = read_voltage_times_from_mode(voltage_file)

    # testcondities.csv wordt alleen gebruikt voor de sensornamen.
    sensor_labels = read_sensor_labels(test_conditions_file)

    # Gebruik dezelfde absolute tijden voor beide metingen.
    # De tijden van temperatuur en elektriciteit lopen volgens jou gelijk.
    sensor_start = batt_start
    sensor_end = batt_end
    voltage_start = batt_start
    voltage_end = batt_end

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_folder = output_base_dir / f"accu_meting_{timestamp}"
    data_folder = output_folder / "meetdata"
    output_folder.mkdir(parents=True, exist_ok=False)
    data_folder.mkdir(parents=True, exist_ok=True)

    copied_sensor_file = data_folder / "metingen.csv"
    copied_test_conditions_file = data_folder / "testcondities.csv"
    copied_voltage_file = data_folder / voltage_file.name
    shutil.copy2(sensor_file, copied_sensor_file)
    shutil.copy2(test_conditions_file, copied_test_conditions_file)
    shutil.copy2(voltage_file, copied_voltage_file)

    settings_path = data_folder / "grafiek_instellingen.csv"
    pd.DataFrame([
        {"naam": "SENSOR_COPY_START", "waarde": sensor_start.strftime("%Y/%m/%d %H:%M:%S")},
        {"naam": "SENSOR_COPY_END", "waarde": sensor_end.strftime("%Y/%m/%d %H:%M:%S")},
        {"naam": "VOLTAGE_COPY_START", "waarde": voltage_start.strftime("%Y/%m/%d %H:%M:%S")},
        {"naam": "VOLTAGE_COPY_END", "waarde": voltage_end.strftime("%Y/%m/%d %H:%M:%S")},
    ]).to_csv(settings_path, index=False)

    voltage_df = load_voltage_data(voltage_file)
    sensor_df = load_sensor_data(sensor_file)
    plot_voltage(voltage_df, data_folder / "spanning_plot.png")
    plot_sensors(sensor_df, data_folder / "temperatuur_plot.png", sensor_labels)

    combined_csv_path = data_folder / "combined_measurements.csv"
    combined_df = create_combined_csv(
        sensor_file=sensor_file,
        voltage_file=voltage_file,
        output_file=combined_csv_path,
        sensor_start=sensor_start,
        sensor_end=sensor_end,
        voltage_start=voltage_start,
        voltage_end=voltage_end,
    )

    graph_filename = f"{_safe_filename(title)}.png"
    graph_path = output_folder / graph_filename
    plot_combined_measurements(combined_df, graph_path, sensor_labels, title)

    return GraphResult(
        output_folder=output_folder,
        graph_path=graph_path,
        data_folder=data_folder,
        combined_csv_path=combined_csv_path,
    )
