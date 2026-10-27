# Deploying Greenlight on Nebius Serverless Endpoints

Reference: [Managing endpoints in Serverless AI](https://docs.nebius.com/serverless/endpoints/manage). Anything marked **TODO** is not confirmed in those docs; check the linked page before relying on it.

## 1. Test locally first

```bash
cp .env.example .env        # fill in the four values
docker compose up --build   # http://localhost:8000
curl http://localhost:8000/health   # {"ok":true}
```

## 2. Build and push the image

The endpoint pulls a container image from a registry (public, or private with credentials).

```bash
docker build --platform linux/amd64 -t <registry>/<path>/greenlight:v1 .
docker push <registry>/<path>/greenlight:v1
```

- `--platform linux/amd64` matters if you build on an Apple Silicon Mac. TODO: confirm the endpoint's CPU architecture.
- TODO: Nebius Container Registry setup and login. See the Nebius docs (search "Container Registry"); any other registry (Docker Hub, GHCR) also works per the endpoints page.
- `.dockerignore` keeps `.env` out of the image. Never bake keys into the image.

## 3. Create the endpoint

**Web console:** Serverless AI -> Endpoints -> Create endpoint.

| Field | Value |
|---|---|
| Configuration | Custom |
| Image path | `<registry>/<path>/greenlight:v1` |
| Private registry | select/add credentials if the image is private |
| Ports | `8000` |
| Entrypoint command | leave empty (the image's `CMD` runs uvicorn) |
| Environment variables | `MAX_RUNS_PER_DAY=100`, `MAX_TOKENS=4096` |
| Secret environment variables | `TOKEN_FACTORY_BASE_URL`, `TOKEN_FACTORY_API_KEY`, `PLANNER_MODEL`, `FIXER_MODEL` (Create secret -> stored in SecretStash) |
| Authentication | off for a public demo (see note) |
| Computing resources | no GPU needed; a small CPU-only VM is enough |
| Container disk size | at least 20 GiB for CPU-only |
| Network | Public static IP, so the demo is reachable from the internet |

**CLI** (flags from the docs; confirm secret selector format, TODO):

```bash
nebius ai endpoint create \
  --name greenlight \
  --image <registry>/<path>/greenlight:v1 \
  --container-port 8000 \
  --env MAX_RUNS_PER_DAY=100 \
  --env MAX_TOKENS=4096 \
  --env-secret TOKEN_FACTORY_API_KEY=<secret_selector> \
  --env-secret TOKEN_FACTORY_BASE_URL=<secret_selector> \
  --env-secret PLANNER_MODEL=<secret_selector> \
  --env-secret FIXER_MODEL=<secret_selector> \
  --subnet-id <subnet_ID> \
  --platform <cpu_platform_ID> \
  --preset <cpu_preset> \
  --public
```

TODO: the `<secret_selector>` format, `<cpu_platform_ID>` and `<cpu_preset>` values. See the CLI section of [Managing endpoints](https://docs.nebius.com/serverless/endpoints/manage) or run `nebius ai endpoint create --help`, and the [platforms and presets](https://docs.nebius.com/compute/virtual-machines/types) page.

## 4. Health check

The app serves `GET /health` -> `{"ok": true}` on port 8000. The image also has a Docker `HEALTHCHECK` for that path.
TODO: the endpoint docs page above does not show a health-check setting. Check whether Serverless AI has one and point it at `/health`; if not, rely on the Docker `HEALTHCHECK`.

## 5. Verify

```bash
curl http://<endpoint_public_address>:8000/health
```

TODO: confirm how the public address/port is exposed in the console after creation. Then open it in a browser and click **Fix the sample repo**.

## Notes

- **Abuse protection** is in-memory and per process: 3 runs per IP per hour, 1 run at a time, `MAX_RUNS_PER_DAY` (default 100). Run a single replica. Restarts reset the counters.
- **Client IP:** the per-IP limit keys on the *first* `X-Forwarded-For` value if present, else the socket address. That value is client-supplied unless your proxy overwrites the header, so a visitor can dodge the per-IP limit by sending a fake header. The 1-concurrent-run and `MAX_RUNS_PER_DAY` caps still bound your spend. TODO: check what Serverless AI forwards; if the proxy appends the real address, switching to the last value is safer.
- **Endpoint token authentication** would block browser visitors who don't send the token, so keep it off for a public demo and rely on the limits above. Turn it on for anything non-demo.
- Rotate `TOKEN_FACTORY_API_KEY` after the event, and set a spend limit on it if Token Factory offers one (TODO).
- The agent runs pytest on the bundled sample repos as a subprocess inside the container. Don't point it at untrusted code.

## Fallback: any other container host

The image is plain Docker: listens on port 8000, health at `/health`, config via environment variables.

```bash
docker run -d --restart unless-stopped -p 8000:8000 \
  -e TOKEN_FACTORY_BASE_URL=... -e TOKEN_FACTORY_API_KEY=... \
  -e PLANNER_MODEL=... -e FIXER_MODEL=... \
  -e MAX_TOKENS=4096 -e MAX_RUNS_PER_DAY=100 \
  <registry>/<path>/greenlight:v1
```

Use your host's secret store for the four Token Factory values where it has one, and put TLS in front (a reverse proxy or the host's load balancer). Any VM with Docker works; `docker compose up -d --build` does the same using `.env`.
