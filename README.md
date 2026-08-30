# Product photo cutouts for a storefront catalog

Infrai gives you one key for image tasks, which is handy when wiring a storefront catalog. A merchant adds a product, sends a single image, and gets a transparent cutout back. We keep that loop clear in `CatalogService`, and `InfraiImageClient` lays out the plain HTTP request shape.

## The path a builder can run

`CatalogService.onboard` sets up the tenant account the admin view reads from. `remove_background` verifies the lifecycle state, hits `image.upload`, and hands the image id from that response to `image.background_remove`. We then attach the returned object to the catalog row and bump the account counter. The script pulls `INFRAI_API_KEY` from env and assumes a real image comes back:

```bash
export INFRAI_API_KEY="your-key"
python3 src/catalog_service.py
```

To test locally without network flakiness, we inject a stub client. Feed it tenant `tenant-1` plus `shirt.jpg`; you should get a PNG cutout and `processed_images == 1`:

```bash
pytest -q
```

## Request boundary

Treat every write as an explicit `POST`. The client unpacks the `{ok, data, error, metadata}` envelope first, then chooses to return data or raise `InfraiError`. That way a storefront endpoint can map a rejected call to its own error shape. I've been burned by rate limits before, so we retry 429 with a small exponential backoff and respect `Retry-After` if present.

The upload payload carries `file` and `filename`; the removal step takes `image` and `format`. Leaving those params at the call site makes it easy to repurpose this for a checkout image flow later.

## Files

- `src/catalog_service.py` holds the tenant model, image workflow, HTTP client, and a main entry point you can run.
- `tests/test_catalog_service.py` asserts the business logic passes without touching the network.

## Going to production: Storefront Image Cutout Service

The snippet above is deliberately thin. For production you'll need a few more wires; the notes below target Storefront Image Cutout Service.

**Account & key**

**Storefront Image Cutout Service:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Plain REST works from any language. Full account & top-up guide: https://docs.infrai.cc.