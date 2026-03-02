"""
Geochemical Data Plotting Tool for Tuli Dataset
Creates depth profile plots similar to stratigraphic variation diagrams
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import gridspec
import warnings
warnings.filterwarnings('ignore')

class GeochemPlotter:
    """A tool for plotting geochemical data from borehole cores"""
    
    def __init__(self, excel_file_path):
        """
        Initialize the plotter with an Excel file
        
        Parameters:
        -----------
        excel_file_path : str
            Path to the Excel file containing borehole data
        """
        self.file_path = excel_file_path
        self.data = {}
        self.load_data()
        
    def load_data(self):
        """Load all sheets from the Excel file"""
        print("Loading data from Excel file...")
        xls = pd.ExcelFile(self.file_path)
        
        for sheet_name in xls.sheet_names:
            print(f"  Loading sheet: {sheet_name}")
            # Read with header from row 1 (second row)
            df = pd.read_excel(self.file_path, sheet_name=sheet_name, header=1)
            
            # Clean up the dataframe
            # First column should be 'Sample'
            if df.columns[0] != 'Sample':
                df = pd.read_excel(self.file_path, sheet_name=sheet_name, header=None)
                # Find the row with 'Sample'
                for idx, row in df.iterrows():
                    if 'Sample' in row.values:
                        df.columns = df.iloc[idx]
                        df = df.iloc[idx+1:].reset_index(drop=True)
                        break
            
            # Convert numeric columns
            for col in df.columns:
                if col not in ['Sample', 'Rock Type']:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except:
                        pass
            
            # Store the data
            self.data[sheet_name] = df
            
        print(f"Loaded {len(self.data)} borehole sheets\n")
        
    def list_available_elements(self):
        """List all available elements/parameters in the dataset"""
        all_columns = set()
        for sheet_name, df in self.data.items():
            all_columns.update(df.columns)
        
        # Remove non-element columns
        exclude = ['Sample', 'Rock Type', 'Unnamed', 'nan']
        # Filter to only string columns and sort
        elements = sorted([col for col in all_columns 
                          if isinstance(col, str)
                          and not any(ex in str(col) for ex in exclude) 
                          and pd.notna(col)])
        
        print("Available elements/parameters:")
        for i, elem in enumerate(elements, 1):
            print(f"  {i:2d}. {elem}")
        print()
        return elements
        
    def plot_depth_profiles(self, elements_to_plot, output_file='geochem_plot.png', 
                           figsize=(16, 10), marker_styles=None, colors=None):
        """
        Create multi-panel depth profile plots
        
        Parameters:
        -----------
        elements_to_plot : list
            List of element/parameter names to plot (e.g., ['MgO', 'SiO2', 'La/Sm'])
        output_file : str
            Output filename for the plot
        figsize : tuple
            Figure size (width, height) in inches
        marker_styles : dict
            Dictionary mapping borehole names to marker styles
        colors : dict
            Dictionary mapping borehole names to colors
        """
        n_panels = len(elements_to_plot)
        
        # Create figure with subplots
        fig, axes = plt.subplots(1, n_panels, figsize=figsize, sharey=True)
        if n_panels == 1:
            axes = [axes]
        
        # Default marker styles for different boreholes
        if marker_styles is None:
            markers = ['o', '^', 's', 'D', 'v', 'P', '*', 'X', 'p', 'h', '+']
            marker_styles = {}
        
        if colors is None:
            colors = {}
        
        # Get all borehole names
        borehole_names = list(self.data.keys())
        
        # Assign markers and colors
        for i, bh in enumerate(borehole_names):
            if bh not in marker_styles:
                marker_styles[bh] = markers[i % len(markers)]
            if bh not in colors:
                colors[bh] = f'C{i % 10}'
        
        # Plot each element
        for ax_idx, element in enumerate(elements_to_plot):
            ax = axes[ax_idx]
            
            # Plot data from each borehole
            for bh_name, df in self.data.items():
                # Check if element exists in this borehole
                if element in df.columns:
                    # Get depth and element data
                    depth = df['BH_From'].values if 'BH_From' in df.columns else df.get('Depth', df.index)
                    values = df[element].values
                    
                    # Remove NaN values and non-positive values for log scale
                    mask = ~(np.isnan(depth) | np.isnan(values)) & (values > 0)
                    depth_clean = depth[mask]
                    values_clean = values[mask]
                    
                    if len(depth_clean) > 0:
                        # Plot with borehole-specific style
                        ax.plot(values_clean, depth_clean, 
                               marker=marker_styles[bh_name],
                               linestyle='-',
                               color=colors[bh_name],
                               label=bh_name,
                               markersize=6,
                               linewidth=1,
                               alpha=0.7)
            
            # Format the subplot
            ax.set_xlabel(element, fontsize=11, fontweight='bold')
            ax.set_xscale('log')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.tick_params(labelsize=9)
            
            # Add panel label (A, B, C, etc.)
            panel_label = chr(65 + ax_idx)  # A, B, C, ...
            ax.text(0.02, 0.98, panel_label, transform=ax.transAxes,
                   fontsize=14, fontweight='bold', va='top')
        
        # Set y-axis label and invert (depth increases downward)
        axes[0].set_ylabel('Depth / Stratigraphic Position (m)', fontsize=12, fontweight='bold')
        axes[0].invert_yaxis()
        
        # Add legend to the last panel
        handles, labels = axes[-1].get_legend_handles_labels()
        if handles:
            # Remove duplicates
            by_label = dict(zip(labels, handles))
            axes[-1].legend(by_label.values(), by_label.keys(), 
                          loc='best', fontsize=8, framealpha=0.9)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_file}")
        plt.close()
        
    def plot_custom_figure(self, plot_config, output_file='custom_geochem_plot.png'):
        """
        Create a custom figure based on configuration
        
        Parameters:
        -----------
        plot_config : dict
            Configuration dictionary with keys:
            - 'elements': list of elements to plot
            - 'figsize': tuple (width, height)
            - 'title': optional title
        output_file : str
            Output filename
        """
        elements = plot_config.get('elements', [])
        figsize = plot_config.get('figsize', (16, 10))
        title = plot_config.get('title', '')
        
        self.plot_depth_profiles(elements, output_file=output_file, figsize=figsize)
        
        if title:
            plt.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            
    def get_summary_stats(self, element):
        """Get summary statistics for an element across all boreholes"""
        stats = {}
        for bh_name, df in self.data.items():
            if element in df.columns:
                values = df[element].dropna()
                if len(values) > 0:
                    stats[bh_name] = {
                        'count': len(values),
                        'mean': values.mean(),
                        'std': values.std(),
                        'min': values.min(),
                        'max': values.max(),
                        'median': values.median()
                    }
        return stats
        
    def export_combined_data(self, output_file='combined_data.csv'):
        """Export all borehole data into a single CSV file"""
        combined = []
        for bh_name, df in self.data.items():
            df_copy = df.copy()
            df_copy['Borehole'] = bh_name
            combined.append(df_copy)
        
        result = pd.concat(combined, ignore_index=True)
        result.to_csv(output_file, index=False)
        print(f"Combined data exported to: {output_file}")
        return result
    
    def plot_scatter(self, x_element, y_element, output_file='scatter_plot.png',
                    figsize=(10, 7), marker_styles=None, colors=None):
        """
        Create a scatter plot of two variables with log scale
        
        Parameters:
        -----------
        x_element : str
            Element/parameter name for X-axis
        y_element : str
            Element/parameter name for Y-axis
        output_file : str
            Output filename for the plot
        figsize : tuple
            Figure size (width, height) in inches
        marker_styles : dict
            Dictionary mapping borehole names to marker styles
        colors : dict
            Dictionary mapping borehole names to colors
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Default marker styles for different boreholes
        if marker_styles is None:
            markers = ['o', '^', 's', 'D', 'v', 'P', '*', 'X', 'p', 'h', '+']
            marker_styles = {}
        else:
            markers = ['o', '^', 's', 'D', 'v', 'P', '*', 'X', 'p', 'h', '+']
        
        if colors is None:
            colors = {}
        
        # Get all borehole names
        borehole_names = list(self.data.keys())
        
        # Assign markers and colors
        for i, bh in enumerate(borehole_names):
            if bh not in marker_styles:
                marker_styles[bh] = markers[i % len(markers)]
            if bh not in colors:
                colors[bh] = f'C{i % 10}'
        
        # Plot data from each borehole
        for bh_name, df in self.data.items():
            # Check if both elements exist in this borehole
            if x_element in df.columns and y_element in df.columns:
                x_vals = df[x_element].values
                y_vals = df[y_element].values
                
                # Remove NaN values and non-positive values for log scale
                mask = ~(np.isnan(x_vals) | np.isnan(y_vals)) & (x_vals > 0) & (y_vals > 0)
                x_clean = x_vals[mask]
                y_clean = y_vals[mask]
                
                if len(x_clean) > 0:
                    # Plot with borehole-specific style
                    ax.scatter(x_clean, y_clean,
                             marker=marker_styles[bh_name],
                             s=50,
                             color=colors[bh_name],
                             label=bh_name,
                             alpha=0.7,
                             edgecolors='black',
                             linewidth=0.5)
        
        # Format the plot
        ax.set_xlabel(x_element, fontsize=11, fontweight='bold')
        ax.set_ylabel(y_element, fontsize=11, fontweight='bold')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.tick_params(labelsize=9)
        
        # Add legend
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc='best', fontsize=8, framealpha=0.9)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Scatter plot saved to: {output_file}")
        plt.close()
    
    def plot_single_borehole_profile(self, borehole_name, element, output_file='borehole_profile.png',
                                     figsize=(8, 10)):
        """
        Create a depth profile plot for a single element in a specific borehole
        
        Parameters:
        -----------
        borehole_name : str
            Name of the borehole
        element : str
            Element/parameter to plot
        output_file : str
            Output filename
        figsize : tuple  
            Figure size (width, height)
        """
        # Validate inputs
        if borehole_name not in self.data:
            raise ValueError(f"Borehole '{borehole_name}' not found")
        
        df = self.data[borehole_name]
        
        if element not in df.columns:
            raise ValueError(f"Element '{element}' not found in borehole '{borehole_name}'")
        
        # Get depth and element values
        if 'BH_From' not in df.columns:
            raise ValueError(f"'BH_From' column not found in borehole '{borehole_name}'")
        
        # Create clean dataframe with only what we need
        work_df = pd.DataFrame({
            'depth': df['BH_From'],
            'value': df[element]
        })
        
        # Add rock type if available
        has_rock_type = False
        if 'Type' in df.columns:
            work_df['rock_type'] = df['Type']
            has_rock_type = True
        
        # Remove NaN values
        work_df = work_df.dropna(subset=['depth', 'value'])
        
        if len(work_df) == 0:
            raise ValueError(f"No valid data points for {element} in {borehole_name}")
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Determine if log scale is appropriate
        use_log = np.all(work_df['value'].values > 0)
        
        # Plot with or without rock type coloring
        if has_rock_type and 'rock_type' in work_df.columns:
            unique_types = work_df['rock_type'].dropna().unique()
            
            if len(unique_types) > 0:
                # Create color map
                color_palette = plt.cm.tab10(np.linspace(0, 1, len(unique_types)))
                type_colors = {rock_type: color_palette[i] for i, rock_type in enumerate(unique_types)}
                
                # Plot each rock type
                for rock_type in unique_types:
                    mask = work_df['rock_type'] == rock_type
                    subset = work_df[mask]
                    
                    ax.plot(subset['value'], subset['depth'],
                           marker='o',
                           markersize=7,
                           linestyle='-',
                           linewidth=1.5,
                           color=type_colors[rock_type],
                           label=str(rock_type),
                           alpha=0.8)
                
                # Add legend
                ax.legend(title='Rock Type', loc='best', fontsize=9, framealpha=0.95)
            else:
                # No valid rock types
                ax.plot(work_df['value'], work_df['depth'],
                       marker='o',
                       markersize=7,
                       linestyle='-',
                       linewidth=2,
                       color='#667eea',
                       alpha=0.8)
        else:
            # No rock type, simple plot
            ax.plot(work_df['value'], work_df['depth'],
                   marker='o',
                   markersize=7,
                   linestyle='-',
                   linewidth=2,
                   color='#667eea',
                   alpha=0.8)
        
        # Apply log scale if appropriate
        if use_log:
            ax.set_xscale('log')
        
        # Format axes
        ax.set_xlabel(element, fontsize=12, fontweight='bold')
        ax.set_ylabel('Depth (m)', fontsize=12, fontweight='bold')
        ax.set_title(f'{borehole_name} - {element}', fontsize=14, fontweight='bold', pad=15)
        
        # Grid and styling
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        ax.invert_yaxis()
        ax.tick_params(labelsize=10)
        
        # Save and close
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.invert_yaxis()  # Depth increases downward
        ax.tick_params(labelsize=10)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Borehole plot saved to: {output_file}")
        plt.close()
    
    def get_borehole_variables(self, borehole_name):
        """Get list of available variables for a specific borehole"""
        if borehole_name not in self.data:
            return []
        
        df = self.data[borehole_name]
        # Exclude non-element columns (use same logic as list_available_elements)
        exclude = ['Sample', 'Rock Type', 'Unnamed', 'nan', 'BH_From', 'BH_To', 'Depth']
        variables = sorted([col for col in df.columns 
                           if isinstance(col, str)
                           and not any(ex in str(col) for ex in exclude)
                           and pd.notna(col)])
        return variables

