create database students;
USE students;

-- 2. Create the Students table
CREATE TABLE Students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    security_q VARCHAR(255) NOT NULL,
    security_a VARCHAR(255) NOT NULL,
    total_fee INT NOT NULL,
    fee_paid INT DEFAULT 0
);

-- 3. Create the Subjects table
CREATE TABLE Subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    subject_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE
);

-- 4. Create the Marks table
CREATE TABLE Marks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    subject_name VARCHAR(100) NOT NULL,
    score INT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE
);
