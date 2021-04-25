"""
Game hints
"""

from __future__ import annotations

import time
from dataclasses import dataclass
import typing

from selenium import webdriver

from copy_encounter_game.helpers import ScriptedPart

__all__ = [
    "Hint",
    "PenalizedHint",
]


@dataclass
class Hint:
    hint_time: typing.Tuple[int, int, int, int] = (0, 0, 0, 0)
    hint_text: str = ""

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
            href: str,
    ) -> Hint:
        with ScriptedPart(driver, href):
            driver.find_element_by_id("lnkEdit").click()
            params = [
                "NewPromptTimeoutDays", "NewPromptTimeoutHours", "NewPromptTimeoutMinutes", "NewPromptTimeoutSeconds"
            ]
            vals = [
                int(driver.find_element_by_name(name).get_attribute("value"))
                for name in params
            ]
            txt = driver.execute_script("return $('.textarea_blank').text()")

            # noinspection PyTypeChecker
            inst = cls(tuple(vals), txt)
        return inst

    def to_html(
            self,
            driver: webdriver.Chrome, hint_url: str,
    ) -> None:
        with ScriptedPart(driver, hint_url):
            # noinspection PyBroadException
            try:
                driver.find_element_by_id("lnkEdit").click()
            except Exception:
                pass
            time.sleep(0.7)
            params = [
                "NewPromptTimeoutDays", "NewPromptTimeoutHours", "NewPromptTimeoutMinutes", "NewPromptTimeoutSeconds"
            ]
            for name, value in zip(params, self.hint_time):
                driver.execute_script(f"""$('[name="{name}"]').attr("value", "{value}")""")

            txt = self.hint_text.replace("\"", "\\\"").replace("`", "\\`")
            driver.execute_script(f"""$('textarea[name="NewPrompt"]').text(`{txt}`)""")
            # noinspection PyBroadException
            try:
                driver.find_element_by_id('btnUpdate').click()
            except Exception:
                driver.find_element_by_id('btnAdd').click()

        return None


@dataclass
class PenalizedHint(Hint):
    hint_description: str = ""
    additional_confirmation_on: bool = True
    penalty_time: typing.Tuple[int, int, int] = (0, 0, 0)

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
            href: str,
    ) -> PenalizedHint:
        with ScriptedPart(driver, href):
            driver.find_element_by_id("lnkEdit").click()
            params = [
                "NewPromptTimeoutDays", "NewPromptTimeoutHours", "NewPromptTimeoutMinutes", "NewPromptTimeoutSeconds",
                "PenaltyPromptHours", "PenaltyPromptMinutes", "PenaltyPromptSeconds",
            ]
            vals = [
                int(driver.find_element_by_name(name).get_attribute("value"))
                for name in params
            ]
            txt = driver.execute_script("""return $('.textarea_blank[name="NewPrompt"]').text()""")

            confirmation_on = bool(driver.find_element_by_id("chkRequestPenaltyConfirm").get_attribute("checked"))
            header = driver.execute_script("""return $('.textarea_blank[name="txtPenaltyComment"]').text()""")

            # noinspection PyTypeChecker
            inst = cls(tuple(vals[:4]), txt, header, confirmation_on, tuple(vals[4:]))
        return inst

    def to_html(
            self,
            driver: webdriver.Chrome, hint_url: str,
    ) -> None:
        with ScriptedPart(driver, hint_url):
            # noinspection PyBroadException
            try:
                driver.find_element_by_id("lnkEdit").click()
            except Exception:
                pass
            time.sleep(0.7)
            params = [
                "NewPromptTimeoutDays", "NewPromptTimeoutHours", "NewPromptTimeoutMinutes", "NewPromptTimeoutSeconds",
                "PenaltyPromptHours", "PenaltyPromptMinutes", "PenaltyPromptSeconds",
            ]
            for name, value in zip(params, self.hint_time):
                driver.execute_script(f"""$('[name="{name}"]').attr("value", "{value}")""")

            txt = self.hint_text.replace("\"", "\\\"").replace("`", "\\`")
            driver.execute_script(f"""$('textarea[name="NewPrompt"]').text(`{txt}`)""")

            desc = self.hint_description.replace("\"", "\\\"").replace("`", "\\`")
            driver.execute_script(f"""$('textarea[name="txtPenaltyComment"]').text(`{desc}`)""")

            is_checked = bool(driver.find_element_by_id("chkRequestPenaltyConfirm").get_attribute("checked"))
            if self.additional_confirmation_on ^ is_checked:
                driver.execute_script("""$('#chkRequestPenaltyConfirm').click()""")
                driver.execute_script("""$('#chkRequestPenaltyConfirm').trigger('onclick')""")

            # noinspection PyBroadException
            try:
                driver.find_element_by_id('btnUpdate').click()
            except Exception:
                driver.find_element_by_id('btnAdd').click()

        return None
