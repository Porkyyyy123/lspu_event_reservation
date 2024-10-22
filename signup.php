<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Database connection
    include 'db_connect.php'; // Ensure you have the correct database connection file

    // Collect form data
    $username = $_POST['username'];
    $password = $_POST['password'];
    $role = $_POST['role']; // Capturing the role (admin or student)

    // Hash the password for security
    $hashed_password = password_hash($password, PASSWORD_DEFAULT);

    // Insert the user into the database
    $sql = "INSERT INTO users (username, password, role) VALUES (?, ?, ?)";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("sss", $username, $hashed_password, $role);
    
    if ($stmt->execute()) {
        echo "Sign up successful!";
        // Redirect to login page or wherever you'd like
    } else {
        echo "Error: " . $stmt->error;
    }

    $stmt->close();
    $conn->close();
}
?>
