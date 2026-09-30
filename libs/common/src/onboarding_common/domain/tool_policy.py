from dataclasses import dataclass
from pathlib import Path

import yaml


class ToolNotAllowed(Exception):
    pass


@dataclass(frozen=True)
class ToolPolicy:
    agent: str
    allowed: frozenset[str]

    def check(self, tool: str) -> None:
        if tool not in self.allowed:
            raise ToolNotAllowed(f"el agente '{self.agent}' no tiene permitido usar '{tool}'")

    @classmethod
    def from_file(cls, path: str | Path, agent: str) -> "ToolPolicy":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls(agent=agent, allowed=frozenset(data["agents"].get(agent) or []))
