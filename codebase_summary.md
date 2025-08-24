# HeliosOS Codebase Summary

This document summarizes the codebase of the HeliosOS project, a cloud-based operating system with AI integration.

## Key Files and Technologies Identified:

Based on the `requirements.txt` and `Dockerfile`, the project is a Python application primarily built with:

*   **Web Frameworks:** Flask (for the main application and API endpoints) and FastAPI (for some core services and WebRTC).
*   **Database:** SQLAlchemy with Flask-SQLAlchemy and Alembic for database management. It uses PostgreSQL (`psycopg2-binary`) but defaults to SQLite (`helios.db`).
*   **Authentication & Security:** PyJWT, bcrypt, and Werkzeug for user authentication and session management.
*   **HTTP Requests:** `requests` library.
*   **Utilities:** `python-dotenv` for environment variables, `tenacity` for retry logic.
*   **AI Integration:** Designed to integrate with HuggingFace models for AI chat and summarization. It can optionally use `openai` and `transformers`.
*   **Deployment:** Docker for containerization, Gunicorn as a WSGI HTTP server.
*   **WebRTC:** `aiortc` for WebRTC functionalities, likely for streaming desktop content.


## Code Content Analysis:

### `app/__init__.py`
This file acts as the application factory for the Flask application. It initializes and configures:
*   **Flask Extensions:** `SQLAlchemy`, `Flask-Migrate`, `Limiter` (for rate limiting), `CORS` (for cross-origin requests), and `LoginManager` (for user sessions).
*   **Configuration:** Loads environment variables for `SECRET_KEY`, `DATABASE_URL`, `HUGGINGFACE_API_KEY`, `SUMMARY_MODEL`, `CHAT_MODEL`, `JWT_SECRET_KEY`, and logging settings.
*   **Blueprints:** Registers `main_bp` (main routes) and `auth_bp` (authentication routes).
*   **Error Handlers:** Defines custom error handlers for common HTTP errors (400, 401, 403, 404, 429, 500).
*   **Database Initialization:** Creates database tables on application startup.

### `app/routes.py`
This file defines the main API endpoints for the Flask application. Key functionalities include:
*   **Health Checks:** `/health` endpoint to check database and AI service status.
*   **AI Endpoints:** `/api/ai/chat` and `/api/ai/summarize` for AI-powered chat and text summarization, requiring user login.
*   **Command Execution:** `/api/exec` allows execution of a *whitelisted* set of system commands (e.g., `ls`, `pwd`, `whoami`), with security restrictions and auditing.
*   **Audit Trails:** `/api/audit/commands` and `/api/audit/ai` to retrieve audit logs for command executions and AI interactions, with admin access for all logs and regular user access for their own.
*   **User Profile Management:** `/api/user/profile` for retrieving and updating user profiles.
*   **User Statistics:** `/api/stats` for fetching user-specific statistics on command usage and AI interactions.

### `app/models.py`
This file defines the SQLAlchemy database models:
*   **User:** Represents application users with fields like `username`, `email`, `password_hash`, `profile` (JSON), `is_active`, `is_admin`, `last_login`, `created_at`, and `updated_at`. It also defines relationships to `CommandAudit` and `UserSession`.
*   **UserSession:** Stores user session information, including `user_id`, `session_token`, `ip_address`, `user_agent`, `expires_at`, `created_at`, and `is_active`.
*   **CommandAudit:** Logs details of executed commands, including `user_id`, `username`, `command`, `return_code`, `stdout`, `stderr`, `execution_time`, `ip_address`, and `created_at`.
*   **AIInteraction:** Records AI interactions, including `user_id`, `interaction_type` (`chat` or `summarize`), `input_text`, `output_text`, `model_used`, `response_time`, `tokens_used`, `success`, `error_message`, and `created_at`.

### `app/ai_client.py`
This file provides a client for interacting with HuggingFace AI models:
*   **HuggingFaceClient:** Handles API requests to HuggingFace, including retry logic (`tenacity`) and error handling. It supports text summarization and chat response generation.
*   **Fallback Mechanisms:** Includes fallback functions (`_fallback_summary`, `_fallback_chat_response`) to provide basic responses if the AI API is unavailable or an API key is not configured.
*   **Logging:** Safely logs AI interactions to the database using the `AIInteraction` model.
*   **AIService:** A wrapper class that provides a unified interface for AI functionalities (summarize, chat) and includes a health check for the AI service.

### `app/main.py`
This file appears to be an alternative or supplementary entry point using FastAPI, possibly for core services or a different part of the application. Key aspects:
*   **FastAPI Application:** Initializes a FastAPI application with CORS middleware.
*   **Session Management:** Uses a simple in-memory session store (SESSIONS) and a basic in-memory user profile (PROFILE).
*   **Authentication:** Provides `/auth/login` and `/auth/logout` endpoints for basic authentication, setting session cookies.
*   **AI Endpoints:** `/summarize` and `/chat` endpoints, similar to the Flask app, but utilizing `AIModelManager`.
*   **Command Execution:** `/exec` endpoint for executing whitelisted commands, with similar security considerations as the Flask app.
*   **File System Operations:** Endpoints for listing (`/fs/list`), reading (`/fs/read`), writing (`/fs/write`), and deleting (`/fs/delete`) files, with path sanitization.
*   **System Information:** Provides endpoints to get system uptime, memory usage, and CPU usage.

