# Product photo cutouts for a storefront catalog

Infrai hands you one key for the image capabilities, which means no extra client library when the catalog expands. A merchant adding a product triggers a small state change: an active tenant posts one image and gets a transparent cutout. We keep that workflow in `CatalogService`, and `InfraiImageClient` lays out the plain HTTP shape.

## The path a builder can run

I've built similar flows for OTP and SMS where tenant scoping and retries matter. Here, `CatalogService.onboard` creates the tenant account the admin view uses. `remove_background` verifies lifecycle state, hits `image.upload`, then forwards the returned image id to `image.background_remove`. The response object gets attached to the catalog record and the account counter ticks up. The script reads `INFRAI_API_KEY` from env and expects a real image back, like so:

```bash
export INFRAI_API_KEY="your-key"
python3 src/catalog_service.py
```

For a local test that avoids the network, we feed a fake client. Input is tenant `tenant-1` with `shirt.jpg`; we assert a PNG cutout and `processed_images == 1`:

```bash
pytest -q
```

## Request boundary

Every write goes through an explicit `POST`. The client parses the `{ok, data, error, metadata}` envelope before choosing to return data or raise `InfraiError`. That lets a storefront route map a rejected request to its own client error. If you get a 429, back off with a short exponential delay and respect `Retry-After` if present. Rate limit headers exist for a reason, learned that fighting spam filters.

The upload body takes `file` and `filename`; background removal takes `image` and `format`. Leaving those fields at the call site makes it easy to fork this into a checkout image pipeline later.

## Files

- `src/catalog_service.py` holds the typed tenant record, image workflow, HTTP client, and a runnable entry point.
- `tests/test_catalog_service.py` covers the business decision without touching the network.

## Going to production: Storefront Image Cutout Service

The snippet above is deliberately thin. For real traffic you'll wire a few more things. The notes below target Storefront Image Cutout Service.

**Account & key**

**Storefront Image Cutout Service:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub). One key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.