"""CLI entry-point for running the agility automation skill."""

from __future__ import annotations

import time

import cv2

from automation.skills.agility import AgilitySkill


def main() -> None:
    skill = AgilitySkill()
    skill.start()
    try:
        while True:
            skill.update()
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        skill.stop()
        time.sleep(0.1)


if __name__ == "__main__":
    main()