### `app/auth.py`
This file handles authentication-related functionalities for the Flask application:
*   **Password Hashing:** `hash_password` and `verify_password` using `bcrypt`.
*   **Session Management:** `generate_session_token` and `create_user_session` for managing user sessions.
*   **JWT Tokens:** `create_jwt_token` and `decode_jwt_token` for JSON Web Token creation and validation.
*   **User Authentication:** `authenticate_user` function to verify user credentials.
*   **Decorators:** `auth_required` and `admin_required` decorators to protect routes based on user authentication and admin privileges.

### `app/os_core.py`
This file defines the core logic for the HeliosOS cloud desktop environment:
*   **Data Classes:** `UserSession` and `DesktopInstance` to represent user sessions and cloud desktop instances.
*   **HeliosOSCore:** The main class managing active user sessions and a pool of desktop instances. It includes methods for:
    *   `_initialize_desktop_pool`: Initializes a pool of ready desktop instances.
    *   `_start_monitoring` and `_update_system_stats`: Background thread for monitoring system statistics (mock data for now).
    *   `create_session`: Assigns an available desktop to a user and creates a new session.
    *   `end_session`: Cleans up resources and frees the desktop instance.
    *   `get_session` and `list_sessions`: For retrieving and listing active sessions.
    *   `get_system_stats`: Returns current system statistics.
*   **Global Instance:** `os_core` is a global instance of `HeliosOSCore`.

### `app/webrtc_service.py`
This file implements WebRTC functionalities for streaming desktop content:
*   **WebRTCService:** A class with class methods to manage WebRTC connections.
*   **Peer Connection Management:** `create_peer_connection` sets up a new WebRTC peer connection, including STUN server configuration for NAT traversal.
*   **Media Source:** Uses `aiortc` and `ffmpeg` (`x11grab`) to capture the X11 display as a video stream.
*   **SDP and ICE Handling:** `handle_offer` processes SDP offers and creates answers, `handle_ice_candidate` processes ICE candidates.
*   **Data Channel:** Sets up a data channel for potential remote command handling (e.g., keyboard/mouse control).
*   **WebSocket Signaling:** `handle_websocket` manages the WebSocket connection for WebRTC signaling, including sending client IDs and handling offer/answer/candidate exchanges.
*   **Resource Cleanup:** `close_peer_connection` closes connections and stops media streams.

## Overall Architecture:

HeliosOS appears to be a complex application with a multi-layered architecture:

1.  **Frontend (Web):** The presence of `index.html` in `web/` and `app/static/react-ui` suggests a web-based user interface, possibly built with React, that interacts with the backend APIs.
2.  **Backend (Flask & FastAPI):**
    *   **Flask Application:** Handles user authentication, AI interactions (chat, summarization), command execution, and audit logging. It uses SQLAlchemy for database persistence.
    *   **FastAPI Application:** Seems to provide core system services, including session management, file system operations, and system information retrieval. It also has AI and command execution endpoints, potentially for a different interface or internal use.
3.  **Core OS Logic (`app/os_core.py`):** Manages cloud desktop instances and user sessions, providing the underlying 


infrastructure for the cloud desktop.
4.  **WebRTC (`app/webrtc_service.py`):** Enables real-time streaming of the desktop environment to the client, likely integrating with the `os_core` to provide a visual interface.

## Potential Areas for Further Investigation:

*   **FastAPI vs. Flask:** Clarify the exact roles and interaction between the Flask and FastAPI applications. It appears there might be some overlapping functionality (e.g., AI endpoints, command execution). Understanding which part serves which purpose is crucial.
*   **Desktop Environment:** The `os_core.py` and `webrtc_service.py` suggest a virtual desktop environment. Further investigation into how the actual desktop (e.g., X11) is provisioned and managed within the Docker containers would be beneficial.
*   **AI Model Management:** While `ai_client.py` handles HuggingFace models, the `app/main.py` (FastAPI) references `AIModelManager`. Understanding the `AIModelManager`'s implementation and how it integrates with `ai_client` would be important.
*   **Security:** The `exec` endpoints in both Flask and FastAPI have whitelists for commands. A deeper dive into the security measures for command execution and file system operations is warranted, especially concerning potential vulnerabilities.
*   **Scalability and Persistence:** The in-memory session and profile management in the FastAPI app (`app/main.py`) indicate that it's not production-ready for persistence. Understanding the plans for database integration for these aspects would be important.
*   **Frontend Integration:** How the React UI (`app/static/react-ui`) interacts with both the Flask and FastAPI backends, and how the WebRTC stream is consumed and displayed on the client side.

This summary provides a high-level overview of the HeliosOS codebase. A more in-depth analysis would require running the application, debugging, and further examining specific functionalities.

