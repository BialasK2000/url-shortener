# URL shortener

A very simple URL shortener API, something like TinyURL but without the UI. Written in Django REST
Framework. Plain and simple, enjoy :)

## Running locally

You will need Python 3.12 or newer. `requirements.txt` has everything needed to run the app,
`requirements-dev.txt` adds the tools for tests and linting.

```bash
git clone https://github.com/BialasK2000/url-shortener.git
cd url-shortener
python -m venv .venv
source .venv/bin/activate    # on Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

If you need to, you can set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=1` and `DJANGO_ALLOWED_HOSTS` as
environment variables.

## Usage

The API takes and returns JSON, so any HTTP client will do (Postman, curl, HTTPie...). With the
server running, the base URL is `http://127.0.0.1:8000`.

1. Shorten a URL:

   ```http
   POST /shrt/
   Content-Type: application/json

   {"url": "https://en.wikipedia.org/wiki/Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch"}
   ```

   Response contains the short URL (the code at the end is random, so yours will be different...):

   ```json
   {"url": "https://en.wikipedia.org/wiki/Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch", "short_url": "http://127.0.0.1:8000/shrt/Xk3p9Qa"}
   ```

   New link comes back with `201`. Shortening the same URL twice gives you the same short URL
   with `200`.

2. Open the `short_url` from that response in your browser. It redirects (`302`) to the original
   page.

3. To get the original URL back, send your `short_url` to `/expand/`:

   ```http
   POST /expand/
   Content-Type: application/json

   {"short_url": "http://127.0.0.1:8000/shrt/<code>"}
   ```

   The response looks the same as in step 1, with `200`.

Invalid input gets a `400` with a short explanation, for example
`{"url": ["Only http and https URLs are allowed."]}`, and a short URL that doesn't exist gets a
`404`. Don't forget the trailing slash in `/shrt/` and `/expand/`.

## Tests

```bash
pytest                 # everything
pytest -m "not e2e"    # without the e2e
mypy
ruff check .
```

e2e tests start a server with pytest-django's `live_server` and send requests to it with
httpx.

## Notes

A few things weren't clear , so here's what I decided:

- The example short URL doesn't say much about the code format so I went with 7 random letters and digits from `secrets`.
  A collision between them is very unlikely, but if it happens, a new code is generated.
- I used English in the entire project because I decided this is a standard,
  although the task itself was written in Polish.
- Only http and https links are accepted. Short links were I assumed to use for a web pages only so there's
  no reason to allow ftp:// (which Django's URL validator would accepts by default, so I accept only http and https).
- The same URL always gets the same short link. URLs are compared exactly as they come in, so
  `http://example.com` and `http://example.com/` are treated as two different URLs. 
  I didn't want to save unnecessary short urls pointing to the same normal url in the database, so I chose this approach.
- I don't check whether the page behind a URL actually exists. It would slow shortening down, fail
  for sites that block bots and open to SSRF attack. 
- `/expand/` takes the whole short URL, since it's the reverse of shortening. Only the
  `/shrt/<code>` part is checked, not the host, because the app can be reached under different
  hostnames.
- A redirect wasn't required, but a short link that doesn't lead anywhere seemed pointless. It's a
  302, so browser don't cache it like 301.
- I chose to use SQLite, because the task was aiming for simplicity and it also needs no setup. 
  Moving to Postgres if we wanted to will be needed to run a Postgres server and updating `DATABASES`.
