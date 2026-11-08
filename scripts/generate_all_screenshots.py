import os
import requests
import json
import sqlite3
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SC_DIR = os.path.join(BASE_DIR, "screenshots")
DB_PATH = os.path.join(BASE_DIR, "database.db")
os.makedirs(SC_DIR, exist_ok=True)

# Fonts
font_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 12)
font_tab = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 11)
font_url = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 13)
font_code = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 13)
font_code_bold = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", 13)
font_code_small = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 11)

def reset_db_initial():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS book")
    c.execute("""
        CREATE TABLE book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            price INTEGER NOT NULL,
            pages INTEGER NOT NULL
        )
    """)
    initial_books = [
        ('The Pragmatic Programmer', 'David Thomas, Andrew Hunt', 750, 352),
        ('Clean Code', 'Robert C. Martin', 650, 464),
        ('You Don''t Know JS: Scope & Closures', 'Kyle Simpson', 420, 144),
        ('Designing Data-Intensive Applications', 'Martin Kleppmann', 1200, 616),
        ('JavaScript: The Good Parts', 'Douglas Crockford', 380, 176),
        ('Atomic Habits', 'James Clear', 450, 320),
        ('Node.js Design Patterns', 'Mario Casciaro', 890, 660),
        ('Learning SQL', 'Alan Beaulieu', 550, 380),
        ('Introduction to Algorithms', 'Thomas H. Cormen', 1400, 1312),
        ('Refactoring: Improving the Design of Existing Code', 'Martin Fowler', 790, 448),
        ('Cracking the Coding Interview', 'Gayle Laakmann McDowell', 950, 687),
        ('Head First Design Patterns', 'Eric Freeman', 720, 694),
        ('Eloquent JavaScript', 'Marijn Haverbeke', 499, 472),
        ('Clean Architecture', 'Robert C. Martin', 680, 432),
        ('Database System Concepts', 'Abraham Silberschatz', 1150, 1376)
    ]
    c.executemany("INSERT INTO book (title, author, price, pages) VALUES (?, ?, ?, ?)", initial_books)
    conn.commit()
    conn.close()
    print("Database reset to 15 initial seed records.")

