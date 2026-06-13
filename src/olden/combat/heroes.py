from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class HeroStats:
    attack: int = 0
    defense: int = 0
    spell_power: int = 0
    knowledge: int = 0

    def __post_init__(self) -> None:
        _require_non_negative(self.attack, "Hero attack")
        _require_non_negative(self.defense, "Hero defense")
        _require_non_negative(self.spell_power, "Hero spell power")
        _require_non_negative(self.knowledge, "Hero knowledge")


@dataclass(frozen=True, slots=True)
class Hero:
    id: str
    name: str
    level: int = 1
    experience: int = 0
    stats: HeroStats = field(default_factory=HeroStats)

    def __post_init__(self) -> None:
        if not self.id:
            msg = "Hero ID must be non-empty"
            raise ValueError(msg)
        if not self.name:
            msg = "Hero name must be non-empty"
            raise ValueError(msg)
        if self.level < 1:
            msg = "Hero level must be at least 1"
            raise ValueError(msg)
        _require_non_negative(self.experience, "Hero experience")


def _require_non_negative(value: int, name: str) -> None:
    if value < 0:
        msg = f"{name} must be non-negative"
        raise ValueError(msg)
