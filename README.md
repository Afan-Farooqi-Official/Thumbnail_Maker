# 🎨 AI-Powered YouTube Thumbnail Generator

A full-stack application designed to generate professional, click-worthy YouTube thumbnails. The application uses AI to generate custom thumbnail scenes (matching the video topic) that feature the likeness of the user based on an uploaded headshot.

---

## ⚙️ Architecture & Features

### Backend (Python & FastAPI)
*   **AI-Powered Image Generation:** Integrates with the **OpenAI Responses API** using the `gpt-4o` model and the built-in `gpt-image-2` tool to generate custom thumbnails that preserve the user's likeness from an input headshot image.
*   **CDN Hosting & Transformations:** Uploads the generated thumbnails to the **ImageKit** CDN. It leverages ImageKit transforms to generate multiple aspect ratios on-the-fly:
    *   📺 **YouTube Thumbnail:** 16:9 (`1280x720`)
    *   📱 **YouTube Shorts / TikTok:** 9:16 (`1080x1920`)
    *   📸 **Instagram / Square:** 1:1 (`1080x1080`)
*   **SSE Job Progress Streaming:** Streams job updates (`generating`, `ready`, or `failed`) in real-time to clients using Server-Sent Events (SSE) via FastAPI's `StreamingResponse`.
*   **SQLite Database Storage:** Uses **SQLModel** (SQLAlchemy + Pydantic) to store user prompts, uploaded headshot URLs, and the status of generated thumbnail records.

### Frontend (React & Vite)
*   **React & Vite Scaffolding:** Initialized with a high-performance build system ready for fast UI feedback (Hot Module Replacement).
*   **Interactive Generation Wizard:** A multi-step form to input video descriptions, upload headshots, select thumbnail styles, and track job statuses.
*   **Real-time Event Observers:** SSE stream listeners to update thumbnail previews on-the-fly as they finish generating in the backend.
*   **Responsive Previews & Downloads:** Card interfaces displaying different dimension crops (16:9, 9:16, 1:1) with cross-origin download handlers for local saving.

---

## 📂 File Architecture Map

```text
ThumbnailMaker/
├── backend/                  # FastAPI & SQLModel backend server
│   ├── main.py               # Server entry point & CORS configuration
│   ├── database.py           # DB connection engine & SQLite session generators
│   ├── models.py             # DB Schemas (Jobs and Thumbnails)
│   ├── routes.py             # API endpoints (upload, streaming SSE, status queries)
│   ├── config.py             # Environment configuration manager
│   ├── NOTES.md              # Detailed concept cheat-sheet (FastAPI vs. Node.js)
│   └── services/
│       ├── openai_service.py # Core generation code (OpenAI Responses API call)
│       ├── imagekit_service.py # ImageKit CDN upload & transform variants
│       └── generator_services.py # Orchestrates background processes (DB saves & API calls)
│
└── frontend/                 # React & Vite frontend
    ├── src/
    │   ├── App.jsx           # UI Entrypoint
    │   ├── App.css           # Styling assets
    │   ├── api.js            # API utility calls
    │   └── main.jsx          # Render script
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
*   [Python 3.10+](https://www.python.org/downloads/)
*   [Node.js (v18+)](https://nodejs.org/)

---

### 2. Backend Setup
1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    *   **Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   **Mac/Linux:**
        ```bash
        python -m venv venv
        source venv/bin/activate
        ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure environment keys in a `.env` file:
    ```env
    OPENAI_API_KEY=your_openai_api_key
    IMAGEKIT_PRIVATE_KEY=your_imagekit_private_key
    IMAGEKIT_PUBLIC_KEY=your_imagekit_public_key
    IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_endpoint_id/
    ```
5.  Start the FastAPI server:
    ```bash
    python -m uvicorn main:app --reload --port 8000
    ```
    *   **Swagger API Docs:** Accessible at [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 3. Frontend Setup
1.  Navigate to the `frontend` directory:
    ```bash
    cd ../frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
    *   **Dev URL:** [http://localhost:5173/](http://localhost:5173/)
