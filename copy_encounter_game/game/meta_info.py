"""
Game meta info
"""

from __future__ import annotations

import time
from dataclasses import dataclass
import typing

from selenium import webdriver

from copy_encounter_game.helpers import ScriptedPart

__all__ = [
    "GameName",
    "Autopass",
    "AnswerBlock",
    "SectorsToCover",
]


@dataclass
class GameName:
    name: str = ""

    SCRIPT_SECTION = "GameEditor('./NameCommentEdit.aspx?gid={game_id}&level={level_id}', '');"

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
            game_id: int,
            level_id: int,
    ) -> GameName:
        script = cls.SCRIPT_SECTION.format(
            game_id=game_id,
            level_id=level_id,
        )
        with ScriptedPart(driver, script):
            lvl_name = driver.find_element_by_name("txtLevelName")
            val = lvl_name.get_attribute('value')
            inst = cls(val)
        return inst

    def to_html(
            self,
            driver: webdriver.Chrome,
            game_id: int,
            level_id: int,
    ) -> None:
        script = self.SCRIPT_SECTION.format(
            game_id=game_id,
            level_id=level_id,
        )
        with ScriptedPart(driver, script):
            driver.execute_script(f"""$('[name="txtLevelName"]').attr("value", "{self.name}")""")
            btn = driver.find_element_by_xpath('//input[@title="Update"]')
            btn.click()

        return None


@dataclass
class Autopass:
    enabled: bool = False
    autopass_time: typing.Tuple[int, int, int] = (0, 0, 0)
    penalty_time: typing.Tuple[int, int, int] = (0, 0, 0)

    STATUS_ID = "lnkAdjustAutopass"
    SETTINGS_ID = "AutoPassSettingsHolder"

    @property
    def penalty(self) -> bool:
        return any(self.penalty_time)

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
    ) -> Autopass:
        elem = driver.find_element_by_id(cls.STATUS_ID)
        enabled = elem.text not in ("нет", "no")
        if not enabled:
            return cls(enabled)

        elem.click()
        time.sleep(0.7)
        autopass_form = driver.find_element_by_id(cls.SETTINGS_ID)
        params = [
            "txtApHours", "txtApMinutes", "txtApSeconds",
            # "chkTimeoutPenalty",
            "txtApPenaltyHours", "txtApPenaltyMinutes", "txtApPenaltySeconds",
        ]
        vals = [
            int(autopass_form.find_element_by_name(name).get_attribute("value"))
            for name in params
        ]
        # noinspection PyTypeChecker
        return cls(enabled, tuple(vals[:3]), tuple(vals[3:]))

    def to_html(self, driver: webdriver.Chrome) -> None:
        elem = driver.find_element_by_id(self.STATUS_ID)
        elem.click()
        time.sleep(0.3)

        is_checked = bool(driver.find_element_by_id("chkTimeoutPenalty").get_attribute("checked"))
        if self.penalty ^ is_checked:
            driver.execute_script("""$('#chkTimeoutPenalty').click()""")
            driver.execute_script("""$('#chkTimeoutPenalty').trigger('onclick')""")

        params = [
            "txtApHours", "txtApMinutes", "txtApSeconds",
            # "chkTimeoutPenalty",
            "txtApPenaltyHours", "txtApPenaltyMinutes", "txtApPenaltySeconds",
        ]

        for name, value in zip(params, self.autopass_time + self.penalty_time):
            driver.execute_script(f"""$('[name="{name}"]').attr("value", "{value}")""")

        driver.execute_script(f"""$('#AutoPassSettingsHolder').find('input[title="Save"]').click()""")
        return None


@dataclass
class AnswerBlock:
    enabled: bool = False
    individual: bool = False
    n_tries: int = 0
    block_time: typing.Tuple[int, int, int] = (0, 0, 0)

    STATUS_ID = "lnkAnswerBlockingStatus"
    SETTINGS_ID = "divAnswerBlockingSettings"

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
    ) -> AnswerBlock:

        elem = driver.find_element_by_id(cls.STATUS_ID)
        enabled = elem.text not in ("отключена", "disabled")
        if not enabled:
            return cls(enabled)

        elem.click()
        form = driver.find_element_by_id(cls.SETTINGS_ID)
        params = [
            "txtAttemptsNumber",
            "txtAttemptsPeriodHours", "txtAttemptsPeriodMinutes", "txtAttemptsPeriodSeconds"
        ]
        vals = [
            int(form.find_element_by_name(name).get_attribute("value"))
            for name in params
        ]
        for_user_elem = form.find_element_by_id("rbApplyForUser")
        for_user = bool(for_user_elem.get_attribute("checked"))
        # noinspection PyTypeChecker
        inst = cls(enabled, for_user, vals[0], tuple(vals[1:]))

        return inst

    def to_html(self, driver: webdriver.Chrome) -> None:
        elem = driver.find_element_by_id(self.STATUS_ID)
        elem.click()
        params = [
            "txtAttemptsNumber",
            "txtAttemptsPeriodHours", "txtAttemptsPeriodMinutes", "txtAttemptsPeriodSeconds"
        ]
        for name, value in zip(params, [self.n_tries, *self.block_time]):
            driver.execute_script(f"""$('[name="{name}"]').attr("value", "{value}")""")

        if self.individual:
            driver.execute_script("""$('#rbApplyForUser').click()""")
        else:
            driver.execute_script("""$('#rbApplyForTeam').click()""")

        driver.execute_script(f"""$('#divAnswerBlockingSettings').find('input[title="Save"]').click()""")
        return None


@dataclass
class SectorsToCover:
    n_sectors: typing.Optional[int] = None

    STATUS_ID = "lnkSectorsSettings"
    COMPLETE_CUSTOM_ID = "rbCompleteCustom"
    N_COMPLETE_ID = "txtRequiredSectorsCount"

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
    ) -> SectorsToCover:
        # noinspection PyBroadException
        try:
            elem = driver.find_element_by_id(cls.STATUS_ID)
        except Exception:
            inst = cls()
            return inst

        elem.click()
        is_custom_btn = driver.find_element_by_id(cls.COMPLETE_CUSTOM_ID)
        is_custom = bool(is_custom_btn.get_attribute("checked"))
        if not is_custom:
            n = None
        else:
            n = int(driver.find_element_by_id(cls.N_COMPLETE_ID).get_attribute("value"))
        inst = cls(n)
        return inst

    def to_html(self, driver: webdriver.Chrome) -> None:
        elem = driver.find_element_by_id(self.STATUS_ID)
        elem.click()
        if self.n_sectors is not None:
            driver.execute_script(f"""$('#{self.COMPLETE_CUSTOM_ID}').click()""")
            driver.execute_script(f"""$('#{self.N_COMPLETE_ID}').attr("value", "{self.n_sectors}")""")

        driver.execute_script(f"""$('#divSectorsSettins').find('input[title="Save"]').click()""")
        return None
