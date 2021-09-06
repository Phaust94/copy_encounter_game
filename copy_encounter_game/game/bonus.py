"""
Game hints
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
import typing

from selenium import webdriver

from copy_encounter_game.helpers import ScriptedPart, DedicatedItem

__all__ = [
    "Bonus",
]


@dataclass
class Bonus(DedicatedItem):
    name: str
    bonus_task: str = ""
    answers: typing.List[str] = field(default_factory=list)
    levels_available: typing.List[int] = None
    available_time: typing.Optional[typing.Tuple[str, str]] = None
    appearence_delay: typing.Optional[typing.Tuple[int, int, int]] = None
    availability_window: typing.Optional[typing.Tuple[int, int, int]] = None
    bonus_time: typing.Tuple[int, int, int] = (0, 0, 0)
    hint_text: str = ""
    dedicated_to_who: int = 0

    @staticmethod
    def get_levels(
            driver: webdriver.Chrome
    ) -> typing.List[int, str, typing.Optional[str]]:
        levels = driver.execute_script("""
                        var levels = [];
                        $('.enCheckBox[name^="level"]').each(
                            function(i, e){
                                levels.push(
                                    [
                                        i + 1,
                                        $(e).attr('name'),
                                        $(e).attr('checked')
                                    ]
                                )
                            }
                        );
                        return levels
                        """)
        return levels

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
            href: str,
    ) -> Bonus:
        with ScriptedPart(driver, href):
            driver.find_element_by_css_selector('a[title="Edit"]').click()
            str_params = [
                "txtBonusName", "txtTask",
                "txtValidFrom", "txtValidTo",
                "txtHelp",
            ]
            str_vals = [
                driver.find_element_by_name(name).get_attribute("value")
                for name in str_params
            ]

            int_params = [
                "txtDelayHours", "txtDelayMinutes", "txtDelaySeconds",
                "txtValidHours", "txtValidMinutes", "txtValidSeconds",
                "txtHours", "txtMinutes", "txtSeconds",
            ]
            int_vals = [
                int(driver.find_element_by_name(name).get_attribute("value"))
                for name in int_params
            ]

            levels = cls.get_levels(driver)
            levels_available = [
                level_id
                for level_id, _, res in levels
                if res
            ]

            checkboxes = [
                "rbAllLevels",
                "chkAbsoluteLimit", "chkDelay", "chkRelativeLimit",
            ]

            checkboxes_results = []
            for chb in checkboxes:
                checked_element = driver.find_element_by_id(chb)
                checked = bool(checked_element.get_attribute("checked"))
                checkboxes_results.append(checked)

            levels_available = levels_available if not checkboxes_results[0] else None
            available_time = tuple(str_vals[2:4]) if checkboxes_results[1] else None
            appearance_delay = tuple(int_vals[:3]) if checkboxes_results[2] else None
            availability_window = tuple(int_vals[3:6]) if checkboxes_results[3] else None
            bonus_time = tuple(int_vals[6:9])

            hint_answers = driver.execute_script("""
                var ans = [];
                $('input[name^="answer_"]').each(
                    function(i, e){
                        var val_ = $(e).attr('value');
                        if (val_) {
                            ans.push(val_);
                        }
                    }
                );
                return ans
            """)

            who = cls._get_for_who(driver)

            # noinspection PyTypeChecker
            inst = cls(
                str_vals[0], str_vals[1],
                hint_answers,
                levels_available,
                available_time,
                appearance_delay,
                availability_window,
                bonus_time,
                str_vals[-1],
                who,
            )
        return inst

    def to_html(
            self,
            driver: webdriver.Chrome, hint_url: str,
    ) -> None:
        with ScriptedPart(driver, hint_url):
            # noinspection PyBroadException
            try:
                driver.find_element_by_css_selector('a[title="Edit"]').click()
            except Exception:
                pass
            time.sleep(0.7)

            if self.levels_available:
                driver.execute_script("""$('#rbCustomLevels').click()""")
            else:
                driver.execute_script("""$('#rbAllLevels').click()""")

            checkboxes = [
                "chkAbsoluteLimit", "chkDelay", "chkRelativeLimit",
            ]
            expecteds = [
                self.available_time, self.appearence_delay, self.availability_window,
            ]

            for chb_name, chb_value in zip(checkboxes, expecteds):
                checked_element = driver.find_element_by_id(chb_name)
                checked = bool(checked_element.get_attribute("checked"))
                if checked != bool(chb_value):
                    driver.execute_script(f"""$('#{chb_name}').click()""")
                    driver.execute_script(f"""$('#{chb_name}').trigger('onclick')""")

            driver.execute_script(f"""$('[name="txtBonusName"]').attr("value", "{self.name}")""")

            params = [
                ("txtValidFrom", "txtValidTo"),
                ("txtDelayHours", "txtDelayMinutes", "txtDelaySeconds"),
                ("txtValidHours", "txtValidMinutes", "txtValidSeconds"),
                ("txtHours", "txtMinutes", "txtSeconds"),
            ]
            params_values = [
                self.available_time,
                self.appearence_delay,
                self.availability_window,
                self.bonus_time,
            ]
            for name_g, value_g in zip(params, params_values):
                if value_g:
                    for name, value in zip(name_g, value_g):
                        driver.execute_script(f"""$('[name="{name}"]').attr("value", "{value}")""")

            txt = self.bonus_task.replace("\"", "\\\"").replace("`", "\\`")
            driver.execute_script(f"""$('textarea[name="txtTask"]').text(`{txt}`)""")
            txt = self.hint_text.replace("\"", "\\\"").replace("`", "\\`")
            driver.execute_script(f"""$('textarea[name="txtHelp"]').text(`{txt}`)""")

            levels_available = self.levels_available or []
            levels_in_en = self.get_levels(driver)
            for lvl_id, lvl_name, is_checked in levels_in_en:
                if bool(is_checked) ^ (lvl_id in levels_available):
                    driver.execute_script(f"""$('.enCheckBox[name="{lvl_name}"]').click()""")
                    driver.execute_script(f"""$('.enCheckBox[name="{lvl_name}"]').trigger('onclick')""")

            n_times_to_click = math.ceil((len(self.answers) - 10) / 30)
            for _ in range(n_times_to_click):
                driver.execute_script("$('a.Text4')[2].click()")

            answer_names = driver.execute_script("""
                var levels = [];
                $('input[name^="answer_"]').each(function(i, e){levels.push($(e).attr('name'))});
                return levels
            """)
            for ans, ans_name in zip(self.answers, answer_names):
                driver.execute_script(f"""$('input[name="{ans_name}"]').val(`{ans}`)""")

            self._set_for_who(driver, self.dedicated_to_who)

            # noinspection PyBroadException
            try:
                driver.find_element_by_name('btnUpdate').click()
            except Exception:
                driver.find_element_by_name('btnAdd').click()

        return None
