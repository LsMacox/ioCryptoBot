CREATE USER 'mansur_sheikh'@'%' IDENTIFIED BY 'mansur_krasava';
CREATE DATABASE IF NOT EXISTS main;
GRANT ALL PRIVILEGES ON main.* TO 'mansur_sheikh'@'%';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS main.user_pump_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    pump_interval INT,
    pump_perc_threshold FLOAT,
    is_scan BOOLEAN
);

CREATE TABLE IF NOT EXISTS main.coin_pumps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    exchanger_name VARCHAR(50),
    symbol VARCHAR(50),
    open_interest FLOAT,
    created_at DATETIME
);

CREATE TABLE IF NOT EXISTS main.user_last_coin_pump (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    exchanger_name VARCHAR(50),
    symbol VARCHAR(50),
    last_pump DATETIME
);
