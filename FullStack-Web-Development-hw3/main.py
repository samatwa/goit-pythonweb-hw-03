from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
from jinja2 import Environment, FileSystemLoader, Template
import json
from datetime import datetime


# Абсолютний шлях до папки, де знаходиться main.py
BASE_DIR = pathlib.Path(__file__).parent

# Створюємо директорію 'storage', якщо вона не існує
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

# Файл для збереження повідомлень
DATA_FILE = STORAGE_DIR / "data.json"

# Налаштування Jinja2
env = Environment(loader=FileSystemLoader(BASE_DIR / "templates"))


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/" or pr_url.path == "/index.html":
            self.send_html_file("index.html")
        elif pr_url.path == "/message.html":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            self.handle_read("read.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            data = urllib.parse.parse_qs(post_data)

            username = data.get("username", [""])[0]
            message = data.get("message", [""])[0]

            now = datetime.now().isoformat()
            entry = {now: {"username": username, "message": message}}

            if DATA_FILE.exists():
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
            else:
                old_data = {}

            old_data.update(entry)

            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(old_data, f, ensure_ascii=False, indent=2)

            self.send_response(302)
            self.send_header("Location", "/message.html")
            self.end_headers()
        else:
            self.send_html_file("error.html", 404)

    def send_html_file(self, filename, status=200):
        file_path = BASE_DIR / "templates" / filename
        if not file_path.exists():
            self.send_response(404)
            self.end_headers()
            return
    
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        with open(file_path, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def handle_read(self, filename):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        template = env.get_template(filename)

        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as fd:
                data = json.load(fd)
        else:
            data = {}

        html = template.render(messages=data)
        self.wfile.write(html.encode("utf-8"))


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
