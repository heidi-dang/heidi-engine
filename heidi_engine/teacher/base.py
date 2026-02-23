from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Protocol


class TeacherBackend(Protocol):
    name: str

    def run(
        self,
        *,
        repo_dir: str,
        prompt: str,
        model_id: str,
        agent: str,
        attach_url: Optional[str] = None,
    ) -> str:
        """Run the teacher and return final assistant text."""


@dataclass(frozen=True)
class TeacherRegistry:
    backends: Dict[str, TeacherBackend]

    @classmethod
    def from_env(cls) -> "TeacherRegistry":
        # Lazy-import to avoid any optional deps at import time.
        from .openhei_teacher import OpenHeiTeacher

        openhei = OpenHeiTeacher()
        return cls(backends={openhei.name: openhei})

    def get(self, name: str) -> TeacherBackend:
        if name not in self.backends:
            raise KeyError(f"Unknown teacher backend: {name}")
        return self.backends[name]
