from importlib import resources

from olden.unit_data.catalog import UnitCatalog, load_unit_catalog_yaml


def load_packaged_unit_catalog() -> UnitCatalog:
    catalog_file = resources.files("olden.unit_data").joinpath("units.yaml")
    return load_unit_catalog_yaml(catalog_file.read_text(encoding="utf-8"))
