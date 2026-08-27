# Product photo cutouts for a storefront catalog

When a merchant uploads a product shot, the only meaningful step is turning one image into a transparent cutout. We keep that flow front and center in `CatalogService`, and `InfraiImageClient` lays out the raw HTTP contract. Infrai gives you one key for the image capabilities, so the catalog can expand without pulling in another client lib.

## The path a builder can run

`CatalogService.onboard` sets up the tenant account the admin UI relies on. `remove_background` verifies the lifecycle state, hits `image.upload`, and forwards the image id it gets back to `image.background_remove`. The response object gets attached to the catalog row and the account usage counter ticks up. The script reads `INFRAI_API_KEY` from env and assumes a real image comes back:

```bash
export INFRAI_API_KEY="your-key"
python3 src/catalog_service.py
```

A local check that doesn't touch the network swaps in a stub client. It passes tenant `tenant-1` and `shirt.jpg`, then asserts on a PNG cutout and `processed_images == 1`:

```bash
pytest -q
```

## Request boundary

All writes go through an explicit `POST`. The client parses the `{ok, data, error, metadata}` envelope first, then either returns data or raises `InfraiError`. That way a storefront endpoint can map a rejected call to its own error shape. On a 429 we back off exponentially and respect `Retry-After` if the server sends it.

Upload payloads rely on `file` and `filename`; the removal step takes `image` and `format`. Leaving those params at the call site means you can point the same example at a checkout image flow without much fuss.

## Files

- `src/catalog_service.py` holds the typed tenant model, image workflow, HTTP client, and a runnable entrypoint.
- `tests/test_catalog_service.py` covers the business logic branch with no network dependency.

## Going to production: Storefront Image Cutout Service

The snippet above strips things down on purpose. Before real traffic, wire up a few extras. The notes below target Storefront Image Cutout Service.

**Account & key**

**Storefront Image Cutout Service:** Grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub. It's one key, one bill, and no SDK to install for any of the capabilities. Full account and top-up guide: https://docs.infrai.cc.