# Example usage
if __name__ == "__main__":
    # Initialize the plotter
    from pathlib import Path
    file_path = Path(__file__).resolve().parent / "Tuli dataset.xls"
    plotter = GeochemPlotter(str(file_path))
    
    # List available elements
    elements = plotter.list_available_elements()
    
    print("\n" + "="*80)
    print("Creating example plots based on reference images...")
    print("="*80 + "\n")
    
    # Example 1: Major elements and ratios (similar to Figure 1 in references)
    print("Plot 1: Major elements and trace element ratios")
    plot1_elements = ['MgO', 'SiO2', 'La/Sm', 'Th/Nb']
    plotter.plot_depth_profiles(plot1_elements, 
                               output_file='plot1_major_elements.png',
                               figsize=(14, 10))
    
    # Example 2: Trace elements (similar to Figure 2 in references)
    print("\nPlot 2: Trace elements")
    plot2_elements = ['Rb', 'Cu', 'Pt', 'Pd']
    plotter.plot_depth_profiles(plot2_elements, 
                               output_file='plot2_trace_elements.png',
                               figsize=(14, 10))
    
    # Example 3: Custom scatter plot with log scale
    print("\nPlot 3: Custom scatter plot (Ni vs MgO)")
    plotter.plot_scatter('MgO', 'Ni',
                        output_file='scatter_ni_vs_mgo.png',
                        figsize=(10, 7))
    
    print("\nPlot 4: Custom scatter plot (Cu vs Ni)")
    plotter.plot_scatter('Cu', 'Ni',
                        output_file='scatter_ni_vs_cu.png',
                        figsize=(10, 7))
    
    print("\n" + "="*80)
    print("Plotting complete! Check the output files.")
    print("="*80)
