// ==============================================================================
// LAB 3: DEBUGGING EXERCISE - BROKEN SERVER
// Student: S. Dinesh Kumar (252U1R1227)
// This file contains 4 deliberate bugs for the debugging practical exercise:
// 1. Bug 1: Port conflict (EADDRINUSE) - Two server listeners on the same port
// 2. Bug 2: Wrong import path - Module cannot be found
// 3. Bug 3: Table-name typo - Querying 'books' instead of 'book' (no such table)
// 4. Bug 4: Missing await on database call - Sending pending Promise instead of rows
// ==============================================================================

// BUG 2: Wrong import/require path (typo in module/file path)
// BROKEN: const sqlite3 = require("./sqlite3-wrong-path");
// FIX: const sqlite3 = require("sqlite3");
const express = require("express");
const path = require("path");
const { open } = require("sqlite");
const sqlite3 = require("sqlite3");

const app = express();
const PORT = 3000;
const dbPath = path.join(__dirname, "../database.db");

app.use(express.json());

let db = null;

const initializeDBAndServer = async () => {
  try {
    db = await open({
      filename: dbPath,
      driver: sqlite3.Database,
    });

    // BUG 1: Port conflict (EADDRINUSE)
    // Starting listener 1
    app.listen(PORT, () => {
      console.log(`First listener on http://localhost:${PORT}`);
    });

    // Attempting a second listener on the exact same port creates EADDRINUSE
    // BROKEN:
    // const secondListener = app.listen(PORT, () => {});
    // FIX: Only call app.listen() once on an available port.
  } catch (error) {
    console.error(`Database Error: ${error.message}`);
  }
};

initializeDBAndServer();

// BUG 3: Table-name typo ("no such table: books")
// Table was created as 'book' (singular), but query uses 'books' (plural)
// BROKEN: const query = "SELECT * FROM books";
// FIX: const query = "SELECT * FROM book";
app.get("/broken-table/", async (req, res) => {
  try {
    const query = "SELECT * FROM books"; // Typo here!
    const result = await db.all(query);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// BUG 4: Missing await on database call
// Omitting 'await' causes db.all() to return a Promise { <pending> } rather than the resolved rows array
// BROKEN: const books = db.all("SELECT * FROM book LIMIT 5");
// FIX: const books = await db.all("SELECT * FROM book LIMIT 5");
app.get("/broken-await/", async (req, res) => {
  try {
    const books = db.all("SELECT * FROM book LIMIT 5"); // Missing await!
    res.json(books); // Express serializes a pending Promise into an empty object {}
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
