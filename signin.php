<?php
// Database connection
$conn = new mysqli('localhost', 'root', '', 'db_lspu_event_reservation');

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Get form data
$email = $_POST['email'];
$password = $_POST['password'];

// Check if the user exists
$sql = "SELECT * FROM users WHERE email='$email'";
$result = $conn->query($sql);

if ($result->num_rows > 0) {
    $row = $result->fetch_assoc();
    
    // Verify password
    if (password_verify($password, $row['password'])) {
        echo "Login successful! Welcome, " . $row['name'];
    } else {
        echo "Invalid password!";
    }
} else {
    echo "No user found with this email!";
}

$conn->close();
?>
