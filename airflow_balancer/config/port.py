from typing import List, Optional

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from .host import Host

__all__ = ("Port",)


class Port(BaseModel):
    name: str = ""
    host: Optional[Host] = None
    host_name: str = ""
    port: int = Field(default=None, ge=1, le=65535, description="Port number")
    tags: List[str] = Field(default_factory=list)

    def __lt__(self, other):
        return (self.name or "") < (other.name or "") and self.host < other.host and self.port < other.port

    def __hash__(self):
        return hash(self.name or "") ^ hash(self.host) ^ hash(self.port)

    @property
    def pool(self):
        return f"{self.name}-{self.host.name}-port-{self.port}" if self.name else f"{self.host.name}-port-{self.port}"

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if not self.host and not self.host_name:
            raise ValueError("Either host or host_name must be provided")
        if self.host and self.host_name and self.host.name != self.host_name:
            raise ValueError("Host and host_name must match")
        return self
