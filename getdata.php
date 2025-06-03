<?php
// Database config (adjust these as per your setup)
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "stroke_prediction";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check for connection error
if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

// Assume patient is logged in and their ID is known (e.g., from session)
$patient_id = 1; // Replace this with actual patient ID from session/login system

// Fetch latest scan result
$sql = "SELECT * FROM scan_results WHERE patient_id = $patient_id ORDER BY scan_date DESC LIMIT 1";
$result = $conn->query($sql);

$response = [];

if ($result->num_rows > 0) {
  $row = $result->fetch_assoc();
  $response = [
    "scan_image" => $row["scan_image"],
    "scan_type" => $row["scan_type"],
    "scan_date" => $row["scan_date"],
    "analysis_result" => $row["analysis_result"],
    "stroke_probability" => $row["stroke_probability"],
    "model_confidence" => $row["model_confidence"],
    "recommendations" => $row["recommendations"],
    "doctor_notes" => $row["doctor_notes"]
  ];
}

$conn->close();

header('Content-Type: application/json');
echo json_encode($response);
?>
