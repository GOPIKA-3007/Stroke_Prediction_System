CREATE TABLE ct_scans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    scan_date DATE,
    scan_type VARCHAR(50),
    image_path VARCHAR(255),
    notes TEXT,
    doctor_notes TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

