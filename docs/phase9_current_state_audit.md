# Phase 9: Current State Audit (Android API Integration)

## API Assessment
The Python FastAPI backend (at `src/evoforge/api/server.py`) provides a robust, typed REST interface that is highly suitable for consumption by an Android application.

### Existing Endpoints for Mobile
- **Runtime & Status:** `/api/status`, `/api/runtime/status`, `/api/scheduler/status` (Provides overall health and compute mode)
- **Workers:** `/api/workers`, `/api/workers/{id}/drain` (Provides worker lists and safe operational controls)
- **Portfolio & Projects:** `/api/projects`, `/api/projects/{id}/health`, `/api/projects/{id}/tasks` (Provides project hierarchies and priorities)
- **Tasks & Workflows:** Handled via project task endpoints and runtime routing events.
- **Agents:** `/api/agents` (Provides capabilities, current task bindings, and skill confidence)
- **Routing:** `/api/routing/recent` (Provides AI routing explanations)
- **Learning & Evolution:** `/api/learning/research`, `/api/learning/gaps`, `/api/evolution/proposals`, `/api/evolution/proposals/{id}/approve`
- **Settings:** `/api/settings/compute` (Allows changing compute mode dynamically)

### Authentication
- Worker and restricted runtime operations require `Authorization: Bearer <token>`.
- The Android app will need a settings screen to input the API Base URL and an optional Bearer Token to access administrative endpoints safely.

### Mobile-Specific Security Requirements
- Tokens must not be hardcoded or logged. They should be stored using Android's `EncryptedSharedPreferences` or DataStore.
- The UI should degrade gracefully if unauthorized, displaying "UNAUTHORIZED" rather than crashing or showing empty generic errors.

### Missing Mobile APIs
- There is no native Push Notification or WebSocket endpoint natively exposed for live streaming without SSE. The Android app will rely on optimized coroutine polling (e.g., every 5-10s while foregrounded) mimicking the Phase 8 web app.
- No dedicated "Task Details" endpoint exists outside of pulling it from the portfolio tasks list. The mobile app will need to locate the task from the cached portfolio response.
