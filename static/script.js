document.addEventListener('DOMContentLoaded', function() {
    // Handle file upload and generate heatmap
    document.getElementById('upload-button').addEventListener('click', function() {
        const formData = new FormData(document.getElementById('file-upload-form'));
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            document.open();
            document.write(html);
            document.close();
        });
    });

    // Handle update plot button click
    document.getElementById('update-button').addEventListener('click', () => {
        const selectedColumns = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
            .map(cb => cb.value);
        const correlationMethod = document.getElementById('correlation-method').value;

        fetch('/update_columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: selectedColumns, correlation_method: correlationMethod })
        })
        .then(response => response.json())
        .then(data => {
            if (data.heatmap_url) {
                document.getElementById('heatmap-container').innerHTML = `<img src="${data.heatmap_url}" alt="Updated Heatmap">`;
            } else {
                alert(data.error);
            }
        });
    });

    // Handle sort button click
    document.querySelector('form[action="/sort_columns"]').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        formData.append('correlation_method', document.getElementById('correlation-method').value);

        fetch('/sort_columns', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            document.open();
            document.write(html);
            document.close();
        });
    });

    // Handle download combined data button click
    document.getElementById('download-combined-button').addEventListener('click', () => {
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
            alert(error.message);
        });
    });

    // Handle download heatmap data button click
    document.getElementById('download-heatmap-button').addEventListener('click', () => {
        fetch('/download_heatmap', {
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
            a.download = 'heatmap_data.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            alert(error.message);
        });
    });
});

function selectAll(tableClass) {
    document.querySelectorAll('input.' + tableClass).forEach(cb => cb.checked = true);
}

function selectNone(tableClass) {
    document.querySelectorAll('input.' + tableClass).forEach(cb => cb.checked = false);
}
