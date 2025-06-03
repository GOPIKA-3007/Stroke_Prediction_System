<?php
$host = "localhost";
$username = "root";
$password = "";
$database = "stroke_prediction";

$conn = new mysqli($host, $username, $password, $database);
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Ensure request is POST
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $patient_id = $_POST['patient_id'];
    $scan_date = $_POST['scan_date'];
    $scan_type = $_POST['scan_type'];
    $notes = $_POST['notes'];
    $doctor_notes = $_POST['doctor_notes'] ?? '';

    $upload_dir = "uploads/";
    if (!file_exists($upload_dir)) {
        mkdir($upload_dir, 0777, true);
    }

    $success = false;

    foreach ($_FILES['ct_images']['tmp_name'] as $index => $tmp_name) {
        $original_name = basename($_FILES['ct_images']['name'][$index]);
        $file_path = $upload_dir . time() . "_" . $original_name;

        if (move_uploaded_file($tmp_name, $file_path)) {
            $stmt = $conn->prepare("INSERT INTO ct_scans (patient_id, scan_date, scan_type, image_path, notes, doctor_notes) VALUES (?, ?, ?, ?, ?, ?)");
            $stmt->bind_param("isssss", $patient_id, $scan_date, $scan_type, $file_path, $notes, $doctor_notes);
            $stmt->execute();
            $stmt->close();
            $success = true;
        }
    }

    if ($success) {
        echo "<script>alert('CT Scan uploaded successfully!'); window.location.href='upload_ct.html';</script>";
    } else {
        echo "<script>alert('Upload failed.'); window.history.back();</script>";
    }
} else {
    echo "Invalid request.";
}

$conn->close();
?>
