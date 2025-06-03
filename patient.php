<?php
$host = "localhost";
$username = "root";
$password = "";
$database = "stroke_prediction";

$conn = new mysqli($host, $username, $password, $database);
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$sql = "SELECT id, name FROM patients";
$result = $conn->query($sql);

if ($result->num_rows > 0) {
    echo '<option value="">Select a patient</option>';
    while ($row = $result->fetch_assoc()) {
        echo '<option value="' . $row['id'] . '">' . htmlspecialchars($row['name']) . '</option>';
    }
} else {
    echo '<option>No patients found</option>';
}

$conn->close();
?>
