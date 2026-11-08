# Lab 3: Debugging Exercise & Troubleshooting Guide

**Student Name:** S. Dinesh Kumar  
**Registration Number:** 252U1R1227  
**Section:** CSE-2E 211  
**Subject:** Backend Development Fundamentals  
**College:** Aurora Deemed-to-be University  

---

## Overview

This document analyzes the four deliberate bugs created in `debug-exercise/server-broken.js`. For every bug, the exact error message observed in the terminal, the discovery method, the root cause, and the step-by-step fix are documented.

---

## Bug 1: Port Conflict (`EADDRINUSE`)

### 1. Exact Error Message Observed
```text
node:events:497
      throw er; // Unhandled 'error' event
      ^

Error: listen EADDRINUSE: address already in use :::3000
    at Server.setupListenHandle [as _listen2] (node:net:1940:16)
    at listenInCluster (node:net:1997:12)
    at Server.listen (node:net:2102:7)
    at Function.listen (C:\Users\Dinesh\S-Dinesh-Kumar-Lab-03\node_modules\express\lib\application.js:605:24)
    at Server.<anonymous> ([eval]:1:104)
    at Server.f (C:\Users\Dinesh\S-Dinesh-Kumar-Lab-03\node_modules\once\once.js:25:25)
    at Object.onceWrapper (node:events:633:28)
    at Server.emit (node:events:531:35)
    at emitListeningNT (node:net:1983:10)
    at process.processTicksAndRejections (node:internal/process/task_queues:88:21)
Emitted 'error' event on Server instance at:
    at emitErrorNT (node:net:1976:8)
    at process.processTicksAndRejections (node:internal/process/task_queues:89:21) {
  code: 'EADDRINUSE',
  errno: -4091,
  syscall: 'listen',
  address: '::',
  port: 3000
}
```

### 2. How Found
- Attempted to start an Express server on port 3000 while another instance or another `app.listen()` call was already bound to port 3000.
- Command executed:
  ```bash
  npm start
  ```
- The terminal immediately aborted execution with exit code 1.

### 3. Root Cause
Operating systems permit only one process or socket to bind to a specific TCP port (here 3000) on an IP interface at any given time. When `app.listen(3000)` was called a second time or while an existing background Node process was active, the operating system kernel rejected the bind request with `EADDRINUSE` ("Error: Address Already In Use").

### 4. The Fix
1. **Find and terminate the process occupying the port:**
   ```powershell
   # On Windows PowerShell:
   Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
   ```
2. **Make the port configurable via environment variables in `server.js`:**
   ```javascript
   const PORT = process.env.PORT || 3000;
   ```
3. **Add a friendly error handler on the HTTP server object:**
   ```javascript
   const server = app.listen(PORT, () => {
     console.log(`Server is running at http://localhost:${PORT}`);
   });

   server.on("error", (error) => {
     if (error.code === "EADDRINUSE") {
       console.error(`[Port Conflict] Port ${PORT} is already in use. Please terminate the process or set PORT=<other_port>.`);
     } else {
       console.error(`[Server Error] ${error.message}`);
     }
   });
   ```

---

## Bug 2: Wrong Import / Require Path (`MODULE_NOT_FOUND`)

### 1. Exact Error Message Observed
```text
node:internal/modules/cjs/loader:1386
  throw err;
  ^

