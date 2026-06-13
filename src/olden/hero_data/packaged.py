from importlib import resources

from olden.hero_data.catalog import HeroCatalog, load_hero_catalog_yaml


def load_packaged_hero_catalog() -> HeroCatalog:
    catalog_file = resources.files("olden.hero_data").joinpath("heroes.yaml")
    return load_hero_catalog_yaml(catalog_file.read_text(encoding="utf-8"))