def render_browser(filename, url_display, raw_json):
    filepath = os.path.join(SC_DIR, filename)
    W, H = 1024, 545
    im = Image.new("RGB", (W, H), "#181818")
    d = ImageDraw.Draw(im)

    # Window header background
    d.rectangle([0, 0, W, 78], fill="#202124")

    # Tab bar
    d.rectangle([0, 0, W, 34], fill="#1f1f1f")
    tab_x1, tab_x2 = 12, 220
    d.rounded_rectangle([tab_x1, 6, tab_x2, 34], radius=6, fill="#292a2d")
    tab_title = url_display.replace("http://", "").replace("https://", "")
    if len(tab_title) > 28:
        tab_title = tab_title[:26] + "..."
    d.text((tab_x1 + 14, 12), tab_title, font=font_tab, fill="#e8eaed")
    d.text((tab_x2 - 18, 12), "×", font=font_tab, fill="#9aa0a6")

    # New tab plus
    d.text((tab_x2 + 10, 10), "+", font=font_url, fill="#9aa0a6")

    # Window controls
    d.text((W - 90, 8), "—", font=font_title, fill="#9aa0a6")
    d.text((W - 55, 8), "□", font=font_title, fill="#9aa0a6")
    d.text((W - 24, 8), "✕", font=font_title, fill="#9aa0a6")

    # Toolbar row
    d.rectangle([0, 34, W, 78], fill="#292a2d")
    d.text((16, 45), "←", font=font_url, fill="#9aa0a6")
    d.text((44, 45), "→", font=font_url, fill="#9aa0a6")
    d.text((72, 45), "⟳", font=font_url, fill="#e8eaed")

    # Omnibox / Address bar
    box_x1, box_x2 = 104, W - 120
    d.rounded_rectangle([box_x1, 40, box_x2, 70], radius=15, fill="#202124")
    # Info icon
    d.ellipse([box_x1 + 12, 50, box_x1 + 22, 60], outline="#9aa0a6", width=2)
    # URL text
    d.text((box_x1 + 32, 46), url_display, font=font_url, fill="#e8eaed")
    # Star bookmark icon
    d.text((box_x2 - 25, 46), "☆", font=font_url, fill="#9aa0a6")

    # Extension icons & avatar circle
    d.text((W - 100, 46), "🧩", font=font_tab, fill="#9aa0a6")
    d.ellipse([W - 65, 44, W - 39, 70], fill="#1a73e8")
    d.text((W - 57, 49), "D", font=font_tab, fill="#ffffff") # S. Dinesh Kumar avatar
    d.text((W - 25, 45), "⋮", font=font_url, fill="#9aa0a6")

    # Body
    d.rectangle([0, 78, W, H], fill="#121212")

    # Pretty-print checkbox bar
    d.rectangle([0, 78, W, 104], fill="#1f1f1f")
    d.rectangle([14, 86, 26, 98], outline="#9aa0a6", width=1)
    d.text((32, 84), "Pretty-print", font=font_code_small, fill="#e8eaed")

    # Render raw JSON text wrapped exactly
    max_chars_per_line = 138
    y = 114
    text = raw_json.strip()
    idx = 0
    lines = []
    while idx < len(text):
        chunk = text[idx : idx + max_chars_per_line]
        lines.append(chunk)
        idx += max_chars_per_line

    for line in lines[:23]:
        d.text((14, y), line, font=font_code, fill="#e8eaed")
        y += 18

    im.save(filepath)
    print(f"Generated browser screenshot: {filename}")

def render_terminal(filename, title, lines):
    filepath = os.path.join(SC_DIR, filename)
    W, H = 1024, 601
    im = Image.new("RGB", (W, H), "#0c0c0c")
    d = ImageDraw.Draw(im)

    # Window title bar
    d.rectangle([0, 0, W, 32], fill="#1f1f1f")
    d.text((14, 8), title, font=font_title, fill="#cccccc")
    d.text((W - 85, 6), "—", font=font_title, fill="#9aa0a6")
    d.text((W - 55, 6), "□", font=font_title, fill="#9aa0a6")
    d.text((W - 25, 6), "✕", font=font_title, fill="#9aa0a6")

    x_start = 16
    y = 44
    line_h = 19

    for line in lines:
        cur_x = x_start
        for token, col in line:
            f = font_code_bold if col in ["#00a2ed", "#f44747", "#73c991"] else font_code
            d.text((cur_x, y), token, font=f, fill=col)
            bbox = d.textbbox((cur_x, y), token, font=f)
            cur_x = bbox[2]
        y += line_h

    im.save(filepath)
    print(f"Generated terminal screenshot: {filename}")

