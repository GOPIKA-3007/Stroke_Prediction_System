const fileInput = document.getElementById("ct_images");
const fileLabel = document.getElementById("fileLabel");

fileInput.addEventListener("change", () => {
  const files = Array.from(fileInput.files);
  if (files.length > 0) {
    const names = files.map(f => f.name).join(", ");
    fileLabel.textContent = names;
  } else {
    fileLabel.textContent = "No files selected";
  }
});

document.addEventListener('DOMContentLoaded', function () {
    const patientSelect = document.getElementById('patientSelect');
    // Fetch patients for dropdown
    fetch('/api/patients/list', { credentials: 'include' })
        .then(res => res.json())
        .then(patients => {
            patientSelect.innerHTML = '';
            patients.forEach(p => {
                patientSelect.innerHTML += `<option value="${p.patient_id}">${p.full_name} (${p.patient_id})</option>`;
            });
        })
        .catch(() => {
            patientSelect.innerHTML = '<option>Error loading patients</option>';
        });

    // Handle CT scan upload
    document.getElementById('ctForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        // Only send the first file for now (backend expects 'scan_image')
        if (formData.has('ct_images[]')) {
            const files = formData.getAll('ct_images[]');
            if (files.length > 0) {
                formData.append('scan_image', files[0]);
            }
            formData.delete('ct_images[]');
        }
        fetch('/api/doctor/upload-scan', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        })
        .then(res => res.json())
        .then(data => {
            if (data.prediction) {
                alert('Prediction: ' + JSON.stringify(data.prediction));
            } else if (data.error) {
                alert('Error: ' + data.error);
            }
        })
        .catch(err => {
            alert('Upload failed: ' + err);
        });
    });
});
