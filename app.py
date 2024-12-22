from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
import uuid

# Ensure matplotlib can render Chinese characters
plt.rcParams['font.sans-serif'] = ['SimHei']  # Use SimHei for Chinese
plt.rcParams['axes.unicode_minus'] = False  # Ensure minus signs are rendered correctly
plt.rcParams['xtick.labelsize'] = 12  # Increase x-axis label size
plt.rcParams['ytick.labelsize'] = 12  # Increase y-axis label size

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

uploaded_data = None
heatmap_filename = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global uploaded_data

    if 'file' not in request.files:
        return render_template('error.html', message="No file part in the request.")

    file = request.files['file']

    if file.filename == '':
        return render_template('error.html', message="No file selected.")

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Read the CSV file
        try:
            data = pd.read_csv(filepath, encoding='utf-8')  # Try reading as UTF-8
        except UnicodeDecodeError:
            try:
                data = pd.read_csv(filepath, encoding='gbk')  # Fallback to GBK
            except Exception as e:
                return render_template('error.html', message=f"Unable to read the file: {e}")

        if data.empty or data.shape[1] < 2:
            return render_template('error.html', message="CSV must have at least two columns.")

        # Check if the CSV contains only one table
        split_indices = [i for i, col in enumerate(data.columns) if pd.isna(data.iloc[0, i])]
        table1_columns, table2_columns = [], []

        if not split_indices:
            combined_table = data
            table1_columns = data.columns.tolist()
        else:
            # Handle split into two tables
            split_idx = split_indices[0]
            table1 = data.iloc[:, :split_idx]
            table2 = data.iloc[:, split_idx + 1:]

            # Automatically remove columns with all zeros after splitting
            table1 = table1.loc[:, (table1 != 0).any(axis=0)]
            table2 = table2.loc[:, (table2 != 0).any(axis=0)]

            table1_columns = table1.columns.tolist()
            table2_columns = table2.columns.tolist()

            if table2.empty:
                combined_table = table1
            else:
                # Match rows in the first table to the second table by closest time using column indices
                smaller_time = table2.iloc[:, 1].dropna().sort_values()
                larger_time = table1.iloc[:, 1].dropna().sort_values()

                matched_indices = []
                j = 0
                for t in smaller_time:
                    while j < len(larger_time) - 1 and abs(larger_time.iloc[j + 1] - t) < abs(larger_time.iloc[j] - t):
                        j += 1
                    matched_indices.append(larger_time.index[j])

                matched_rows = table1.loc[matched_indices]

                # Combine the tables
                combined_table = pd.concat([table2.reset_index(drop=True), matched_rows.reset_index(drop=True)], axis=1)

                # Drop timestamp column (column 0) and parse as datetime if necessary
                if pd.api.types.is_string_dtype(combined_table.iloc[:, 0]):
                    combined_table.iloc[:, 0] = pd.to_datetime(combined_table.iloc[:, 0], errors='coerce')
                combined_table = combined_table.drop(columns=[combined_table.columns[0]], errors='ignore')

        uploaded_data = combined_table

        # Generate the heatmap
        if not combined_table.empty:
            numeric_combined_table = combined_table.select_dtypes(include=[np.number])
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
        else:
            heatmap_filename = None

        return render_template('heatmap_layout.html', heatmap_filename=heatmap_filename, 
                               table1_columns=table1_columns, table2_columns=table2_columns)

@app.route('/update_columns', methods=['POST'])
def update_columns():
    global uploaded_data

    if not uploaded_data.empty:
        # Get selected columns from the request
        selected_columns = request.json.get('columns', [])
        numeric_combined_table = uploaded_data[selected_columns].select_dtypes(include=[np.number])

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


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
