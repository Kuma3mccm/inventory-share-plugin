CREATE DATABASE IF NOT EXISTS player_data;

USE player_data;

CREATE TABLE IF NOT EXISTS player_data (
    player_xuid VARCHAR(64) PRIMARY KEY,
    player_inv TEXT DEFAULT NULL,
    is_logged_in TINYTEXT DEFAULT 'False'
);
