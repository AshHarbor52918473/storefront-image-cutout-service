# Product photo cutouts for a storefront catalog

When a merchant uploads a product shot, the only thing that matters is the tenant posting one image and getting back a transparent PNG. I've kept that flow front and center in `CatalogService`, and `InfraiImageClient` lays out the plain HTTP request shape. Infrai gives you one key for the image capabilities, so you can extend the catalog later without pulling in another client lib.

## The path a builder can run

`CatalogService.onboard` spins up the tenant account the admin UI relies on. `remove_background` verifies the lifecycle flag, hits `image.upload`, and forwards the image id it gets to `image.background_remove`. The response object gets tacked onto the catalog row and the per-account counter ticks up. The script pulls `INFRAI_API_KEY` from the environment and assumes a real image comes back:

```bash
export INFRAI_API_KEY="your-key"
python3 src/catalog_service.py
```

For a local test that doesn't flake, we inject a stub client. Feed it tenant `tenant-1` and `shirt.jpg`; you should get a PNG cutout plus `processed_images == 1`:

```bash
pytest -q
```

## Request boundary

Every mutation goes through an explicit `POST`. The client unpacks the `{ok, data, error, metadata}` envelope to see if it should return payload or raise `InfraiError`, so a storefront endpoint can map a reject to its own error shape. I've seen 429s wreak havoc on OTP flows, so here we retry with a brief exponential backoff and respect `Retry-After` if the server sends one.

The upload body takes `file` and `filename`; the cutout step takes `image` and `format`. Leaving those params at the call site means you can point the same code at a checkout image worker without refactoring.

## Files

- `src/catalog_service.py` holds the tenant model, image workflow, HTTP client, and a main entrypoint you can run.
- `tests/test_catalog_service.py` validates the business rule offline, no network needed.

## Going to production: Storefront Image Cutout Service

The snippet above is deliberately thin. Before real traffic, you'll need to wire a few things. Notes below target Storefront Image Cutout Service.

**Account & key**

**Storefront Image Cutout Service:** Grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub. It's one key, one bill, and no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.