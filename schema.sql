CREATE TABLE IF NOT EXISTS contact_messages (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL CHECK (length(trim(email)) BETWEEN 3 AND 254),
    betreff TEXT NOT NULL CHECK (length(trim(betreff)) BETWEEN 1 AND 200),
    name TEXT CHECK (name IS NULL OR length(name) <= 100),
    vorname TEXT CHECK (vorname IS NULL OR length(vorname) <= 100),
    telefon TEXT CHECK (telefon IS NULL OR length(telefon) <= 40),
    nachricht TEXT NOT NULL CHECK (length(trim(nachricht)) BETWEEN 1 AND 10000),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contact_messages_email
    ON contact_messages (email);
