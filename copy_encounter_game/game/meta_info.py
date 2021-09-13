"""
Game meta info
"""

from __future__ import annotations

from dataclasses import dataclass
import typing
import re

from selenium import webdriver

from copy_encounter_game.helpers import ScriptedPart, wait, PrettyPrinter

__all__ = [
    "LevelName",
    "Autopass",
    "AnswerBlock",
    "SectorsToCover",
]


@dataclass(repr=False)
class LevelName(PrettyPrinter):
    name: str = ""

    SCRIPT_SECTION = "GameEditor('./NameCommentEdit.aspx?gid={game_id}&level={level_id}', '');"

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
            game_id: int,
            level_id: int,
    ) -> LevelName:
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


@dataclass(repr=False)
class Autopass(PrettyPrinter):
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
        wait(driver, "chkTimeoutPenalty")
        autopass_form = driver.find_element_by_id(cls.SETTINGS_ID)
        params = [
            "txtApHours", "txtApMinutes", "txtApSeconds",
            "txtApPenaltyHours", "txtApPenaltyMinutes", "txtApPenaltySeconds",
        ]
        vals = [
            int(autopass_form.find_element_by_name(name).get_attribute("value"))
            for name in params
        ]
        # noinspection PyTypeChecker
        return cls(enabled, tuple(vals[:3]), tuple(vals[3:]))

    @classmethod
    def from_past_html(
        cls,
        driver: webdriver.Chrome,
    ) -> Autopass:

        elem = driver.find_element_by_id("lnkAdjustAutopass").text
        pts = elem.split(",")
        ap = []
        for pt in pts:
            t = []
            for unit in ("hours", "minutes", "seconds"):
                un_val = re.findall(
                    fr"([0-9]+) {unit}", pt
                )
                un_val = int(un_val[0]) if un_val else 0
                t.append(un_val)
            days = re.findall(fr"([0-9]+) days", pt)
            if days:
                t[0] += int(days[0]) * 24

            ap.append(tuple(t))

        inst = cls(bool(sum(ap[0])), *ap)
        return inst

    def to_html(self, driver: webdriver.Chrome) -> None:
        elem = driver.find_element_by_id(self.STATUS_ID)
        elem.click()
        wait(driver, "chkTimeoutPenalty")

        is_checked = bool(driver.find_element_by_id("chkTimeoutPenalty").get_attribute("checked"))
        if self.penalty ^ is_checked:
            driver.execute_script("""$('#chkTimeoutPenalty').click()""")
            driver.execute_script("""$('#chkTimeoutPenalty').trigger('onclick')""")

        params = [
            "txtApHours", "txtApMinutes", "txtApSeconds",
            "txtApPenaltyHours", "txtApPenaltyMinutes", "txtApPenaltySeconds",
        ]

        for name, value in zip(params, self.autopass_time + self.penalty_time):
            driver.execute_script(f"""$('[name="{name}"]').attr("value", "{value}")""")

        driver.execute_script(f"""$('#AutoPassSettingsHolder').find('input[title="Save"]').click()""")
        return None


@dataclass(repr=False)
class AnswerBlock(PrettyPrinter):
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


@dataclass(repr=False)
class SectorsToCover(PrettyPrinter):
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


# Exists here for backwards compatibility
GameName = LevelName
