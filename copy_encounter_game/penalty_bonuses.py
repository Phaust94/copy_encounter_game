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
        right_answers: typing.Set[str],
        all_answers: typing.List[str],
        levels: typing.List[int],
        penalty: str = None,
        seed: int = 41,
        shuffle_answers: bool = False,
) -> typing.Tuple[
        typing.List[Bonus],
        str
]:
    to_hash = f"{sorted(right_answers)}{all_answers}{seed}"
    new_right_ans = hashlib.md5(to_hash.encode()).hexdigest()[:10]
    wrong_ans_txt = "Неверно"
    if penalty:
        wrong_ans_txt = f"{wrong_ans_txt}. Будет начислен штраф {penalty}"
    right_ans_txt = f"Верно! Введите в поле ввода {new_right_ans!r} (без кавычек)"

    if shuffle_answers:
        random.seed(seed)
        random.shuffle(all_answers)

    all_bonuses = []
    for i, ans in enumerate(all_answers):
        b = Bonus(
            f"Штрафной бонус {i + 1}",
            answers=[ans],
            levels_available=levels,
            bonus_time=(0, 0, 1),
            hint_text=wrong_ans_txt if ans not in right_answers else right_ans_txt
        )
        all_bonuses.append(b)
    return all_bonuses, new_right_ans
