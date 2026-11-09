import json
import re
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "contact.db"
MAX_REQUEST_SIZE = 16_384
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ContactHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/contact":
            self._send_json(404, {"success": False, "message": "API-Endpunkt nicht gefunden."})
            return

        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self._send_json(415, {"success": False, "message": "Die Anfrage muss JSON enthalten."})
            return

        try:
            request_size = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send_json(400, {"success": False, "message": "Die Anfrage hat keine gültige Länge."})
            return

        if request_size <= 0:
            self._send_json(400, {"success": False, "message": "Die Anfrage enthält keine Daten."})
            return
        if request_size > MAX_REQUEST_SIZE:
            self._send_json(413, {"success": False, "message": "Die Nachricht ist zu groß."})
            return

        try:
            data = json.loads(self.rfile.read(request_size))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"success": False, "message": "Die Formulardaten sind ungültig."})
            return

        if not isinstance(data, dict):
            self._send_json(400, {"success": False, "message": "Die Formulardaten haben ein ungültiges Format."})
            return

        fields = (
            ("email", "E-Mail", 254, True),
            ("betreff", "Betreff", 200, True),
            ("nachricht", "Nachricht", 10000, True),
            ("name", "Name", 100, False),
            ("vorname", "Vorname", 100, False),
            ("telefon", "Telefon", 40, False),
        )
        values = {}
        for key, label, max_length, required in fields:
            value = data.get(key, "")
            if not isinstance(value, str):
                self._send_json(400, {"success": False, "message": f"Das Feld „{label}“ ist ungültig."})
                return

            value = value.strip()
            if required and not value:
                self._send_json(400, {"success": False, "message": f"Bitte fülle das Feld „{label}“ aus."})
                return
            if len(value) > max_length:
                self._send_json(400, {"success": False, "message": f"Das Feld „{label}“ ist zu lang."})
                return
            values[key] = value or None

        if not EMAIL_PATTERN.fullmatch(values["email"]):
            self._send_json(400, {"success": False, "message": "Bitte gib eine gültige E-Mail-Adresse ein."})
            return

        try:
            with sqlite3.connect(DATABASE, timeout=5) as connection:
                connection.execute(
                    """
                    INSERT INTO contact_messages
                        (email, betreff, nachricht, name, vorname, telefon)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        values["email"],
                        values["betreff"],
                        values["nachricht"],
                        values["name"],
                        values["vorname"],
                        values["telefon"],
                    ),
                )
        except sqlite3.Error as error:
            self.log_error("Could not save contact message: %s", error)
            self._send_json(
                500,
                {
                    "success": False,
                    "message": "Die Nachricht konnte nicht in der Datenbank gespeichert werden. Bitte versuche es später erneut.",
                },
            )
            return

        self._send_json(201, {"success": True, "message": "Danke! Deine Nachricht wurde erfolgreich gesendet."})


def initialize_database():
    with sqlite3.connect(DATABASE) as connection:
        connection.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))


if __name__ == "__main__":
    initialize_database()
    server = HTTPServer(("127.0.0.1", 8000), ContactHandler)
    print("Kontaktformular läuft unter http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer beendet.")
    finally:
        server.server_close()
