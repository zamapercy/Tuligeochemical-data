"""
Flask web app for Geochemical Data Plotting Tool
"""

from flask import Flask, render_template, jsonify, request, send_file
import os
import json
import tempfile
from geochem_plotter import GeochemPlotter
from io import BytesIO
import base64
import numpy as np
import matplotlib.pyplot as plt

app = Flask(__name__, template_folder='templates')

# Initialize the plotter
file_path = r"c:\Users\mzake\OneDrive\Desktop\Tuli dataset\Tuli dataset.xls"
plotter = GeochemPlotter(file_path)

# Get available elements and boreholes
available_elements = plotter.list_available_elements()
available_boreholes = list(plotter.data.keys())


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                         elements=available_elements,
                         boreholes=available_boreholes)


@app.route('/api/elements')
def get_elements():
    """Get list of available elements"""
    return jsonify({
        'elements': available_elements,
        'count': len(available_elements)
    })


@app.route('/api/boreholes')
def get_boreholes():
    """Get list of available boreholes"""
    return jsonify({
        'boreholes': available_boreholes,
        'count': len(available_boreholes)
    })


@app.route('/api/stats/<element>')
def get_stats(element):
    """Get statistics for an element"""
    stats = plotter.get_summary_stats(element)
    return jsonify(stats)


