from __future__ import annotations

from pathlib import Path
import tempfile

import pandas as pd
import streamlit as st

from geochem_plotter import GeochemPlotter


st.set_page_config(page_title="Tuli Geochemical Plotter", layout="wide")


@st.cache_resource
def get_plotter(excel_path: str) -> GeochemPlotter:
    return GeochemPlotter(excel_path)


def _default_excel_path() -> Path:
    """Return path to Excel file, checking multiple common locations."""
    candidates = [
        Path(__file__).resolve().parent / "Tuli dataset.xls",
        Path(__file__).resolve().parent / "Tuli_dataset.xls",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]  # Return first path even if not found (will error with helpful message)


def _image_bytes_from_temp_plot(plot_fn) -> bytes:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    temp_path = temp_file.name
    temp_file.close()

    try:
        plot_fn(temp_path)
        with open(temp_path, "rb") as img_file:
            return img_file.read()
    finally:
        Path(temp_path).unlink(missing_ok=True)


def _csv_bytes(plotter: GeochemPlotter) -> bytes:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_path = temp_file.name
    temp_file.close()

    try:
        plotter.export_combined_data(temp_path)
        with open(temp_path, "rb") as csv_file:
            return csv_file.read()
    finally:
        Path(temp_path).unlink(missing_ok=True)


def _stats_dataframe(stats: dict) -> pd.DataFrame:
    if not stats:
        return pd.DataFrame()
    df = pd.DataFrame(stats).T.reset_index().rename(columns={"index": "Borehole"})
    return df[["Borehole", "count", "mean", "std", "min", "max", "median"]]


def main() -> None:
    st.title("Tuli Dataset Geochemical Plotter")

    default_excel = _default_excel_path()
    excel_path_str = str(default_excel)
    
    # Debug: Show where we're looking for the file
    st.sidebar.markdown("---")
    st.sidebar.subheader("Debug Info")
    st.sidebar.text(f"Looking for: {excel_path_str}")
    st.sidebar.text(f"Exists: {Path(excel_path_str).exists()}")
    
    if not Path(excel_path_str).exists():
        st.error(f"❌ Excel file not found: {excel_path_str}")
        st.info("Place 'Tuli dataset.xls' in the repository root folder and redeploy.")
        st.stop()

    try:
        with st.spinner("Loading dataset..."):
            plotter = get_plotter(excel_path_str)
        st.sidebar.success("✅ Data loaded successfully")
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

    elements = plotter.list_available_elements()
    boreholes = list(plotter.data.keys())

    st.sidebar.markdown("---")
    st.sidebar.write(f"**Boreholes loaded:** {len(boreholes)}")
    st.sidebar.write(f"**Elements available:** {len(elements)}")

    tab_profiles, tab_scatter, tab_borehole, tab_data = st.tabs(
        ["Depth Profiles", "Scatter", "Single Borehole", "Data & Stats"]
    )

    with tab_profiles:
        st.subheader("Multi-panel depth profiles")
        selected_elements = st.multiselect(
            "Elements to plot",
            options=elements,
            default=[e for e in ["MgO", "SiO2", "Rb", "Ni"] if e in elements],
        )
        col1, col2 = st.columns(2)
        fig_w = col1.slider("Figure width", 6, 24, 14)
        fig_h = col2.slider("Figure height", 4, 16, 8)

        if st.button("Generate depth profile", use_container_width=True):
            if not selected_elements:
                st.warning("Select at least one element.")
            else:
                with st.spinner("Generating plot..."):
                    image = _image_bytes_from_temp_plot(
                        lambda output: plotter.plot_depth_profiles(
                            selected_elements,
                            output_file=output,
                            figsize=(fig_w, fig_h),
                        )
                    )
                st.image(image, caption="Depth profile")
                st.download_button(
                    "Download PNG",
                    data=image,
                    file_name="depth_profile.png",
                    mime="image/png",
                    use_container_width=True,
                )

    with tab_scatter:
        st.subheader("Scatter plot (log-log)")
        col1, col2 = st.columns(2)
        x_var = col1.selectbox("X variable", options=elements, index=elements.index("MgO") if "MgO" in elements else 0)
        y_var = col2.selectbox("Y variable", options=elements, index=elements.index("Ni") if "Ni" in elements else min(1, len(elements) - 1))

        col3, col4 = st.columns(2)
        scatter_w = col3.slider("Figure width ", 6, 16, 10)
        scatter_h = col4.slider("Figure height ", 4, 12, 7)

        if st.button("Generate scatter", use_container_width=True):
            if x_var == y_var:
                st.warning("Choose different X and Y variables.")
            else:
                with st.spinner("Generating scatter plot..."):
                    image = _image_bytes_from_temp_plot(
                        lambda output: plotter.plot_scatter(
                            x_var,
                            y_var,
                            output_file=output,
                            figsize=(scatter_w, scatter_h),
                        )
                    )
                st.image(image, caption=f"{y_var} vs {x_var}")
                st.download_button(
                    "Download scatter PNG",
                    data=image,
                    file_name=f"scatter_{y_var}_vs_{x_var}.png",
                    mime="image/png",
                    use_container_width=True,
                )

    with tab_borehole:
        st.subheader("Single borehole profile")
        selected_borehole = st.selectbox("Borehole", options=boreholes)
        borehole_vars = plotter.get_borehole_variables(selected_borehole)

        if not borehole_vars:
            st.info("No plottable variables found for this borehole.")
        else:
            variable = st.selectbox("Variable", options=borehole_vars)
            col1, col2 = st.columns(2)
            bh_w = col1.slider("Figure width  ", 4, 14, 8)
            bh_h = col2.slider("Figure height  ", 6, 18, 10)

            if st.button("Generate borehole plot", use_container_width=True):
                with st.spinner("Generating borehole plot..."):
                    image = _image_bytes_from_temp_plot(
                        lambda output: plotter.plot_single_borehole_profile(
                            selected_borehole,
                            variable,
                            output_file=output,
                            figsize=(bh_w, bh_h),
                        )
                    )
                st.image(image, caption=f"{selected_borehole} - {variable}")
                st.download_button(
                    "Download borehole PNG",
                    data=image,
                    file_name=f"{selected_borehole}_{variable}.png",
                    mime="image/png",
                    use_container_width=True,
                )

    with tab_data:
        st.subheader("Dataset overview")
        selected_data_borehole = st.selectbox("Preview borehole", options=boreholes, key="preview_borehole")
        preview_df = plotter.data[selected_data_borehole]
        st.write(f"Rows: {preview_df.shape[0]} | Columns: {preview_df.shape[1]}")
        st.dataframe(preview_df.head(50), use_container_width=True)

        st.subheader("Element statistics")
        stats_element = st.selectbox("Element for summary stats", options=elements)
        stats_df = _stats_dataframe(plotter.get_summary_stats(stats_element))
        if stats_df.empty:
            st.info("No statistics available for this element.")
        else:
            st.dataframe(stats_df, use_container_width=True)

        st.subheader("Export combined data")
        if st.button("Prepare CSV export", use_container_width=True):
            with st.spinner("Creating CSV..."):
                csv_data = _csv_bytes(plotter)
            st.download_button(
                "Download combined_data.csv",
                data=csv_data,
                file_name="combined_data.csv",
                mime="text/csv",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
