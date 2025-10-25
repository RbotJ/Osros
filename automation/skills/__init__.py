"""Skill registry for RuneLabs automation."""

from __future__ import annotations

from typing import Dict, Type

from .base import SkillTask

_SKILL_REGISTRY: Dict[str, Type[SkillTask]] = {}


def register_skill(name: str, skill_cls: Type[SkillTask]) -> None:
    """Register a new skill implementation."""

    _SKILL_REGISTRY[name] = skill_cls


def get_registered_skills() -> Dict[str, Type[SkillTask]]:
    """Return a mapping of registered skill implementations."""

    return dict(_SKILL_REGISTRY)


__all__ = ["SkillTask", "register_skill", "get_registered_skills"]
