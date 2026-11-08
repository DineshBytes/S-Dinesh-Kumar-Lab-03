const express = require("express");
const path = require("path");
const { open } = require("sqlite");
const sqlite3 = require("sqlite3");

const app = express();
const PORT = process.env.PORT || 3000;
const dbPath = path.join(__dirname, "database.db");

// Middleware to parse incoming JSON request bodies
app.use(express.json());

// Student identification header middleware
app.use((req, res, next) => {
  res.setHeader("X-Student-Name", "S. Dinesh Kumar");
  res.setHeader("X-Student-RegNo", "252U1R1227");
  next();
});

let db = null;

// Initialize Database connection and start Express server
const initializeDBAndServer = async () => {
  try {
    db = await open({
      filename: dbPath,
      driver: sqlite3.Database,
    });

    // Create the book table if it does not exist
    await db.exec(`
      CREATE TABLE IF NOT EXISTS book (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        price INTEGER NOT NULL,
        pages INTEGER NOT NULL
      )
    `);

    // Ensure database contains at least 15 varied book records for testing
    const count = await db.get("SELECT COUNT(*) as total FROM book");
    if (count.total < 15) {
      await db.exec(`DELETE FROM book`);
      await db.exec(`
        INSERT INTO book (title, author, price, pages) VALUES
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
      `);
      console.log("Seeded database with 15 realistic book records.");
    }

    const server = app.listen(PORT, () => {
      console.log(`Server initialized for S. Dinesh Kumar (252U1R1227)`);
      console.log(`Server is running at http://localhost:${PORT}`);
    });

    // Friendly error handling for port conflicts (EADDRINUSE)
    server.on("error", (error) => {
      if (error.code === "EADDRINUSE") {
        console.error(
          `[Port Conflict] Port ${PORT} is already in use. Please terminate the process using this port or specify another port using PORT=<number>.`
        );
      } else {
        console.error(`[Server Error] ${error.message}`);
      }
    });
  } catch (error) {
    console.error(`Database Initialization Error: ${error.message}`);
    process.exit(1);
  }
};

initializeDBAndServer();

// ==========================================
// ROOT ROUTE - API DIRECTORY & STUDENT INFO
// ==========================================
app.get("/", (req, res) => {
  res.status(200).json({
    message: "Welcome to Backend Development Fundamentals - Lab 3 (REST API, Query Parameters, Validation & Debugging)",
    student: "S. Dinesh Kumar",
    registrationNumber: "252U1R1227",
    section: "CSE-2E 211",
    college: "Aurora Deemed-to-be-University",
    faculty: "Mr Yugandhar Gurjalwar",
    endpoints: {
      listBooksWithFilters: "GET /books/?search_q=&order_by=id&order=ASC&limit=10&offset=0&min_price=&max_price=",
      getSingleBook: "GET /books/:bookId/",
      addBook: "POST /books/",
      updateBook: "PUT /books/:bookId/",
      deleteBook: "DELETE /books/:bookId/"
    }
  });
});

// ==========================================
// REST ENDPOINTS
// ==========================================

// 1. GET /books/ - List books with Query Parameters (Search, Sort, Pagination, Price Range)
app.get("/books/", async (req, res, next) => {
  try {
    const {
      search_q = "",
      order_by = "id",
      order = "ASC",
      limit = "10",
      offset = "0",
      min_price,
      max_price,
    } = req.query;

    // --- SECURITY NOTE: ORDER BY WHITELIST VALIDATION ---
    // In SQL, ? placeholders are strictly reserved for literal values (strings, numbers).
    // Identifiers such as column names and keywords (ASC/DESC) CANNOT be parameterized.
    // To prevent SQL injection, order_by and order MUST be validated against a strict whitelist in JavaScript.
    const allowedOrderBy = ["id", "title", "author", "price", "pages"];
    const normalizedOrderBy = order_by.toLowerCase();
    if (!allowedOrderBy.includes(normalizedOrderBy)) {
      return res.status(400).json({
        message: `Invalid order_by field. Allowed fields: ${allowedOrderBy.join(", ")}`,
      });
    }

    const normalizedOrder = order.toUpperCase();
    if (normalizedOrder !== "ASC" && normalizedOrder !== "DESC") {
      return res.status(400).json({
        message: "Invalid order value. Allowed values: ASC, DESC",
      });
    }

    // --- PAGINATION VALIDATION ---
    const parsedLimit = Number(limit);
    if (!Number.isInteger(parsedLimit) || parsedLimit < 0) {
      return res.status(400).json({
        message: "limit must be a non-negative integer",
      });
    }

    const parsedOffset = Number(offset);
    if (!Number.isInteger(parsedOffset) || parsedOffset < 0) {
      return res.status(400).json({
        message: "offset must be a non-negative integer",
      });
    }

    // --- PRICE FILTER VALIDATION ---
    if (min_price !== undefined) {
      const parsedMin = Number(min_price);
      if (isNaN(parsedMin) || parsedMin < 0) {
        return res.status(400).json({
          message: "min_price must be a non-negative number",
        });
      }
    }

    if (max_price !== undefined) {
      const parsedMax = Number(max_price);
      if (isNaN(parsedMax) || parsedMax < 0) {
        return res.status(400).json({
          message: "max_price must be a non-negative number",
        });
      }
    }

    if (min_price !== undefined && max_price !== undefined) {
      if (Number(min_price) > Number(max_price)) {
        return res.status(400).json({
          message: "min_price cannot be greater than max_price",
        });
      }
    }

    // --- SQL QUERY CONSTRUCTION (Parameterized for data values) ---
    const conditions = [];
    const queryParams = [];

    // Partial search on title using LIKE with ? parameter
    if (search_q.trim() !== "") {
      conditions.push("title LIKE ?");
      queryParams.push(`%${search_q.trim()}%`);
    }

    // Price range filtering (BETWEEN or separate conditions)
    if (min_price !== undefined && max_price !== undefined) {
      conditions.push("price BETWEEN ? AND ?");
      queryParams.push(Number(min_price), Number(max_price));
    } else if (min_price !== undefined) {
      conditions.push("price >= ?");
      queryParams.push(Number(min_price));
    } else if (max_price !== undefined) {
      conditions.push("price <= ?");
      queryParams.push(Number(max_price));
    }

    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

    // Assemble SQL using whitelisted identifiers and ? parameterized data values
    const query = `
      SELECT * FROM book
      ${whereClause}
      ORDER BY ${normalizedOrderBy} ${normalizedOrder}
      LIMIT ? OFFSET ?
    `;
    queryParams.push(parsedLimit, parsedOffset);

    const books = await db.all(query, queryParams);
    res.status(200).json(books);
  } catch (error) {
    next(error);
  }
});

