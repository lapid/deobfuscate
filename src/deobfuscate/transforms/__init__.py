"""The transforms the engine runs, in no particular order."""

from deobfuscate.transforms.base import Candidate, Transform
from deobfuscate.transforms.base64 import Base64
from deobfuscate.transforms.rot13 import Rot13

ALL: tuple[Transform, ...] = (Base64(), Rot13())

__all__ = ["ALL", "Candidate", "Transform"]
