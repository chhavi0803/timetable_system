CREATE DATABASE IF NOT EXISTS timetable_db;

USE timetable_db;

CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    role ENUM('admin', 'teacher', 'student') NOT NULL,
    class_id INT,
    FOREIGN KEY (class_id) REFERENCES class(id)
);

CREATE TABLE IF NOT EXISTS teacher (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    teacher_name VARCHAR(50) NOT NULL,
    class_id INT,
    FOREIGN KEY (user_id) REFERENCES user(id),
   