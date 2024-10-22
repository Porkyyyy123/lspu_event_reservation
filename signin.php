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

// Check if the user wants to be redirected (based on form checkbox)
$redirect = isset($_POST['redirect']) && $_POST['redirect'] == 'yes';

// Fetch the user from the database
$sql = "SELECT * FROM users WHERE email = ?";
$stmt = $conn->prepare($sql);
$stmt->bind_param("s", $email);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows > 0) {
    $row = $result->fetch_assoc();
    
    // Verify the password
    if (password_verify($password, $row['password'])) {
        // Password is correct, now check the role
        $role = $row['role'];
        $username = $row['name']; // Assuming the 'name' column holds the username

        if ($role == 'admin') {
            echo "Login successful! Welcome, Admin " . $username;
            
            // Optional redirection for admin
            if ($redirect) {
                header("Location: admin_dashboard.php");
                exit();
            }
        } elseif ($role == 'student') {
            echo "Login successful! Welcome, " . $username;
            
            // Optional redirection for student
            if ($redirect) {
                header("Location: student_dashboard.php");
                exit();
            }
        }
    } else {
        // If the password is incorrect
        echo "Invalid password!";
    }
} else {
    // If no user is found with the provided email
    echo "No user found with this email!";
}

$stmt->close();
$conn->close();
?>
