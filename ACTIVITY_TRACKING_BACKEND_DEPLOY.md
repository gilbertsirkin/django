# User Activity Tracking Backend Deployment

The backend changes add authenticated user presence and page-visit tracking.

## Files changed

- `users/models.py` adds `UserActivityEvent`.
- `users/migrations/0010_useractivityevent.py` creates the activity table and indexes.
- `api/views.py` adds `UserActivityPingView`, `AdminActivityUsersView`, and `AdminActivityUserPagesView`.
- `api/urls.py` registers the three activity routes.

## Routes

| Route | Access | Purpose |
|---|---|---|
| `POST /api/activity/ping/` | Authenticated | Records the current path, title, session, and timestamp. Query strings are stripped. Duplicate same-page heartbeats within 60 seconds are coalesced. |
| `GET /api/admin/activity/users/` | Platform admin | Returns paginated user summaries with `last_seen_at`, `current_page`, and `page_visit_count`. Supports `search`, `limit`, and `offset`. |
| `GET /api/admin/activity/users/{user_id}/pages/` | Platform admin | Returns recent page history for one user. Supports `limit` and `offset`. |

## Production rollout

Deploy the backend files, then run:

```bash
python manage.py migrate
```

Restart the Django service after migration. Confirm that the frontend origin is allowed by Django CORS settings. The existing frontend commit `13b3929` sends activity pings for authenticated users on navigation, visibility changes, and a 60-second heartbeat.

The implementation intentionally stores only the normalized page path, page title, session identifier, and timestamp. It does not store raw IP addresses, query strings, fragments, passwords, or JWT values. The endpoint is authenticated, so anonymous visitors are not included in the user activity report.

The current local environment cannot run a production database migration because the uploaded backend project does not include production database credentials. Django system checks and migration drift checks passed using an isolated temporary SQLite configuration.
