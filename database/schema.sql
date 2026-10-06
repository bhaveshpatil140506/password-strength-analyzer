-- ============================================================
--  PASSWORD STRENGTH ANALYZER - DATABASE SCHEMA (phpMyAdmin/MySQL)
--  Import this file in phpMyAdmin under the database
--  name: password_analyzer
-- ============================================================

-- CREATE DATABASE IF NOT EXISTS password_analyzer;
-- USE password_analyzer;

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

-- ------------------------------------------------------------
-- TABLE: users (User Registration/Login Module)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT(11) NOT NULL AUTO_INCREMENT,
    fullname VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    security_question VARCHAR(255) DEFAULT NULL,
    security_answer_hash VARCHAR(255) DEFAULT NULL,
    is_admin TINYINT(1) DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    last_login DATETIME DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Opaque API sessions are stored as hashes so client supplied IDs alone
-- never grant access to user or admin data.
CREATE TABLE IF NOT EXISTS api_sessions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id INT(11) NOT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_api_sessions_user_expiry (user_id, expires_at),
    CONSTRAINT fk_api_sessions_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- TABLE: analyzed_passwords (Password Analysis Module / History)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analyzed_passwords (
    id INT(11) NOT NULL AUTO_INCREMENT,
    user_id INT(11) NOT NULL,
    password_placeholder VARCHAR(255) NOT NULL,
    strength_score INT(11) DEFAULT 0,
    strength_label VARCHAR(20) DEFAULT NULL,
    length INT(11) DEFAULT 0,
    has_uppercase TINYINT(1) DEFAULT 0,
    has_lowercase TINYINT(1) DEFAULT 0,
    has_numbers TINYINT(1) DEFAULT 0,
    has_special TINYINT(1) DEFAULT 0,
    character_count DECIMAL(5,2) DEFAULT 0,
    link_speed VARCHAR(30) DEFAULT NULL,
    estimated_crack_time VARCHAR(60) DEFAULT NULL,
    is_common TINYINT(1) DEFAULT 0,
    breached_count INT(11) DEFAULT 0,
    entropy DECIMAL(6,2) DEFAULT 0,
    analysis_notes TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY fk_passwords_user (user_id),
    CONSTRAINT fk_passwords_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- TABLE: common_passwords (Common Password Detection Module)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS common_passwords (
    id INT(11) NOT NULL AUTO_INCREMENT,
    password_hash CHAR(64) NOT NULL,
    password_plaintext VARCHAR(255) DEFAULT NULL,
    appearance_rank INT(11) DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uniq_password_hash (password_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- TABLE: recommendations (Security Recommendations Module)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recommendations (
    id INT(11) NOT NULL AUTO_INCREMENT,
    user_id INT(11) NOT NULL,
    analysis_id INT(11) DEFAULT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    severity VARCHAR(20) DEFAULT 'medium',
    is_applied TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY fk_rec_user (user_id),
    KEY fk_rec_analysis (analysis_id),
    CONSTRAINT fk_rec_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_rec_analysis FOREIGN KEY (analysis_id)
        REFERENCES analyzed_passwords (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- TABLE: reports (Report Generation Module)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id INT(11) NOT NULL AUTO_INCREMENT,
    user_id INT(11) NOT NULL,
    report_type VARCHAR(50) DEFAULT 'full',
    report_format VARCHAR(10) DEFAULT 'html',
    total_analyses INT(11) DEFAULT 0,
    avg_strength DECIMAL(5,2) DEFAULT 0,
    weak_passwords INT(11) DEFAULT 0,
    medium_passwords INT(11) DEFAULT 0,
    strong_passwords INT(11) DEFAULT 0,
    common_detected INT(11) DEFAULT 0,
    recommendations_count INT(11) DEFAULT 0,
    report_data LONGTEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY fk_report_user (user_id),
    CONSTRAINT fk_report_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- TABLE: login_attempts (Audit / Login module)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS login_attempts (
    id INT(11) NOT NULL AUTO_INCREMENT,
    user_id INT(11) DEFAULT NULL,
    username VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    user_agent VARCHAR(255) DEFAULT NULL,
    success TINYINT(1) DEFAULT 0,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY fk_attempt_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- TABLE: admin_activity_log (Admin Dashboard Module)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin_activity_log (
    id INT(11) NOT NULL AUTO_INCREMENT,
    admin_id INT(11) DEFAULT NULL,
    action VARCHAR(255) NOT NULL,
    target_user_id INT(11) DEFAULT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- DEFAULT ADMIN ACCOUNT
-- Created by php_backend/install.php (runs this schema then inserts
-- the admin with a REAL bcrypt hash via password_hash()).
-- Default credentials:  admin / Admin@123
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- SEED DATA: Sample common passwords (top 25)
-- Blinded: only SHA-256 is stored; plaintext kept only as reference.
-- ------------------------------------------------------------
INSERT INTO common_passwords (password_hash, password_plaintext, appearance_rank) VALUES
(SHA2('123456',256), '123456', 1),
(SHA2('password',256), 'password', 2),
(SHA2('123456789',256), '123456789', 3),
(SHA2('12345678',256), '12345678', 4),
(SHA2('12345',256), '12345', 5),
(SHA2('qwerty',256), 'qwerty', 6),
(SHA2('abc123',256), 'abc123', 7),
(SHA2('password1',256), 'password1', 8),
(SHA2('111111',256), '111111', 9),
(SHA2('1234567',256), '1234567', 10),
(SHA2('iloveyou',256), 'iloveyou', 11),
(SHA2('admin',256), 'admin', 12),
(SHA2('welcome',256), 'welcome', 13),
(SHA2('monkey',256), 'monkey', 14),
(SHA2('login',256), 'login', 15),
(SHA2('dragon',256), 'dragon', 16),
(SHA2('master',256), 'master', 17),
(SHA2('letmein',256), 'letmein', 18),
(SHA2('hello',256), 'hello', 19),
(SHA2('freedom',256), 'freedom', 20),
(SHA2('whatever',256), 'whatever', 21),
(SHA2('trustno1',256), 'trustno1', 22),
(SHA2('sunshine',256), 'sunshine', 23),
(SHA2('qwerty123',256), 'qwerty123', 24),
(SHA2('123123',256), '123123', 25),
(SHA2('passw0rd',256), 'passw0rd', 26),
(SHA2('654321',256), '654321', 27),
(SHA2('qazwsx',256), 'qazwsx', 28),
(SHA2('princess',256), 'princess', 29),
(SHA2('football',256), 'football', 30),
(SHA2('ashley',256), 'ashley', 31),
(SHA2('batman',256), 'batman', 32),
(SHA2('superman',256), 'superman', 33),
(SHA2('soccer',256), 'soccer', 34),
(SHA2('jordan',256), 'jordan', 35),
(SHA2('michael',256), 'michael', 36),
(SHA2('shadow',256), 'shadow', 37),
(SHA2('1234',256), '1234', 38),
(SHA2('000000',256), '000000', 39),
(SHA2('qwertyuiop',256), 'qwertyuiop', 40);

-- ------------------------------------------------------------
-- INDEXES / OPTIMIZATION
-- ------------------------------------------------------------
CREATE INDEX idx_passwords_user_time ON analyzed_passwords (user_id, analyzed_at);
CREATE INDEX idx_reports_user_time ON reports (user_id, generated_at);
CREATE INDEX idx_login_attempts_time ON login_attempts (attempted_at);

COMMIT;