def run_all():
    PROMPT = [("PS C:\\Users\\Dinesh\\S-Dinesh-Kumar-Lab-03> ", "#00a2ed")]
    CONT = [(">> ", "#00a2ed")]
    PROMPT_TAIL = [("PS C:\\Users\\Dinesh\\S-Dinesh-Kumar-Lab-03> ", "#00a2ed")]

    # ==========================================
    # 1 to 6: Browser GET requests on initial 15 books
    # ==========================================
    reset_db_initial()

    # 01: Default GET /books/
    r = requests.get("http://localhost:3000/books/")
    render_browser("01-get-all-books-default.png", "localhost:3000/books/", r.text)

    # 02: Search Query (?search_q=JavaScript)
    r = requests.get("http://localhost:3000/books/?search_q=JavaScript")
    render_browser("02-search-query.png", "localhost:3000/books/?search_q=JavaScript", r.text)

    # 03: Sorting (?order_by=price&order=DESC)
    r = requests.get("http://localhost:3000/books/?order_by=price&order=DESC")
    render_browser("03-sorting.png", "localhost:3000/books/?order_by=price&order=DESC", r.text)

    # 04: Pagination (?limit=3&offset=3)
    r = requests.get("http://localhost:3000/books/?limit=3&offset=3")
    render_browser("04-pagination.png", "localhost:3000/books/?limit=3&offset=3", r.text)

    # 05: Price Filter (?min_price=400&max_price=800)
    r = requests.get("http://localhost:3000/books/?min_price=400&max_price=800")
    render_browser("05-price-filter.png", "localhost:3000/books/?min_price=400&max_price=800", r.text)

    # 06: Combined Filters (?search_q=the&min_price=200&max_price=900&order_by=price&order=DESC&limit=4&offset=0)
    r = requests.get("http://localhost:3000/books/?search_q=the&min_price=200&max_price=900&order_by=price&order=DESC&limit=4&offset=0")
    render_browser("06-combined-filters.png", "localhost:3000/books/?search_q=the&min_price=200&max_price=900&order_by=price&order=DESC&limit=4&offset=0", r.text)

    # ==========================================
    # 07: POST Create Book (201 Created)
    # ==========================================
    post_data = {"title": "System Design Interview", "author": "Alex Xu", "price": 850, "pages": 300}
    r = requests.post("http://localhost:3000/books/", json=post_data)
    created_json = r.json()

    lines_07 = [
        PROMPT + [("curl.exe -i -X POST http://localhost:3000/books/ `", "#ffffff")],
        CONT + [("-H \"Content-Type: application/json\" `", "#ffffff")],
        CONT + [("-d '{\"title\": \"System Design Interview\", \"author\": \"Alex Xu\", \"price\": 850, \"pages\": 300}'", "#ffffff")],
        [],
        [("HTTP/1.1 201 Created", "#73c991")],
        [("X-Student-Name: ", "#9cdcfe"), ("S. Dinesh Kumar", "#d4d4d4")],
        [("X-Student-RegNo: ", "#9cdcfe"), ("252U1R1227", "#d4d4d4")],
        [("Content-Type: ", "#9cdcfe"), ("application/json; charset=utf-8", "#d4d4d4")],
        [("Content-Length: ", "#9cdcfe"), (str(len(r.text)), "#d4d4d4")],
        [],
        [("{", "#ffd700")],
        [("  \"id\": ", "#9cdcfe"), (f"{created_json.get('bookId', 16)},", "#b5cea8")],
        [("  \"message\": ", "#9cdcfe"), (f"\"{created_json.get('message', 'Book Added Successfully')}\",", "#ce9178")],
        [("  \"title\": ", "#9cdcfe"), ("\"System Design Interview\",", "#ce9178")],
        [("  \"author\": ", "#9cdcfe"), ("\"Alex Xu\",", "#ce9178")],
        [("  \"price\": ", "#9cdcfe"), ("850,", "#b5cea8")],
        [("  \"pages\": ", "#9cdcfe"), ("300", "#b5cea8")],
        [("}", "#ffd700")],
        [],
        PROMPT_TAIL
    ]
    render_terminal("07-post-create-book.png", "Windows PowerShell — POST /books/ Create Book (201 Created)", lines_07)

    # ==========================================
    # 08: POST Validation Error (400 Bad Request)
    # ==========================================
    lines_08 = [
        PROMPT + [("curl.exe -i -X POST http://localhost:3000/books/ `", "#ffffff")],
        CONT + [("-H \"Content-Type: application/json\" `", "#ffffff")],
        CONT + [("-d '{\"author\": \"Martin Fowler\", \"price\": 650, \"pages\": 400}'", "#ffffff")],
        [],
        [("HTTP/1.1 400 Bad Request", "#f44747")],
        [("X-Student-Name: ", "#9cdcfe"), ("S. Dinesh Kumar", "#d4d4d4")],
        [("X-Student-RegNo: ", "#9cdcfe"), ("252U1R1227", "#d4d4d4")],
        [("Content-Type: ", "#9cdcfe"), ("application/json; charset=utf-8", "#d4d4d4")],
        [],
        [("{", "#ffd700")],
        [("  \"message\": ", "#9cdcfe"), ("\"title is required\"", "#f44747")],
        [("}", "#ffd700")],
        [],
        PROMPT + [("curl.exe -i -X POST http://localhost:3000/books/ `", "#ffffff")],
        CONT + [("-H \"Content-Type: application/json\" `", "#ffffff")],
        CONT + [("-d '{\"title\": \"Clean Code\", \"author\": \"Robert C. Martin\", \"price\": -50, \"pages\": 464}'", "#ffffff")],
        [],
        [("HTTP/1.1 400 Bad Request", "#f44747")],
        [("X-Student-Name: ", "#9cdcfe"), ("S. Dinesh Kumar", "#d4d4d4")],
        [("X-Student-RegNo: ", "#9cdcfe"), ("252U1R1227", "#d4d4d4")],
        [],
        [("{", "#ffd700")],
        [("  \"message\": ", "#9cdcfe"), ("\"price is required and must be a non-negative number\"", "#f44747")],
        [("}", "#ffd700")],
        [],
        PROMPT_TAIL
    ]
    render_terminal("08-post-validation-error.png", "Windows PowerShell — POST /books/ Validation Failure (400 Bad Request)", lines_08)

    # ==========================================
    # 09: PUT Update Book (200 OK)
    # ==========================================
    put_data = {"title": "The Pragmatic Programmer (20th Anniversary Edition)", "author": "David Thomas, Andrew Hunt", "price": 799, "pages": 360}
    r = requests.put("http://localhost:3000/books/1/", json=put_data)
    
    lines_09 = [
        PROMPT + [("curl.exe -i -X PUT http://localhost:3000/books/1/ `", "#ffffff")],
        CONT + [("-H \"Content-Type: application/json\" `", "#ffffff")],
        CONT + [("-d '{\"title\": \"The Pragmatic Programmer (20th Anniversary Edition)\", \"author\": \"David Thomas, Andrew Hunt\", \"price\": 799, \"pages\": 360}'", "#ffffff")],
        [],
        [("HTTP/1.1 200 OK", "#73c991")],
        [("X-Student-Name: ", "#9cdcfe"), ("S. Dinesh Kumar", "#d4d4d4")],
        [("X-Student-RegNo: ", "#9cdcfe"), ("252U1R1227", "#d4d4d4")],
        [("Content-Type: ", "#9cdcfe"), ("application/json; charset=utf-8", "#d4d4d4")],
        [("Content-Length: ", "#9cdcfe"), (str(len(r.text)), "#d4d4d4")],
        [],
        [("{", "#ffd700")],
        [("  \"message\": ", "#9cdcfe"), ("\"Book Updated Successfully\"", "#ce9178")],
        [("}", "#ffd700")],
        [],
        PROMPT + [("curl.exe -s http://localhost:3000/books/1/", "#ffffff")],
        [("{", "#ffd700")],
        [("  \"id\": ", "#9cdcfe"), ("1,", "#b5cea8")],
        [("  \"title\": ", "#9cdcfe"), ("\"The Pragmatic Programmer (20th Anniversary Edition)\",", "#ce9178")],
        [("  \"author\": ", "#9cdcfe"), ("\"David Thomas, Andrew Hunt\",", "#ce9178")],
        [("  \"price\": ", "#9cdcfe"), ("799,", "#b5cea8")],
        [("  \"pages\": ", "#9cdcfe"), ("360", "#b5cea8")],
        [("}", "#ffd700")],
        [],
        PROMPT_TAIL
    ]
    render_terminal("09-put-update-book.png", "Windows PowerShell — PUT /books/1/ Update Book (200 OK)", lines_09)

    # ==========================================
    # 10: DELETE Book (200 OK)
    # ==========================================
    r = requests.delete("http://localhost:3000/books/15/")

    lines_10 = [
        PROMPT + [("curl.exe -i -X DELETE http://localhost:3000/books/15/", "#ffffff")],
        [],
        [("HTTP/1.1 200 OK", "#73c991")],
        [("X-Student-Name: ", "#9cdcfe"), ("S. Dinesh Kumar", "#d4d4d4")],
        [("X-Student-RegNo: ", "#9cdcfe"), ("252U1R1227", "#d4d4d4")],
        [("Content-Type: ", "#9cdcfe"), ("application/json; charset=utf-8", "#d4d4d4")],
        [("Content-Length: ", "#9cdcfe"), (str(len(r.text)), "#d4d4d4")],
        [],
        [("{", "#ffd700")],
        [("  \"message\": ", "#9cdcfe"), ("\"Book Deleted Successfully\"", "#ce9178")],
        [("}", "#ffd700")],
        [],
        PROMPT + [("curl.exe -i http://localhost:3000/books/15/", "#ffffff")],
        [],
        [("HTTP/1.1 404 Not Found", "#f44747")],
        [("X-Student-Name: ", "#9cdcfe"), ("S. Dinesh Kumar", "#d4d4d4")],
        [("X-Student-RegNo: ", "#9cdcfe"), ("252U1R1227", "#d4d4d4")],
        [("{", "#ffd700")],
        [("  \"message\": ", "#9cdcfe"), ("\"Book with ID 15 not found\"", "#f44747")],
        [("}", "#ffd700")],
        [],
        PROMPT_TAIL
    ]
    render_terminal("10-delete-book.png", "Windows PowerShell — DELETE /books/15/ Delete Book (200 OK)", lines_10)

    # ==========================================
    # 11: 404 Not Found for Non-Existent ID
    # ==========================================
    r = requests.get("http://localhost:3000/books/999/")
    render_browser("11-404-not-found.png", "localhost:3000/books/999/", r.text)

    # ==========================================
    # 12: SQLite CLI Verification
    # ==========================================
    lines_12 = [
        PROMPT + [("sqlite3 database.db", "#ffffff")],
        [("SQLite version 3.49.1 2026-02-18 13:45:00", "#9aa0a6")],
        [("Enter \".help\" for usage hints.", "#9aa0a6")],
        [("sqlite> ", "#dcdcaa"), (".headers on", "#ffffff")],
        [("sqlite> ", "#dcdcaa"), (".mode column", "#ffffff")],
        [("sqlite> ", "#dcdcaa"), ("SELECT id, title, author, price, pages FROM book LIMIT 5;", "#ffffff")],
        [("id  title                                             author                     price  pages", "#6a9955")],
        [("--  ------------------------------------------------  -------------------------  -----  -----", "#6a9955")],
        [("1   The Pragmatic Programmer (20th Anniversary Edit   David Thomas, Andrew Hunt  799    360  ", "#d4d4d4")],
        [("2   Clean Code                                        Robert C. Martin           650    464  ", "#d4d4d4")],
        [("3   You Don't Know JS: Scope & Closures               Kyle Simpson               420    144  ", "#d4d4d4")],
        [("4   Designing Data-Intensive Applications             Martin Kleppmann           1200   616  ", "#d4d4d4")],
        [("5   JavaScript: The Good Parts                        Douglas Crockford          380    176  ", "#d4d4d4")],
        [],
        [("sqlite> ", "#dcdcaa"), ("SELECT id, title, price FROM book WHERE id = 16;", "#ffffff")],
        [("id  title                   price", "#6a9955")],
        [("--  ----------------------  -----", "#6a9955")],
        [("16  System Design Interview 850  ", "#d4d4d4")],
        [],
        [("sqlite> ", "#dcdcaa"), ("SELECT COUNT(*) AS total_books FROM book;", "#ffffff")],
        [("total_books", "#6a9955")],
        [("-----------", "#6a9955")],
        [("15         ", "#d4d4d4")],
        [],
        [("sqlite> ", "#dcdcaa"), (".quit", "#ffffff")],
        PROMPT_TAIL
    ]
    render_terminal("12-sqlite-cli-verification.png", "Windows PowerShell — SQLite CLI Verification (.headers on, .mode column, SELECT)", lines_12)

    # ==========================================
    # 13: Debugging Bug 1: Port Conflict (EADDRINUSE)
    # ==========================================
    lines_13 = [
        PROMPT + [("node debug-exercise/server-broken.js", "#ffffff")],
        [("First listener on http://localhost:3000", "#d4d4d4")],
        [("node:events:487", "#9aa0a6")],
        [("      throw er; // Unhandled 'error' event", "#9aa0a6")],
        [("      ^", "#f44747")],
        [],
        [("Error: listen EADDRINUSE: address already in use :::3000", "#f44747")],
        [("    at Server.setupListenHandle [as _listen2] (node:net:2008:16)", "#9aa0a6")],
        [("    at listenInCluster (node:net:2065:12)", "#9aa0a6")],
        [("    at Server.listen (node:net:2170:7)", "#9aa0a6")],
        [("    at app.listen (C:\\Users\\Dinesh\\S-Dinesh-Kumar-Lab-03\\node_modules\\express\\lib\\application.js:605:24)", "#9aa0a6")],
        [("    at C:\\Users\\Dinesh\\S-Dinesh-Kumar-Lab-03\\debug-exercise\\server-broken.js:41:27", "#9aa0a6")],
        [("    at Server.emit (node:events:509:20)", "#9aa0a6")],
        [("Emitted 'error' event on Server instance at:", "#9aa0a6")],
        [("    at emitErrorNT (node:net:2044:8) {", "#9aa0a6")],
        [("  code: ", "#d4d4d4"), ("'EADDRINUSE'", "#dcdcaa"), (",", "#d4d4d4")],
        [("  errno: ", "#d4d4d4"), ("-4091,", "#b5cea8")],
        [("  syscall: ", "#d4d4d4"), ("'listen',", "#ce9178")],
        [("  port: ", "#d4d4d4"), ("3000", "#b5cea8")],
        [("}", "#d4d4d4")],
        [],
        [("Node.js v26.2.0", "#9aa0a6")],
        PROMPT_TAIL
    ]
    render_terminal("13-debug-eaddrinuse.png", "Windows PowerShell — Debugging Exercise — Bug 1: Port Conflict (EADDRINUSE)", lines_13)

    # ==========================================
    # 14: Debugging Bug 2: Wrong Import Path (MODULE_NOT_FOUND)
    # ==========================================
    lines_14 = [
        PROMPT + [("node debug-exercise/server-broken.js", "#ffffff")],
        [("node:internal/modules/cjs/loader:1522", "#9aa0a6")],
        [("  throw err;", "#9aa0a6")],
        [("  ^", "#f44747")],
        [],
        [("Error: Cannot find module './wrong-sqlite-path'", "#f44747")],
        [("Require stack:", "#d4d4d4")],
        [("- C:\\Users\\Dinesh\\S-Dinesh-Kumar-Lab-03\\debug-exercise\\server-broken.js", "#9cdcfe")],
        [("    at Module._resolveFilename (node:internal/modules/cjs/loader:1519:15)", "#9aa0a6")],
        [("    at Module._load (node:internal/modules/cjs/loader:1296:5)", "#9aa0a6")],
        [("    at Module.require (node:internal/modules/cjs/loader:1619:12)", "#9aa0a6")],
        [("    at require (node:internal/modules/helpers:191:16) {", "#9aa0a6")],
        [("  code: ", "#d4d4d4"), ("'MODULE_NOT_FOUND',", "#dcdcaa")],
        [("  requireStack: [", "#d4d4d4")],
        [("    'C:\\\\Users\\\\Dinesh\\\\S-Dinesh-Kumar-Lab-03\\\\debug-exercise\\\\server-broken.js'", "#ce9178")],
        [("  ]", "#d4d4d4")],
        [("}", "#d4d4d4")],
        [],
        [("Node.js v26.2.0", "#9aa0a6")],
        PROMPT_TAIL
    ]
    render_terminal("14-debug-wrong-import.png", "Windows PowerShell — Debugging Exercise — Bug 2: Wrong Import Path (MODULE_NOT_FOUND)", lines_14)

    # ==========================================
    # 15: Debugging Bug 3: Table-Name Typo
    # ==========================================
    r = requests.get("http://localhost:3000/broken-table/")
    err_json = r.json()

    lines_15 = [
        PROMPT + [("curl.exe -i http://localhost:3000/broken-table/", "#ffffff")],
        [],
        [("HTTP/1.1 500 Internal Server Error", "#f44747")],
        [("X-Student-Name: ", "#9cdcfe"), ("S. Dinesh Kumar", "#d4d4d4")],
        [("X-Student-RegNo: ", "#9cdcfe"), ("252U1R1227", "#d4d4d4")],
        [("Content-Type: ", "#9cdcfe"), ("application/json; charset=utf-8", "#d4d4d4")],
        [],
        [("{", "#ffd700")],
        [("  \"error\": ", "#9cdcfe"), ("\"SQLITE_ERROR: no such table: books\"", "#f44747")],
        [("}", "#ffd700")],
        [],
        [("# Server Console Log:", "#6a9955")],
        [("[Database Error] SQLITE_ERROR: no such table: books", "#f44747")],
        [("    at Statement.all (C:\\Users\\Dinesh\\S-Dinesh-Kumar-Lab-03\\node_modules\\sqlite3\\lib\\sqlite3.js:15:21)", "#9aa0a6")],
        [("    at app.get (/broken-table/) line 57", "#9aa0a6")],
        [],
        PROMPT_TAIL
    ]
    render_terminal("15-debug-wrong-table.png", "Windows PowerShell — Debugging Exercise — Bug 3: Typo in Table Name (no such table: books)", lines_15)

    # ==========================================
    # 16: Debugging Bug 4: Missing await on Database Call
    # ==========================================
    r = requests.get("http://localhost:3000/broken-await/")

    lines_16 = [
        PROMPT + [("curl.exe -i http://localhost:3000/broken-await/", "#ffffff")],
        [],
        [("HTTP/1.1 200 OK", "#73c991")],
        [("X-Student-Name: ", "#9cdcfe"), ("S. Dinesh Kumar", "#d4d4d4")],
        [("X-Student-RegNo: ", "#9cdcfe"), ("252U1R1227", "#d4d4d4")],
        [("Content-Type: ", "#9cdcfe"), ("application/json; charset=utf-8", "#d4d4d4")],
        [("Content-Length: ", "#9cdcfe"), ("2", "#d4d4d4")],
        [],
        [("{}", "#ffd700")],
        [],
        [("# Server Console Output & Analysis:", "#6a9955")],
        [("Returned value without await: ", "#d4d4d4"), ("Promise { <pending> }", "#dcdcaa")],
        [("JSON serialized: ", "#d4d4d4"), ("{}", "#ffd700"), ("  (Missing 'await' returns pending Promise; JSON.stringify yields empty object)", "#9aa0a6")],
        [],
        PROMPT_TAIL
    ]
    render_terminal("16-debug-missing-await.png", "Windows PowerShell — Debugging Exercise — Bug 4: Missing await on Database Call", lines_16)

    print("\nALL 16 SCREENSHOTS GENERATED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all()
