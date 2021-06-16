"""
Generates penalty bonuses from a list of answers
"""

import typing
import random
import hashlib

from copy_encounter_game.game.bonus import Bonus

__all__ = [
    "penalty_bonuses",
]


def penalty_bonuses(
        right_answer: str, wrong_answers: typing.List[str],
        levels: typing.List[int],
        seed: int = None
) -> typing.Tuple[
        typing.List[Bonus],
        str
]:
    all_answers = [right_answer, *wrong_answers]
    seed = seed or 41
    random.seed(seed)
    random.shuffle(all_answers)
    all_bonuses = []
    to_hash = f"{right_answer}{seed}"
    new_right_ans = hashlib.md5(to_hash.encode()).hexdigest()[:6]
    for ans in all_answers:
        b = Bonus(
            f"Штрафной бонус",
            answers=[ans],
            levels_available=levels,
            bonus_time=(0, 0, 1),
            hint_text="Неверно" if ans != right_answer else f"Верно! Введите в ответ {new_right_ans}"
        )
        all_bonuses.append(b)
    return all_bonuses, new_right_ans
