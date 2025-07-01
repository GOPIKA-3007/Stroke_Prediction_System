// admin.js
// Add patient via admin portal and show all patients

document.addEventListener('DOMContentLoaded', function () {
    // Handle add patient form
    document.getElementById('loginForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const form = e.target;
        const data = {
            full_name: form.name.value,
            age: form.age.value,
            gender: form.gender.value,
            date_of_birth: form.dob.value,
            phone_number: form.phone.value,
            address: form.address.value
        };
        fetch('/api/admin/add-patient', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            credentials: 'include'
        })
        .then(res => res.json())
        .then(resp => {
            if (resp.patient_id) {
                alert('Patient added! ID: ' + resp.patient_id);
                loadPatients();
            } else if (resp.error) {
                alert('Error: ' + resp.error);
            }
        })
        .catch(err => alert('Error: ' + err));
    });

    // Load all patients
    function loadPatients() {
        fetch('/api/patients/list', { credentials: 'include' })
            .then(res => res.json())
            .then(patients => {
                const table = document.getElementById('patientsTable');
                if (table) {
                    table.innerHTML = '<tr><th>ID</th><th>Name</th><th>Age</th><th>Gender</th></tr>';
                    patients.forEach(p => {
                        table.innerHTML += `<tr><td>${p.patient_id}</td><td>${p.full_name}</td><td>${p.age}</td><td>${p.gender}</td></tr>`;
                    });
                }
            });
    }
    loadPatients();
});