def _plot_to_base64(elements, figsize, filename_prefix):
    """Render a plot to a temp file and return base64 data and filename."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix=filename_prefix)
    temp_path = temp_file.name
    temp_file.close()

    try:
        plotter.plot_depth_profiles(elements, output_file=temp_path, figsize=tuple(figsize))
        with open(temp_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return image_data, os.path.basename(temp_path)


def _scatter_to_base64(x_label, y_label, figsize, filename_prefix):
    """Render a scatter plot to a temp file and return base64 data and filename."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix=filename_prefix)
    temp_path = temp_file.name
    temp_file.close()

    fig, ax = plt.subplots(figsize=figsize)
    markers = ['o', '^', 's', 'D', 'v', 'P', '*', 'X', 'p', 'h', '+']

    try:
        for idx, (bh_name, df) in enumerate(plotter.data.items()):
            if x_label not in df.columns or y_label not in df.columns:
                continue
            x_vals = df[x_label].to_numpy()
            y_vals = df[y_label].to_numpy()
            mask = np.isfinite(x_vals) & np.isfinite(y_vals) & (x_vals > 0) & (y_vals > 0)
            if mask.any():
                ax.scatter(
                    x_vals[mask],
                    y_vals[mask],
                    s=28,
                    marker=markers[idx % len(markers)],
                    alpha=0.7,
                    label=bh_name,
                )

        ax.set_xlabel(x_label, fontsize=11, fontweight='bold')
        ax.set_ylabel(y_label, fontsize=11, fontweight='bold')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best', fontsize=8, framealpha=0.9)
        fig.tight_layout()
        fig.savefig(temp_path, dpi=300, bbox_inches='tight')

        with open(temp_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
    finally:
        plt.close(fig)
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return image_data, os.path.basename(temp_path)


@app.route('/api/plot', methods=['POST'])
def generate_plot():
    """Generate a plot based on selected elements"""
    data = request.json
    elements = data.get('elements', [])
    figsize = data.get('figsize', [16, 10])

    if not elements:
        return jsonify({'error': 'No elements selected'}), 400

    try:
        image_data, filename = _plot_to_base64(elements, figsize, 'plot_')
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{image_data}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/export', methods=['POST'])
def export_data():
    """Export combined data"""
    try:
        output_file = 'combined_data.csv'
        plotter.export_combined_data(output_file)
        return send_file(output_file, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/<borehole>')
def get_borehole_data(borehole):
    """Get data for a specific borehole"""
    if borehole not in plotter.data:
        return jsonify({'error': 'Borehole not found'}), 404
    
    df = plotter.data[borehole]
    return jsonify({
        'borehole': borehole,
        'shape': list(df.shape),
        'columns': df.columns.tolist(),
        'data': df.head(20).to_dict()
    })


@app.route('/api/plot/plot1', methods=['GET'])
def get_plot1():
    """Generate Plot 1: Major elements and trace element ratios"""
    try:
        plot1_elements = ['MgO', 'SiO2', 'La/Sm', 'Th/Nb']
        image_data, filename = _plot_to_base64(plot1_elements, (14, 10), 'plot1_')
        
        return jsonify({
            'success': True,
            'plot_name': 'Plot 1: Major Elements & Ratios',
            'elements': plot1_elements,
            'image': f'data:image/png;base64,{image_data}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/plot/plot2', methods=['GET'])
def get_plot2():
    """Generate Plot 2: Trace elements"""
    try:
        plot2_elements = ['Rb', 'Cu', 'Pt', 'Pd']
        image_data, filename = _plot_to_base64(plot2_elements, (14, 10), 'plot2_')
        
        return jsonify({
            'success': True,
            'plot_name': 'Plot 2: Trace Elements',
            'elements': plot2_elements,
            'image': f'data:image/png;base64,{image_data}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/plot/ni-vs-mgo', methods=['GET'])
def get_ni_vs_mgo():
    """Generate Ni vs MgO scatter plot for all boreholes."""
    try:
        image_data, filename = _scatter_to_base64('MgO', 'Ni', (10, 7), 'ni_vs_mgo_')
        return jsonify({
            'success': True,
            'plot_name': 'Ni vs MgO',
            'x': 'MgO',
            'y': 'Ni',
            'image': f'data:image/png;base64,{image_data}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/plot/ni-vs-cu', methods=['GET'])
def get_ni_vs_cu():
    """Generate Ni vs Cu scatter plot for all boreholes."""
    try:
        image_data, filename = _scatter_to_base64('Cu', 'Ni', (10, 7), 'ni_vs_cu_')
        return jsonify({
            'success': True,
            'plot_name': 'Ni vs Cu',
            'x': 'Cu',
            'y': 'Ni',
            'image': f'data:image/png;base64,{image_data}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/plot/custom-scatter', methods=['POST'])
def get_custom_scatter():
    """Generate custom scatter plot for any two variables."""
    try:
        data = request.json
        x_var = data.get('x_variable')
        y_var = data.get('y_variable')
        figsize = data.get('figsize', [10, 7])
        
        if not x_var or not y_var:
            return jsonify({'error': 'Both x_variable and y_variable are required'}), 400
        
        if x_var == y_var:
            return jsonify({'error': 'X and Y variables must be different'}), 400
        
        image_data, filename = _scatter_to_base64(x_var, y_var, tuple(figsize), 'custom_scatter_')
        return jsonify({
            'success': True,
            'plot_name': f'{y_var} vs {x_var}',
            'x': x_var,
            'y': y_var,
            'image': f'data:image/png;base64,{image_data}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/borehole/<borehole_name>/variables')
def get_borehole_variables(borehole_name):
    """Get available variables for a specific borehole"""
    try:
        variables = plotter.get_borehole_variables(borehole_name)
        return jsonify({
            'success': True,
            'borehole': borehole_name,
            'variables': variables,
            'count': len(variables)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _borehole_plot_to_base64(borehole_name, variable, figsize, filename_prefix):
    """Render a single borehole variable plot to base64."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix=filename_prefix)
    temp_path = temp_file.name
    temp_file.close()

    try:
        plotter.plot_single_borehole_profile(borehole_name, variable, output_file=temp_path, figsize=tuple(figsize))
        with open(temp_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return image_data, os.path.basename(temp_path)


@app.route('/api/plot/borehole', methods=['POST'])
def generate_borehole_plot():
    """Generate single borehole variable plots for multiple variables"""
    try:
        data = request.json
        borehole_name = data.get('borehole')
        variables = data.get('variables', [])  # Now accepts multiple variables
        figsize = data.get('figsize', [8, 10])
        
        if not borehole_name:
            return jsonify({'error': 'Borehole name is required'}), 400
        
        if not variables or len(variables) == 0:
            return jsonify({'error': 'At least one variable is required'}), 400
        
        if borehole_name not in available_boreholes:
            return jsonify({'error': f'Borehole {borehole_name} not found'}), 404
        
        # Generate plots for all selected variables
        plots = []
        for variable in variables:
            try:
                image_data, filename = _borehole_plot_to_base64(borehole_name, variable, figsize, 'borehole_')
                plots.append({
                    'variable': variable,
                    'image': f'data:image/png;base64,{image_data}',
                    'filename': filename
                })
            except Exception as e:
                plots.append({
                    'variable': variable,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'borehole': borehole_name,
            'plots': plots,
            'count': len(plots)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
