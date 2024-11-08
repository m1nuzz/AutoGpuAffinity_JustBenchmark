# FPS Benchmark

A simple FPS benchmarking tool that measures and analyzes frame times using PresentMon.

## Features
- Benchmarks FPS using Vulkan (lava-triangle) or D3D9
- Analyzes benchmark data from CSV files
- Supports customizable benchmark duration and cache warmup
- Detailed FPS metrics including percentiles and frame time analysis
- Stores benchmark history for comparison between runs
- Color-coded results highlighting best performance metrics
- Easy history management with clear function

## Installation

To set up the environment, follow these steps:

1. Clone the repository
2. Install the necessary dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
Run the program using:
```bash
python main.py
```

### Benchmark Controls
- Press `Enter` to start a new benchmark
- Type `1` and press `Enter` to clear benchmark history
- Results are automatically saved and compared with previous runs

### Analyze Existing Results
Analyze specific benchmark results:
```bash
python main.py --analyze path/to/csv/directory
```

## Results Display
- Current and historical results are shown together
- Best results are highlighted in green
- Metrics include:
  - Maximum, Average, and Minimum FPS
  - Standard Deviation
  - Percentiles (1%, 0.1%, 0.01%, 0.005%)
  - Low percentages (1%, 0.1%, 0.01%, 0.005%)

## Configuration

Edit `config.ini` to customize:
- Benchmark duration
- Cache warmup duration
- Display settings
- FPS cap
- API selection (Vulkan/D3D9)
- Triple buffering options
- Resolution settings

## History Management
- Benchmark results are automatically saved to `benchmark_history.json`
- View historical results alongside new benchmarks
- Clear history using the `1` command at startup
- Best results are automatically highlighted for easy comparison

## Requirements
- Windows OS
- Python 3.6+
- Dependencies listed in requirements.txt
- PresentMon (included in the package)
