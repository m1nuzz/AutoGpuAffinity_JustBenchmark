# FPS Benchmark

A simple FPS benchmarking tool that measures and analyzes frame times using PresentMon.

## Features
- Benchmarks FPS using Vulkan (lava-triangle) or D3D9
- Analyzes benchmark data from CSV files
- Supports customizable benchmark duration and cache warmup
- Detailed FPS metrics including percentiles and frame time analysis

## Installation

To set up the environment, follow these steps:

1. Clone the repository
2. Install the necessary dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the program using:
```bash
python main.py
```

Or analyze existing benchmark results:
```bash
python main.py --analyze path/to/csv/directory
```

## Configuration

Edit `config.ini` to customize:
- Benchmark duration
- Cache warmup duration
- Display settings
- FPS cap
- And more
