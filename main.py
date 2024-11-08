import argparse
import csv
import datetime
import logging
import os
import shutil
import subprocess
import sys
import textwrap
import time
import traceback
from typing import NoReturn

import consts
import framerate
import psutil
from config import Api, Config

LOG_CLI = logging.getLogger("CLI")


def print_table(formatted_results: dict[str, dict[str, str]]):
    print(f"{'Run':<5}", end="")
    for metric in (
        "Max",
        "Avg",
        "Min",
        "STDEV",
        "1 %ile",
        "0.1 %ile",
        "0.01 %ile",
        "0.005 %ile",
        "1% Low",
        "0.1% Low",
        "0.01% Low",
        "0.005% Low",
    ):
        print(f"{metric:<12}", end="")
    print()

    for _run, _results in formatted_results.items():
        print(f"{_run:<5}", end="")
        for metric_value in _results.values():
            right_padding = 21 if "[" in metric_value else 12
            print(f"{metric_value:<{right_padding}}", end="")
        print()
    print()


def display_results(csv_directory: str, enable_color: bool) -> None:
    results: dict[str, dict[str, float]] = {}
    colors: list[str] = ["\x1b[92m", "\x1b[93m"]
    default = "\x1b[0m" if enable_color else ""

    if enable_color:
        os.system("color")

    csv_files = [f for f in os.listdir(csv_directory) if f.endswith('.csv')]
    for csv_file in csv_files:
        frametimes: list[float] = []
        with open(f"{csv_directory}\\{csv_file}", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                row_lower = {key.lower(): value for key, value in row.items()}
                if (ms_between_presents := row_lower.get("msbetweenpresents")) is not None:
                    frametimes.append(float(ms_between_presents))

        fps = framerate.Fps(frametimes)
        run_name = os.path.splitext(csv_file)[0]
        results[run_name] = {
            "maximum": round(fps.maximum(), 2),
            "average": round(fps.average(), 2),
            "minimum": round(fps.minimum(), 2),
            "stdev": round(-fps.stdev(), 2),
            **{
                f"{metric}{value}": round(getattr(fps, metric)(value), 2)
                for metric in ("percentile", "lows")
                for value in (1, 0.1, 0.01, 0.005)
            },
        }

    formatted_results: dict[str, dict[str, str]] = {run: {} for run in results}
    for metric in (
        "maximum",
        "average",
        "minimum",
        "stdev",
        *(f"{metric}{value}" for metric in ("percentile", "lows") for value in (1, 0.1, 0.01, 0.005)),
    ):
        values = {_results[metric] for _results in results.values()}
        top_values = list(dict.fromkeys(sorted(values, reverse=True)[:len(colors)]))

        for _run, _results in results.items():
            metric_value = _results[metric]
            new_value = f"{abs(metric_value):.2f}"

            if enable_color:
                try:
                    nth_best = top_values.index(metric_value)
                    color = colors[nth_best]
                    new_value = f"{color}{new_value}{default}"
                except ValueError:
                    pass

            formatted_results[_run][metric] = new_value

    print_table(formatted_results)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="version",
        version=f"FPS Benchmark v{consts.VERSION}",
    )
    parser.add_argument(
        "--config",
        metavar="<config>",
        type=str,
        help="path to config file",
    )
    parser.add_argument(
        "--analyze",
        metavar="<csv directory>",
        type=str,
        help="analyze csv files from a previous benchmark",
    )
    return parser.parse_args()


def kill_processes(*targets: str) -> None:
    targets_set = set(targets)
    for process in psutil.process_iter():
        if process.name().lower() in targets_set:
            process.kill()


def main() -> int:
    logging.basicConfig(format="[%(name)s] %(levelname)s: %(message)s", level=logging.INFO)
    print(f"FPS Benchmark Version {consts.VERSION} - GPLv3\n")

    full_program_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__)
    os.chdir(full_program_dir)

    args = parse_args()
    winver = sys.getwindowsversion()

    if args.analyze:
        display_results(args.analyze, winver.major >= 10)
        return 0

    presentmon_version = "1.10.0" if winver.major >= 10 and winver.product_type != 3 else "1.6.0"
    presentmon_binary = f"PresentMon-{presentmon_version}-x64.exe"
    config_path = args.config if args.config is not None else "config.ini"

    try:
        cfg = Config(config_path)
    except FileNotFoundError as e:
        LOG_CLI.exception(e)
        return 1

    if cfg.validate_config() != 0:
        LOG_CLI.error("failed to validate config")
        return 1

    api_binpaths: dict[Api, str] = {
        Api.LIBLAVA: "bin\\liblava\\lava-triangle.exe",
        Api.D3D9: "bin\\D3D9-benchmark.exe",
    }

    api_binpath = api_binpaths[cfg.settings.api]
    api_binname = os.path.basename(api_binpath)
    session_directory = f"captures\\FPSBenchmark-{time.strftime('%d%m%y%H%M%S')}"

    estimated_time_seconds = 10 + cfg.settings.cache_duration + cfg.settings.benchmark_duration
    estimated_time = datetime.timedelta(seconds=estimated_time_seconds)
    finish_time = datetime.datetime.now() + estimated_time

    print(
        textwrap.dedent(
            f"""        Session Directory        {session_directory}
        Cache Duration           {cfg.settings.cache_duration}
        Benchmark Duration       {cfg.settings.benchmark_duration}
        Subject                  {os.path.splitext(api_binname)[0]}
        Estimated Time           {estimated_time}
        Estimated End Time       {finish_time.strftime('%H:%M:%S')}
        """,
        ),
    )

    if not cfg.settings.skip_confirmation:
        input("press enter to start benchmarking...")

    subject_args: list[str] = []
    if cfg.settings.api == Api.LIBLAVA:
        subject_args = [
            f"--fullscreen={int(cfg.liblava.fullscreen)}",
            f"--width={cfg.liblava.x_resolution}",
            f"--height={cfg.liblava.y_resolution}",
            f"--fps_cap={cfg.liblava.fps_cap}",
            f"--triple_buffering={int(cfg.liblava.triple_buffering)}",
        ]

    os.makedirs(f"{session_directory}\\CSVs", exist_ok=True)
    kill_processes(api_binname, presentmon_binary)
    LOG_CLI.info("starting benchmark")

    subprocess.run(
        ["start", "", api_binpath, *subject_args],
        shell=True,
        check=True,
    )

    time.sleep(5 + cfg.settings.cache_duration)

    subprocess.run(
        [
            f"bin\\PresentMon\\{presentmon_binary}",
            "-stop_existing_session",
            "-no_top",
            "-timed",
            str(cfg.settings.benchmark_duration),
            "-process_name",
            api_binname,
            "-output_file",
            f"{session_directory}\\CSVs\\benchmark.csv",
            "-terminate_after_timed",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    if not os.path.exists(f"{session_directory}\\CSVs\\benchmark.csv"):
        LOG_CLI.error("csv log unsuccessful, this may be due to a missing dependency or windows component")
        shutil.rmtree(session_directory)
        return 1

    kill_processes(api_binname, presentmon_binary)
    print()
    display_results(f"{session_directory}\\CSVs", winver.major >= 10)
    return 0


def _main() -> NoReturn:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    _main()
