from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify, make_response
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
import uuid
from data_processing import data_processing

# Ensure matplotlib can render Chinese characters
plt.rcParams['font.sans-serif'] = ['SimHei']  # Use SimHei for Chinese
plt.rcParams['axes.unicode_minus'] = False  # Ensure minus signs are rendered correctly
plt.rcParams['xtick.labelsize'] = 12  # Increase x-axis label size
plt.rcParams['ytick.labelsize'] = 12  # Increase y-axis label size

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

uploaded_data = None
combined_table = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global uploaded_data, combined_table

    if 'file' not in request.files:
        return render_template('heatmap.html', heatmap_filename=None, error_message="No file part in the request.", table1_columns=[], table2_columns=[])

    file = request.files['file']

    if file.filename == '':
        return render_template('heatmap.html', heatmap_filename=None, error_message="No file selected.", table1_columns=[], table2_columns=[])

    if file:
        unique_id = uuid.uuid4().hex
        filename = secure_filename(file.filename)
        unique_filename = f"{unique_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Read the CSV file
        try:
            data = pd.read_csv(filepath, encoding='utf-8')  # Try reading as UTF-8
        except UnicodeDecodeError:
            try:
                data = pd.read_csv(filepath, encoding='gbk')  # Fallback to GBK
            except Exception as e:
                return render_template('heatmap.html', heatmap_filename=None, error_message=f"Unable to read the file: {e}", table1_columns=[], table2_columns=[])

        if data.empty or data.shape[1] < 2:
            return render_template('heatmap.html', heatmap_filename=None, error_message="CSV must have at least two columns.", table1_columns=[], table2_columns=[])

        # Process the data
        combined_table, table1_columns, table2_columns = data_processing(data)
        uploaded_data = data

        return render_template('heatmap.html', heatmap_filename=None, table1_columns=table1_columns, table2_columns=table2_columns, error_message=None)

@app.route('/update_columns', methods=['POST'])
def update_columns():
    global uploaded_data, combined_table

    if not uploaded_data.empty:
        # Get selected columns from the request
        selected_columns = request.json.get('columns', [])
        
        if selected_columns:
            selected_data = uploaded_data[selected_columns]
            combined_table = data_processing(selected_data)[0]

            numeric_combined_table = combined_table.select_dtypes(include=[np.number])

            # Generate the heatmap with the selected columns
            if not numeric_combined_table.empty:
                correlation_matrix = numeric_combined_table.corr()
                plt.figure(figsize=(12, 10))  # Adjust heatmap size
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', cbar_kws={'shrink': 0.75})
                plt.xticks(rotation=45)
                plt.yticks(rotation=0)
                plt.tight_layout()
                unique_id = uuid.uuid4().hex
                heatmap_filename = f"heatmap_{unique_id}.png"
                heatmap_path = os.path.join(app.config['UPLOAD_FOLDER'], heatmap_filename)
                plt.savefig(heatmap_path, bbox_inches='tight')
                plt.close()
                return {"heatmap_url": url_for('uploaded_file', filename=heatmap_filename)}
    return {"error": "No valid columns selected or no data available."}, 400

@app.route('/download_combined_table', methods=['GET'])
def download_combined_table():
    global combined_table
    if combined_table is not None:
        unique_id = uuid.uuid4().hex
        combined_filename = f"combined_table_{unique_id}.csv"
        combined_path = os.path.join(app.config['UPLOAD_FOLDER'], combined_filename)
        combined_table.to_csv(combined_path, index=False)
        return send_from_directory(app.config['UPLOAD_FOLDER'], combined_filename, as_attachment=True)
    else:
        return jsonify({"error": "No combined data available to download."}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
