// doctor.js
// Fetch dashboard data and populate doctor.html

document.addEventListener('DOMContentLoaded', function () {
    // Fetch dashboard overview
    fetch('/api/doctor/dashboard', { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            if (data.stats) {
                const cards = document.querySelectorAll('.overview-cards .card');
                if (cards.length >= 4) {
                    cards[0].innerHTML = `<strong>My Patients:</strong> ${data.stats.total_patients}`;
                    cards[1].innerHTML = `<strong>CT Scans Analyzed:</strong> ${data.stats.total_scans}`;
                    cards[2].innerHTML = `<strong>High Risk Patients:</strong> ${data.stats.high_risk_patients}`;
                    cards[3].innerHTML = `<strong>Appointments Today:</strong> ${data.stats.appointments_today}`;
                }
            }
            // Populate recent patients
            const tbody = document.querySelector('.patients tbody');
            if (tbody && data.recent_patients) {
                tbody.innerHTML = '';
                data.recent_patients.forEach(p => {
                    tbody.innerHTML += `
                        <tr>
                            <td>${p.patient_id}</td>
                            <td>${p.full_name || ''}</td>
                            <td>${p.age || ''}</td>
                            <td>${p.last_visit || ''}</td>
                            <td><span class="tag ${p.risk_level === 'High' ? 'red' : p.risk_level === 'Medium' ? 'yellow' : 'green'}">${p.risk_level || ''}</span></td>
                            <td><button class="btn1" onclick="window.location.href='CT_upload.html?patient_id=${p.patient_id}'"><i class="fa-solid fa-plus"></i> Add</button></td>
                        </tr>
                    `;
                });
            }
            // Populate recent scans
            const scanTbody = document.querySelector('.scans tbody');
            if (scanTbody && data.recent_scans) {
                scanTbody.innerHTML = '';
                data.recent_scans.forEach(s => {
                    scanTbody.innerHTML += `
                        <tr>
                            <td>${s.id}</td>
                            <td>${s.patient_id}</td>
                            <td>${s.scan_date}</td>
                            <td>${s.full_name || ''}</td>
                            <td><span class="tag ${s.risk_level === 'High' ? 'red' : s.risk_level === 'Medium' ? 'yellow' : 'green'}">${s.risk_level || ''}</span></td>
                        </tr>
                    `;
                });
            }
        })
        .catch(err => {
            console.error('Error loading dashboard:', err);
        });
});
