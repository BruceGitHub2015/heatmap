<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Heatmap</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <div class="container">
        <!-- Left Sidebar: Column Headers -->
        <div class="sidebar">
            <h3>Table 1 Columns</h3>
            <button type="button" onclick="selectAll('table1')">Select All</button>
            <button type="button" onclick="selectNone('table1')">Select None</button>
            <form id="update-columns-form">
                {% for column in table1_columns %}
                    <label>
                        <input type="checkbox" name="columns" value="{{ column }}" class="table1" checked>
                        {{ column }}
                    </label>
                {% endfor %}
                <h3>Table 2 Columns</h3>
                <button type="button" onclick="selectAll('table2')">Select All</button>
                <button type="button" onclick="selectNone('table2')">Select None</button>
                {% for column in table2_columns %}
                    <label>
                        <input type="checkbox" name="columns" value="{{ column }}" class="table2" checked>
                        {{ column }}
                    </label>
                {% endfor %}
                <button type="button" id="update-button">Update Columns</button>
            </form>            
        </div>
        
        <!-- Center Content: Heatmap -->
        <div class="content">
            <div id="heatmap-container" class="heatmap-container">
                {% if heatmap_filename %}
                    <img src="/uploads/{{ heatmap_filename }}" alt="Correlation Heatmap">
                {% else %}
                    <p>No data to display in heatmap.</p>
                {% endif %}
            </div>
            <button type="button" id="download-button">Download Combined Table as CSV</button>
            <div id="message-box" style="height: 150px; border: 1px solid #ccc; margin-top: 20px; padding: 10px;">
                {% if error_message %}
                    <p>{{ error_message }}</p>
                {% else %}
                    <p>No errors.</p>
                {% endif %}
            </div>
        </div>
        
        <!-- Right Sidebar: Sort by Column -->
        <div class="sidebar">
            <h3>Sort by Column</h3>
            <form action="/sort_columns" method="post">
                {% for column in table1_columns + table2_columns %}
                    <label>
                        <input type="radio" name="primary_column" value="{{ column }}" required>
                        {{ column }}
                    </label>
                {% endfor %}
                <button type="submit">Sort Heatmap</button>
            </form>
        </div>
    </div>
    <script>
        function selectAll(tableClass) {
            document.querySelectorAll('input.' + tableClass).forEach(cb => cb.checked = true);
        }
        function selectNone(tableClass) {
            document.querySelectorAll('input.' + tableClass).forEach(cb => cb.checked = false);
        }
        document.getElementById('update-button').addEventListener('click', () => {
            const selectedColumns = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
                .map(cb => cb.value);
            fetch('/update_columns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ columns: selectedColumns })
            })
            .then(response => response.json())
            .then(data => {
                if (data.heatmap_url) {
                    document.getElementById('heatmap-container').innerHTML = `<img src="${data.heatmap_url}" alt="Updated Heatmap">`;
                    document.getElementById('message-box').innerHTML = '<p>No errors.</p>'; // Clear any error messages
                } else {
                    document.getElementById('message-box').innerHTML = `<p>${data.error}</p>`;
                }
            });
        });

        document.getElementById('download-button').addEventListener('click', () => {
            fetch('/download_combined_table', {
                method: 'GET'
            })
            .then(response => {
                if (response.status === 200) {
                    return response.blob();
                } else {
                    throw new Error('Failed to download the file.');
                }
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'combined_table.csv';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
                document.getElementById('message-box').innerHTML = `<p>${error.message}</p>`;
            });
        });
    </script>
</body>
</html>
