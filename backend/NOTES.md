# ⚡ FastAPI Backend — Simple Reference

A simple cheat-sheet for developers transitioning from **Node.js** to **FastAPI**.

---

## 📂 File Roles

*   **`main.py`** ➔ App entry point (Express `server.js`).
*   **`config.py`** ➔ Reads env variables (`dotenv`).
*   **`database.py`** ➔ Database connection setup (`db.js`).
*   **`models.py`** ➔ Database tables & schemas (Mongoose schemas).
*   **`routes.py`** ➔ API endpoints & controllers (Express routers).
*   **`services/`** ➔ Helper files for ImageKit and OpenAI APIs.

---

## 🧠 Core Concepts Used

*   **Lifespan (`@asynccontextmanager`):** Runs startup actions (like creating DB tables) before the server begins accepting requests, and cleanup actions when the server stops.
*   **Pydantic (`BaseModel`):** Automatically validates incoming JSON data type structures. If the frontend sends invalid types, it auto-rejects with a `422` error.
*   **SQLModel:** An ORM that links Python classes directly to database tables. No writing raw SQL required.
*   **Dependency Injection (`Depends`):** Injecting helper functions (like database sessions) directly into API routes. FastAPI manages their lifecycle.
*   **Background Tasks (`asyncio.create_task`):** Fires a time-consuming task (like image generation) to run in the background so the API can respond instantly to the frontend.
*   **Parallel Tasks (`asyncio.gather`):** Runs multiple background tasks at the same time instead of waiting for each one to finish sequentially.
*   **Server-Sent Events (SSE):** Keeps an open HTTP stream to push updates (e.g., "Thumbnail ready") to the frontend in real-time without polling.
*   **Threading (`run_in_executor`):** Offloads synchronous actions (like ImageKit SDK uploads) to separate threads so they do not freeze the main server.

---

## 🔁 Node.js vs. FastAPI Comparison

| Action | Node.js (Express / Mongoose) | FastAPI (Python) |
| :--- | :--- | :--- |
| **Start Server** | `node server.js` | `uvicorn main:app --reload` |
| **Define Route** | `router.get("/jobs", (req, res) => {})` | `@router.get("/jobs")` |
| **API Error** | `res.status(404).json({ error: "Msg" })` | `raise HTTPException(404, "Msg")` |
| **Request Body** | Joi / Zod validation | Pydantic model (`BaseModel`) |
| **Multipart Upload** | Multer middleware | `UploadFile = File(...)` |
| **Background Task** | Run promise without `await` | `asyncio.create_task(func())` |
| **Run in Parallel** | `Promise.allSettled([...])` | `await asyncio.gather(*tasks)` |

---

## 💾 Database Cheat-Sheet (SQLModel)

| Action | Node.js (Mongoose / Prisma) | SQLModel |
| :--- | :--- | :--- |
| **Create Tables** | `prisma db push` / Schema auto-sync | `SQLModel.metadata.create_all(engine)` |
| **Find By ID** | `Model.findById(id)` | `session.get(Model, id)` |
| **Find One / Many** | `Model.find({ job_id: id })` | `session.exec(select(Model).where(...))` |
| **Save / Update** | `await doc.save()` | `session.add(doc); session.commit()` |

---

## ⚠️ 3 Quick Rules (Gotchas)

1.  **Do not hold SQLite connections open during API calls:**
    *   *Rule:* Open session ➔ Fetch data ➔ Close session ➔ `await` API call ➔ Open new session to save.
2.  **Use `run_in_executor` for synchronous libraries:**
    *   *Rule:* ImageKit SDK is synchronous. Wrap it so it doesn't freeze the backend server.
    *   *Example:* `await loop.run_in_executor(None, upload_fn, args)`
3.  **Server-Sent Events (SSE) formatting:**
    *   *Rule:* Every message yielded must end with **two newlines** (`\n\n`), or the browser will ignore it.
    *   *Example:* `yield "event: x\ndata: y\n\n"`

---

## 🏃 Commands

```bash
# 1. Activate virtual environment (Windows)
.\venv\Scripts\activate

# 2. Run the server
python -m uvicorn main:app --reload --port 8000

# 3. Test API in browser (Auto-generated Swagger UI docs)
http://localhost:8000/docs
```
