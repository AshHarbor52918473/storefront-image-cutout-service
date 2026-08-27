from catalog_service import CatalogService


class FakeClient:
    def upload(self, image_bytes, filename):
        assert filename == "shirt.jpg"
        return {"id": "img_123"}

    def background_remove(self, image, format="png"):
        assert image == "img_123"
        return {"url": "https://cdn.example/cutout.png", "format": format}


def test_active_tenant_gets_a_cutout_and_counter_moves():
    service = CatalogService(FakeClient())
    service.onboard("tenant-1", "buyer@example.com")
    result = service.remove_background("tenant-1", "shirt.jpg", b"pixels")
    assert result.cutout["format"] == "png"
    assert service.accounts["tenant-1"].processed_images == 1
