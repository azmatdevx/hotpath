# Locust: correlation syntax

Extract in Python from the response and use the value in later requests. Each simulated user has its own `self.client` session, which keeps cookies per user.

```python
import re
from locust import HttpUser, task, between

class WebUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def flow(self):
        # JSON body
        with self.client.post("/api/login", json={"user": "u", "pass": "p"},
                              catch_response=True) as r:
            token = r.json().get("data", {}).get("token")
            if not token:
                r.failure("token not extracted")
                return

        # HTML hidden field (BeautifulSoup) or regex
        page = self.client.get("/form")
        m = re.search(r'name="csrf" value="([^"]+)"', page.text)
        if not m:
            return
        csrf = m.group(1)

        self.client.post("/submit", data={"csrf": csrf},
                         headers={"Authorization": f"Bearer {token}"})
```

## Tips
- Use `catch_response=True` so a missing value or wrong content is recorded as a failure, not a success.
- Prefer `r.json()` or a real HTML parser over regex when possible.
- Store per-user values on `self` (for example `self.token` set in `on_start`) when they live for the whole session.
- Do not use module-level variables for per-user tokens, since users share module state.
- Keep credentials and tokens out of source; read them from environment variables or a data file.
