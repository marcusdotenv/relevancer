CREATE TABLE IF NOT EXISTS terms (
    "id"                      SERIAL PRIMARY KEY,
    "term"                    VARCHAR(255) NOT NULL,
    "frequency"               INT DEFAULT 0 
);