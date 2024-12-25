import matplotlib
matplotlib.use('Agg')

from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import font_manager
from werkzeug.utils import secure_filename
import uuid
from data_processing import data_processing
import platform
from scipy.cluster.hierarchy import dendrogram, linkage

ops = platform.system()
if ops =='Linux':
    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    font_prop = font_manager.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
else:
    plt.rcParams['font.sans-serif'] = ['SimHei']

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

uploaded_data = None
combined_table = None
table1_columns = []
table2_columns = []
correlation_matrix = None
xtick_rotation = 90
filename = ''

def generate_heatmap(correlation_matrix, xtick_rotation, correlation_method):
    plt.figure(figsize=(12, 10))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', cbar_kws={'shrink': 0.75})
    plt.xticks(rotation=xtick_rotation)
    plt.yticks(rotation=0)
    plt.title(f"Correlation Matrix ({correlation_method.capitalize()})", fontsize=12, loc='left')
    plt.tight_layout()
    unique_id = uuid.uuid4().hex
    heatmap_filename = f"heatmap_{unique_id}.png"
    heatmap_path = os.path.join(app.config['UPLOAD_FOLDER'], heatmap_filename)
    plt.savefig(heatmap_path, bbox_inches='tight')
    plt.close()
    return heatmap_filename

def generate_dendrogram(correlation_matrix, xtick_rotation, correlation_method):
    # Ensure the correlation matrix contains only finite values
    finite_matrix = np.nan_to_num(correlation_matrix, nan=0.0, posinf=0.0, neginf=0.0)
    plt.figure(figsize=(10, 10))  # Adjust dendrogram size to match heatmap
    Z = linkage(finite_matrix, 'ward')
    dendrogram(Z, labels=correlation_matrix.columns, leaf_rotation=xtick_rotation)
    plt.title(f"Dendrogram ({correlation_method.capitalize()})", fontsize=12, loc='left')
    plt.tight_layout()
    unique_id = uuid.uuid4().hex
    dendrogram_filename = f"dendrogram_{unique_id}.png"
    dendrogram_path = os.path.join(app.config['UPLOAD_FOLDER'], dendrogram_filename)
    plt.savefig(dendrogram_path, bbox_inches='tight')
    plt.close()
    return dendrogram_filename

@app.route('/')
def index():
    return render_template('heatmap.html')

