CREATE DATABASE IF NOT EXISTS lookupapis;
USE lookupapis;

CREATE TABLE IF NOT EXISTS apis (
    api_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    endpoint_url VARCHAR(500) NOT NULL,
    documentation_url VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL DEFAULT 'GET',
    requires_auth TINYINT(1) NOT NULL DEFAULT 0
);
