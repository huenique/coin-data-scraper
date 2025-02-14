import dataclasses
from dataclasses import MISSING, dataclass
from typing import Any


@dataclass
class DefaultMixin:

    @classmethod
    def default(cls):
        fields: dict[str, Any] = {
            f.name: (f.default if f.default != MISSING else None)
            for f in dataclasses.fields(cls)
        }

        return cls(**fields)