@app.route('/upload', methods=['POST'])
def upload():
    global uploaded_data, combined_table, table1_columns, table2_columns, correlation_matrix, filename

    if 'file' not in request.files:
        return render_template('heatmap.html', heatmap_filename=None, error_message="No file part in the request.", table1_columns=[], table2_columns=[], correlation_method='pearson', file_name='')

    file = request.files['file']
    correlation_method = request.form.get('correlation_method', 'pearson')

    if file.filename == '':
        return render_template('heatmap.html', heatmap_filename=None, error_message="No file selected.", table1_columns=[], table2_columns=[], correlation_method=correlation_method, file_name='')

    if file:
        unique_id = uuid.uuid4().hex
        filename = secure_filename(file.filename)
        unique_filename = f"{unique_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        try:
            data = pd.read_csv(filepath, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                data = pd.read_csv(filepath, encoding='gbk')
            except Exception as e:
                return render_template('heatmap.html', heatmap_filename=None, error_message=f"Unable to read the file: {e}", table1_columns=[], table2_columns=[], correlation_method=correlation_method, file_name='')

        if data.empty or data.shape[1] < 2:
            return render_template('heatmap.html', heatmap_filename=None, error_message="CSV must have at least two columns.", table1_columns=[], table2_columns=[], correlation_method=correlation_method, file_name='')

        combined_table, table1_columns, table2_columns = data_processing(data)
        uploaded_data = data

        numeric_combined_table = combined_table.select_dtypes(include=[np.number])
        if not numeric_combined_table.empty:
            correlation_matrix = numeric_combined_table.corr(method=correlation_method)
            heatmap_filename = generate_heatmap(correlation_matrix, xtick_rotation, correlation_method)
            dendrogram_filename = generate_dendrogram(correlation_matrix, xtick_rotation, correlation_method)
            return render_template('heatmap.html', heatmap_filename=heatmap_filename, dendrogram_filename=dendrogram_filename, table1_columns=table1_columns, table2_columns=table2_columns, correlation_method=correlation_method, file_name=filename)

    return render_template('heatmap.html', heatmap_filename=None, table1_columns=table1_columns, table2_columns=table2_columns, correlation_method=correlation_method, file_name='', error_message="Error processing the file.")

@app.route('/update_columns', methods=['POST'])
def update_columns():
    global uploaded_data, combined_table, table1_columns, table2_columns, correlation_matrix

    if uploaded_data is None:
        return {"error": "No data uploaded."}, 400

    if not uploaded_data.empty:
        selected_columns = request.json.get('columns', [])
        correlation_method = request.json.get('correlation_method', 'pearson')

        selected_table1_columns = [col for col in selected_columns if col in table1_columns]
        selected_table2_columns = [col for col in selected_columns if col in table2_columns]

        if selected_table1_columns and selected_table2_columns:
            selected_columns_with_separator = selected_table1_columns + ['Separator'] + selected_table2_columns
            uploaded_data['Separator'] = np.nan
        else:
            selected_columns_with_separator = selected_columns

        if selected_columns_with_separator:
            selected_data = uploaded_data[selected_columns_with_separator]
            combined_table, table1_columns, table2_columns = data_processing(selected_data)

            numeric_combined_table = combined_table.select_dtypes(include=[np.number])

            if not numeric_combined_table.empty:
                correlation_matrix = numeric_combined_table.corr(method=correlation_method)
                heatmap_filename = generate_heatmap(correlation_matrix, xtick_rotation, correlation_method)
                dendrogram_filename = generate_dendrogram(correlation_matrix, xtick_rotation, correlation_method)
                return {"heatmap_url": url_for('uploaded_file', filename=heatmap_filename), "dendrogram_url": url_for('uploaded_file', filename=dendrogram_filename)}

    return {"error": "No valid columns selected or no data available."}, 400

@app.route('/sort_columns', methods=['POST'])
def sort_columns():
    global combined_table, table1_columns, table2_columns, correlation_matrix

    if combined_table is not None:
        primary_column = request.form.get('primary_column')
        sort_type = request.form.get('sort_type', 'absolute')
        correlation_method = request.form.get('correlation_method', 'pearson')

        if primary_column and primary_column in combined_table.columns:
            combined_table = combined_table.select_dtypes(include=[np.number])

            correlation_matrix = combined_table.corr(method=correlation_method)

            correlation_matrix = correlation_matrix.dropna(axis=1, how='all').dropna(axis=0, how='all')

            if sort_type == 'absolute':
                correlations_with_primary = correlation_matrix[primary_column].abs().sort_values(ascending=False)
            else:
                correlations_with_primary = correlation_matrix[primary_column].sort_values(ascending=False)

            sorted_columns = correlations_with_primary.index.tolist()
            sorted_combined_table = combined_table[sorted_columns]

            sorted_columns.reverse()
            sorted_combined_table = combined_table[sorted_columns]

            numeric_combined_table = sorted_combined_table.select_dtypes(include=[np.number])
            if not numeric_combined_table.empty:
                correlation_matrix = numeric_combined_table.corr(method=correlation_method)
                heatmap_filename = generate_heatmap(correlation_matrix, xtick_rotation, correlation_method)
                dendrogram_filename = generate_dendrogram(correlation_matrix, xtick_rotation, correlation_method)
                return render_template('heatmap.html', heatmap_filename=heatmap_filename, dendrogram_filename=dendrogram_filename, table1_columns=table1_columns, table2_columns=table2_columns, correlation_method=correlation_method, file_name=filename)

        return render_template('heatmap.html', heatmap_filename=None, table1_columns=table1_columns, table2_columns=table2_columns, correlation_method=correlation_method, file_name='', error_message="Could not find the primary column in the combined table.")

    return render_template('heatmap.html', heatmap_filename=None, table1_columns=[], table2_columns=[], correlation_method='pearson', file_name='', error_message="No combined table available to sort.")

@app.route('/download_combined_table', methods=['GET'])
def download_combined_table():
    global combined_table
    if combined_table is not None:
        unique_id = uuid.uuid4().hex
        combined_filename = f"{filename}_cleaned_{unique_id}.csv"
        combined_path = os.path.join(app.config['UPLOAD_FOLDER'], combined_filename)
        combined_table.to_csv(combined_path, index=False)
        return send_from_directory(app.config['UPLOAD_FOLDER'], combined_filename, as_attachment=True)
    else:
        return jsonify({"error": "No combined data available to download."}), 400

@app.route('/download_heatmap', methods=['GET'])
def download_heatmap():
    global correlation_matrix
    if correlation_matrix is not None:
        unique_id = uuid.uuid4().hex
        heatmap_filename = f"{filename}_corr_{unique_id}.csv"
        heatmap_path = os.path.join(app.config['UPLOAD_FOLDER'], heatmap_filename)
        correlation_matrix.to_csv(heatmap_path)
        return send_from_directory(app.config['UPLOAD_FOLDER'], heatmap_filename, as_attachment=True)
    else:
        return jsonify({"error": "No heatmap data available to download."}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True, port=5003)
