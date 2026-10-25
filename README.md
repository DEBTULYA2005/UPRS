# Universal Recommendation System - Backend

Django REST Framework + PostgreSQL backend that serves recommendations to
multiple independent client apps (an e-commerce site, a reels platform, ...).
Your **Lesson 6 algorithm is preserved** (see [Algorithm](#your-lesson-6-algorithm)).

## What has and has not been verified

| Verified in the build environment | NOT verified |
|---|---|
| 45 automated tests pass on SQLite **and** on a real local PostgreSQL 16 | Connecting to a real Supabase or Render database |
| Migrations apply on PostgreSQL 16 | Deploying to Render (the config follows Render's docs but was not run) |
| Real Gunicorn run with `DEBUG=False`, `collectstatic`, health/auth/CORS/docs checked with curl | React frontend integration |
| Python 3.13.13, exact versions in `requirements.txt` | |

---

## 1. Run locally

Requires **Python 3.13** and a PostgreSQL database (local, Supabase, or Render).

```bash
cd Universal-Recommendation-System-Backend
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # Windows: copy .env.example .env
# edit .env: set SECRET_KEY and DATABASE_URL (section 2)

python manage.py migrate
python manage.py create_client "My E-commerce Shop"     # prints the API key ONCE - save it
python manage.py createsuperuser                        # optional, for /admin/
python manage.py runserver
```

* API docs (Swagger UI): http://127.0.0.1:8000/api/docs/ - click **Authorize** and paste your key.
* ReDoc: `/api/redoc/` - OpenAPI schema: `/api/schema/` - Admin: `/admin/`

Run the tests (they never touch your hosted database):

```bash
python manage.py test tests                       # in-memory SQLite, fastest
TEST_DATABASE_URL=postgresql://user:pw@localhost:5432/anydb python manage.py test tests   # local PostgreSQL
```
(The test DB user needs the `CREATEDB` permission. Do not point this at a hosted database.)

## 2. PostgreSQL configuration (`DATABASE_URL`)

Everything comes from the `DATABASE_URL` environment variable. SSL is turned on
automatically for any non-local host.

**Supabase**
1. Create a project, then click **Connect** in the dashboard and copy the PostgreSQL URI.
2. Replace `[YOUR-PASSWORD]` with your database password (URL-encode special characters, e.g. `@` -> `%40`).
3. If your backend runs on Render (IPv4), use the **Session pooler** string (port 5432, host `...pooler.supabase.com`); Supabase's direct connection is IPv6-oriented. Check Supabase's current docs, this can change.
4. If you choose the **Transaction pooler** (port 6543) also set `DATABASE_USING_TRANSACTION_POOLER=true`.

**Render PostgreSQL**
1. Render dashboard -> **New -> PostgreSQL**.
2. Running locally: use the **External Database URL**. Running on Render in the same region: use the **Internal Database URL**.

Put the value in `.env` locally, or in the Render dashboard's *Environment* tab when deployed. Never commit it.

### Environment variables

| Variable | Required | Meaning |
|---|---|---|
| `SECRET_KEY` | yes (prod) | Django secret. Render generates one via `render.yaml`. |
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `DEBUG` | no (default `False`) | `True` only locally |
| `ALLOWED_HOSTS` | no | Comma-separated hosts. `RENDER_EXTERNAL_HOSTNAME` is added automatically on Render |
| `CORS_ALLOWED_ORIGINS` | no | Comma-separated frontend origins, e.g. `https://shop.example.com` |
| `CSRF_TRUSTED_ORIGINS` | no | Only for `/admin/` on a custom domain |
| `DATABASE_SSL_REQUIRE` | no | `true`/`false`; defaults to `true` for non-local hosts |
| `DATABASE_USING_TRANSACTION_POOLER` | no | `true` for Supabase port-6543 pooler |

## 3. Deploy to Render

1. Push this folder to a GitHub repo (`.env` is git-ignored).
2. Render -> **New -> Blueprint** (uses `render.yaml`), or **New -> Web Service** with:
   * **Build command:** `./build.sh`  (installs deps, `collectstatic`, **runs migrations**)
   * **Start command:** `gunicorn config.wsgi:application --workers 2 --timeout 60`
   * **Health check path:** `/api/health/`
3. Set environment variables: `DATABASE_URL`, `CORS_ALLOWED_ORIGINS` (and `SECRET_KEY` if not using the blueprint), `DEBUG=False`.
4. After the first deploy, open the Render **Shell** and run `python manage.py create_client "My Shop"` to get the API key (or create clients in `/admin/` after `createsuperuser`).

Verify `PYTHON_VERSION` in `render.yaml` against versions Render currently supports.

## 4. API reference

All endpoints except health need the header **`X-API-Key: <your key>`**. Errors use standard
HTTP codes with JSON bodies (`{"detail": "..."}` or `{"field": ["message"]}`).

| Method & path | Purpose |
|---|---|
| `GET /api/health/` | Public. `200 {"status":"ok","database":"ok"}` or `503` if the DB is unreachable |
| `GET /api/content/` | List your content (paginated). Filters: `category`, `q`, `include_inactive` |
| `POST /api/content/` | Create content |
| `GET /api/content/<content_id>/` | Retrieve one item (404 if it isn't yours) |
| `POST /api/events/` | Record `view` / `search` / `like` / `save` |
| `GET /api/recommendations/?user_id=101&top_k=8` | Personalized recommendations (`top_k` 1-50, default 8) |
| `GET /api/recommendations/similar/?content_id=12&top_k=6` | Items similar to one item (`top_k` 1-50, default 6) |

`content_id` allows letters, digits and `_ . : -`. `user_id` allows letters, digits and `_ . : @ -`.

### Examples (real output from a local run)

```bash
curl -X POST http://127.0.0.1:8000/api/content/ \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"content_id":"1","title":"Python Programming","category":"Programming",
       "description":"Learn Python programming and coding","image_url":"https://example.com/p.jpg"}'
```
```json
{"content_id":"1","title":"Python Programming","category":"Programming","description":"Learn Python programming and coding","image_url":"https://example.com/p.jpg","is_active":true,"created_at":"2026-10-25T06:38:11.753740Z"}
```

```bash
curl -X POST http://127.0.0.1:8000/api/events/ -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"user_id":"101","content_id":"1","event_type":"like","weight":99}'
```
```json
{"id":1,"user_id":"101","content_id":"1","event_type":"like","weight":3,"timestamp":"2026-10-25T06:38:26.007691Z"}
```
The `weight` you send is ignored; the server derives it from `event_type`. Unknown or other-client content gives `400 {"content_id": ["No active content with this content_id exists for your account."]}`.

```bash
curl "http://127.0.0.1:8000/api/recommendations/?user_id=101&top_k=3" -H "X-API-Key: $KEY"
```
```json
{"user_id":"101","strategy":"personalized","count":2,"results":[
  {"content_id":"3","title":"Java Programming","category":"Programming","image_url":"","score":0.455942},
  {"content_id":"5","title":"Football Highlights","category":"Sports","image_url":"","score":0.019139}]}
```

`strategy` tells you how the list was made:

* `personalized` - your Lesson 6 algorithm (user has interaction history).
* `popular_fallback` - **not** Lesson 6. A separate rule for users with no history: most-interacted-with content first (`score` = count / max count; `0.0` if nothing has any interactions yet).
* `empty` - the client has no active content; `results` is `[]`.

If a personalized user has already interacted with everything, you get `personalized` with `results: []`.

Similar content (`strategy: "content_similarity"`, `score` = cosine similarity):
```json
{"content_id":"1","strategy":"content_similarity","count":2,"results":[
  {"content_id":"3","title":"Java Programming","category":"Programming","image_url":"","score":0.556634},
  {"content_id":"2","title":"Django Web Development","category":"Programming","image_url":"","score":0.264623}]}
```

## 5. Security model

* Each client has its own key. Only a SHA-256 hash and a short non-secret prefix are stored; the raw key is shown once (command line or admin) and can be rotated (`python manage.py rotate_client_key <id>`, or the admin action).
* The client is **always** derived from the key. A `client` field in a request body is ignored.
* Every query is filtered by the authenticated client; content/users/interactions of other clients return 404/400 as if they did not exist. `user_id` and `content_id` namespaces are per client.
* Keys are never returned in responses and request headers/bodies are not logged.

### Connecting your React/Vite shop safely

**Never** put the key in `VITE_*` variables or any browser code: everything in your bundle is public.
Keep the key on a server you control and let the browser call *that*:

```
Browser (React)  ->  your own server / serverless function (holds API_KEY)  ->  this backend
```

*Development* (`vite.config.js`; `RECS_API_KEY` has no `VITE_` prefix so it is never sent to the browser):
```js
import { defineConfig, loadEnv } from 'vite'
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')          // reads .env.local; '' = all vars
  return { server: { proxy: { '/recs-api': {
    target: 'http://127.0.0.1:8000', changeOrigin: true,
    rewrite: p => p.replace(/^\/recs-api/, '/api'),
    headers: { 'X-API-Key': env.RECS_API_KEY },
  } } } }
})
```
React then calls `fetch('/recs-api/recommendations/?user_id=101')` with no key.

*Production:* use the same idea in a small Express/Node server, or a Netlify/Vercel function, that adds the `X-API-Key` header from a server-side environment variable. Let that server decide the `user_id` from its own login session instead of trusting one sent by the browser.

## 6. Your Lesson 6 algorithm

`recommendation_engine/engine.py` is built from your uploaded `recommendation_engine.py`.

* **Unchanged:** popularity = count / max count; TF-IDF on `title + category + description`; cosine similarity; weighted sum of similarity rows; division by total weight; `0.8 * personalization + 0.2 * popularity`; seen content set to `-1`; descending sort; top-N. Weights `view=1, search=2, like=3, save=4` (`recommendation_engine/weights.py`).
* **Changed only for integration:** your file built DataFrames from hard-coded demo data and used module globals. The same two DataFrames (same columns) are now passed in from PostgreSQL by `data_loader.py`; steps 3-9 became `build_model()`; steps 10-17 are `recomender(user_id, top_n=5, *, content_df, interaction_df)`; `print()` calls and the demo call were removed.
* **Your untouched file** is at `recommendation_engine/reference/lesson6_original.py`. Two tests run it side by side with the integrated engine (demo data, and demo data round-tripped through PostgreSQL) and assert identical ids and scores.
* **Added around it, not inside it:** the `popular_fallback` rule (`recommendations/fallback.py`), the `similar_content()` function for `/similar/`, and filtering of `-1` sentinel rows in the API layer. In your original, asking for more results than there are unseen items returns the seen ones with score `-1`; the API drops those.

## 7. Known limitations

* The TF-IDF/similarity model is rebuilt on every recommendation request (as it is built once at import in your original). Fine for hundreds to low thousands of items per client; cache per client if your catalogue grows large.
* Only active content is considered; deactivating content removes it and its interactions from scoring.
* Content is created one item per request (no bulk import endpoint). No rate limiting. API docs pages are public (they contain no secrets).
* `Interaction.save()` enforces client consistency; raw `bulk_create` would bypass it.

## Project layout

```
config/                 settings, urls, wsgi
clients/                Client model, API-key auth, permissions, create/rotate commands
content/                Content model + endpoints
interactions/           UserProfile + Interaction models, POST /api/events/
recommendations/        endpoints, services, popular-content fallback
recommendation_engine/  your Lesson 6 algorithm, data loader, weights, original reference
tests/                  45 automated tests
```
