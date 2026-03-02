# Tuli Dataset Geochemical Plotter

A Streamlit web application for interactive visualization and analysis of geochemical data from borehole cores.

## Features

- **Depth Profiles**: Multi-panel stratigraphic plots of geochemical elements
- **Scatter Plots**: Log-log visualization comparing any two variables across boreholes
- **Single Borehole Analysis**: Detailed depth profiles for individual boreholes
- **Data Export**: Download combined dataset as CSV
- **Summary Statistics**: Element-by-element stats across all boreholes
- **Data Preview**: Browse raw data for any borehole

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/tuli-geochemical-plotter.git
   cd tuli-geochemical-plotter
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Local development
```bash
streamlit run streamlit_app.py
```
Open browser to `http://localhost:8501`

### Cloud deployment (Streamlit Community Cloud)
1. Push this repo to GitHub
2. Go to [Streamlit Community Cloud](https://streamlit.io/cloud)
3. Click "New app", select your repo and `streamlit_app.py`
4. Deploy

## Data Format

The app expects an Excel file with geochemical data in multiple sheets:
- Each sheet is a borehole (e.g., `TLE-01`, `TLW-01`)
- Columns: Sample, BH_From (depth), elements/parameters, Type (rock type)
- Numeric values for elements/ratios

## Architecture

- **`geochem_plotter.py`**: Core plotting and data handling (GeochemPlotter class)
- **`streamlit_app.py`**: Streamlit UI entry point
- **`app.py`**: Legacy Flask app (kept for reference)

## License

MIT

## Author

Created for the Tuli Dataset geochemical analysis project.