// Helper function to validate request body for POST & PUT
const validateBookBody = (body) => {
  const { title, author, price, pages } = body;

  if (!title || typeof title !== "string" || title.trim() === "") {
    return "title is required";
  }

  if (!author || typeof author !== "string" || author.trim() === "") {
    return "author is required";
  }

  if (price === undefined || typeof price !== "number" || isNaN(price) || price < 0) {
    return "price is required and must be a non-negative number";
  }

  if (pages !== undefined && (!Number.isInteger(pages) || pages <= 0)) {
    return "pages must be a positive integer";
  }

  return null;
};

// 2. GET /books/:bookId/ - Retrieve a single book
app.get("/books/:bookId/", async (req, res, next) => {
  try {
    const { bookId } = req.params;
    const parsedId = Number(bookId);

    if (!Number.isInteger(parsedId) || parsedId <= 0) {
      return res.status(400).json({
        message: "Invalid bookId format. Must be a positive integer",
      });
    }

    const query = "SELECT * FROM book WHERE id = ?";
    const book = await db.get(query, [parsedId]);

    if (!book) {
      return res.status(404).json({
        message: `Book with ID ${parsedId} not found`,
      });
    }

    res.status(200).json(book);
  } catch (error) {
    next(error);
  }
});

// 3. POST /books/ - Create a new book
app.post("/books/", async (req, res, next) => {
  try {
    const validationError = validateBookBody(req.body);
    if (validationError) {
      return res.status(400).json({ message: validationError });
    }

    const { title, author, price, pages = 100 } = req.body;

    const query = "INSERT INTO book (title, author, price, pages) VALUES (?, ?, ?, ?)";
    const result = await db.run(query, [title.trim(), author.trim(), price, pages]);

    res.status(201).json({
      message: "Book Added Successfully",
      bookId: result.lastID,
    });
  } catch (error) {
    next(error);
  }
});

// 4. PUT /books/:bookId/ - Update an existing book
app.put("/books/:bookId/", async (req, res, next) => {
  try {
    const { bookId } = req.params;
    const parsedId = Number(bookId);

    if (!Number.isInteger(parsedId) || parsedId <= 0) {
      return res.status(400).json({
        message: "Invalid bookId format. Must be a positive integer",
      });
    }

    // Check if the record exists first so missing ID returns 404
    const existingBook = await db.get("SELECT * FROM book WHERE id = ?", [parsedId]);
    if (!existingBook) {
      return res.status(404).json({
        message: `Book with ID ${parsedId} not found`,
      });
    }

    const validationError = validateBookBody(req.body);
    if (validationError) {
      return res.status(400).json({ message: validationError });
    }

    const { title, author, price, pages = existingBook.pages } = req.body;

    const query = "UPDATE book SET title = ?, author = ?, price = ?, pages = ? WHERE id = ?";
    await db.run(query, [title.trim(), author.trim(), price, pages, parsedId]);

    res.status(200).json({ message: "Book Updated Successfully" });
  } catch (error) {
    next(error);
  }
});

// 5. DELETE /books/:bookId/ - Delete a book
app.delete("/books/:bookId/", async (req, res, next) => {
  try {
    const { bookId } = req.params;
    const parsedId = Number(bookId);

    if (!Number.isInteger(parsedId) || parsedId <= 0) {
      return res.status(400).json({
        message: "Invalid bookId format. Must be a positive integer",
      });
    }

    // Check if record exists before deleting
    const existingBook = await db.get("SELECT * FROM book WHERE id = ?", [parsedId]);
    if (!existingBook) {
      return res.status(404).json({
        message: `Book with ID ${parsedId} not found`,
      });
    }

    const query = "DELETE FROM book WHERE id = ?";
    await db.run(query, [parsedId]);

    res.status(200).json({ message: "Book Deleted Successfully" });
  } catch (error) {
    next(error);
  }
});

// ==========================================
// DEBUGGING EXERCISE DEMONSTRATION ROUTES
// ==========================================
// Bug 3 Demo: Typo in table name ("books" instead of "book")
app.get("/broken-table/", async (req, res) => {
  try {
    const query = "SELECT * FROM books";
    const result = await db.all(query);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Bug 4 Demo: Missing await on database call
app.get("/broken-await/", async (req, res) => {
  try {
    const books = db.all("SELECT * FROM book LIMIT 5");
    console.log("Returned value without await:", books);
    res.json(books);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==========================================
// 404 UNKNOWN ROUTE HANDLER
// ==========================================
app.use((req, res) => {
  res.status(404).json({ message: "Route not found" });
});

// ==========================================
// GLOBAL ERROR HANDLER
// ==========================================
app.use((err, req, res, next) => {
  console.error("Unhandled Error:", err.stack || err.message);
  res.status(500).json({ message: "Internal server error" });
});