Error: Cannot find module './wrong-sqlite-path'
Require stack:
- C:\Users\Dinesh\S-Dinesh-Kumar-Lab-03\debug-exercise\server-broken.js
    at Function._resolveFilename (node:internal/modules/cjs/loader:1383:15)
    at defaultResolveImpl (node:internal/modules/cjs/loader:1025:19)
    at resolveForCJSWithHooks (node:internal/modules/cjs/loader:1030:22)
    at Function._load (node:internal/modules/cjs/loader:1192:37)
    at TracingChannel.traceSync (node:diagnostics_channel:328:14)
    at wrapModuleLoad (node:internal/modules/cjs/loader:237:24)
    at Module.require (node:internal/modules/cjs/loader:1463:12)
    at require (node:internal/modules/helpers:147:16)
    at [eval]:1:17
    at runScriptInThisContext (node:internal/vm:209:10) {
  code: 'MODULE_NOT_FOUND',
  requireStack: [
    'C:\\Users\\Dinesh\\S-Dinesh-Kumar-Lab-03\\debug-exercise\\server-broken.js'
  ]
}
```

### 2. How Found
- Ran `node server.js` immediately after introducing a typo or invalid relative file path in a `require(...)` call.
- The Node.js CommonJS module loader halted the program before any server initialization occurred.

### 3. Root Cause
Node.js resolves module specifiers by looking into `node_modules` for bare package names (e.g. `"sqlite3"`) and inspecting the local file system for relative paths beginning with `./` or `../`. When `./wrong-sqlite-path` was passed, Node tried to locate a local file named `wrong-sqlite-path.js` or `wrong-sqlite-path/index.js`, which does not exist, triggering `MODULE_NOT_FOUND`.

### 4. The Fix
- Replace the invalid local path with the installed package name:
  ```javascript
  // BEFORE (Broken):
  const sqlite3 = require("./wrong-sqlite-path");

  // AFTER (Fixed):
  const sqlite3 = require("sqlite3");
  ```
- Verify that `sqlite3` is present in `package.json` under `dependencies` and run `npm install`.

---

## Bug 3: Table-Name Typo (`SQLITE_ERROR: no such table`)

### 1. Exact Error Message Observed
```text
SQLITE ERROR CAUGHT: SQLITE_ERROR: no such table: books
Error: SQLITE_ERROR: no such table: books
    at Statement.all (C:\Users\Dinesh\S-Dinesh-Kumar-Lab-03\node_modules\sqlite3\lib\sqlite3.js:15:21)
    ...
```

### 2. How Found
- Sent a GET request to the `/broken-table/` route:
  ```bash
  curl http://localhost:3000/broken-table/
  ```
- The API responded with HTTP 500:
  ```json
  {
    "error": "SQLITE_ERROR: no such table: books"
  }
  ```

### 3. Root Cause
In SQLite DDL, the table was created using the singular noun `book`:
```sql
CREATE TABLE IF NOT EXISTS book ( ... );
```
However, the SQL query in the route referenced the plural form `books`:
```sql
SELECT * FROM books;
```
SQLite checked its sqlite_schema table, could not find any entity named `books`, and rejected the query with `SQLITE_ERROR: no such table: books`.

### 4. The Fix
- Match the SQL query table name exactly to the schema definition:
  ```javascript
  // BEFORE (Broken):
  const query = "SELECT * FROM books";

  // AFTER (Fixed):
  const query = "SELECT * FROM book";
  ```

---

## Bug 4: Missing `await` on Database Call (Unresolved Promise)

### 1. Exact Error Message / Behavior Observed
- Value logged to server console:
  ```text
  Returned value without await: Promise { <pending> }
  JSON serialized: {}
  ```
- Client received:
  ```json
  {}
  ```
  Instead of an array of book objects like:
  ```json
  [
    {
      "id": 1,
      "title": "The Pragmatic Programmer",
      "author": "David Thomas, Andrew Hunt",
      "price": 750,
      "pages": 352
    }
  ]
  ```

### 2. How Found
- Sent a GET request to the endpoint:
  ```bash
  curl http://localhost:3000/broken-await/
  ```
- The response status code was 200 OK, but the response body was completely empty `{}`.
- Inspecting the console showed that `db.all(...)` had returned `Promise { <pending> }`.

### 3. Root Cause
Methods on the `sqlite` driver (`db.all`, `db.get`, `db.run`, `db.exec`) are asynchronous and return a JavaScript `Promise`. If `await` is omitted, the variable receives the unresolved `Promise` object rather than the resolved data array. When Express calls `res.json(books)`, `JSON.stringify(promise)` is executed. Since `Promise` instances have no enumerable properties, `JSON.stringify` produces `{}` without throwing an error, leading to a silent bug.

### 4. The Fix
- Add the `await` keyword before calling asynchronous database functions:
  ```javascript
  // BEFORE (Broken):
  const books = db.all("SELECT * FROM book LIMIT 5");
  res.json(books);

  // AFTER (Fixed):
  const books = await db.all("SELECT * FROM book LIMIT 5");
  res.json(books);
  ```

---

## Summary of Debugging Best Practices

| Issue | Detection Technique | Primary Fix |
|---|---|---|
| **Port Conflict (EADDRINUSE)** | Terminal error during startup (`app.listen`) | Kill blocking process or use `process.env.PORT` |
| **Wrong Module Path** | Node module resolution error at startup | Check `package.json` and correct path / name |
| **No Such Table** | HTTP 500 error & SQLite logs | Inspect SQLite schema using `.schema` CLI command |
| **Missing `await`** | Empty JSON `{}` response payload | Always `await` asynchronous database queries inside `async` route handlers |
