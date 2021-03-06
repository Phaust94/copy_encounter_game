"""
Game Task
"""

from __future__ import annotations

from dataclasses import dataclass

from selenium import webdriver

from copy_encounter_game.helpers import ScriptedPart, DedicatedItem, PrettyPrinter

__all__ = [
    "Task",
]


@dataclass(repr=False)
class Task(DedicatedItem, PrettyPrinter):
    html_raw: bool = False
    body: str = ""
    dedicated_to_who: int = 0

    TASK_ID_ELEMENT = "ctl02_ctl00_TasksRepeater_ctl00_lnkTaskEditor"
    TASK_ID_ADD = "ctl02_ctl00_lnkTaskAdd"

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
    ) -> Task:
        task_id_elem = driver.find_element_by_id(cls.TASK_ID_ELEMENT)
        task_script: str = task_id_elem.get_attribute("href")
        with ScriptedPart(driver, task_script):
            edit_btn = driver.find_element_by_id("lnkEdit")
            edit_btn.click()
            task_txt = driver.find_element_by_name("inputTask").text
            replace_chckbox = bool(driver.find_element_by_name("chkReplaceNlToBr").get_attribute("checked"))
            who = cls._get_for_who(driver)

            inst = cls(not replace_chckbox, task_txt, who)
        return inst

    def to_html(self, driver: webdriver.Chrome) -> None:
        # noinspection PyBroadException
        try:
            btn = driver.find_element_by_id(self.TASK_ID_ADD)
        except Exception:
            btn = driver.find_element_by_id(self.TASK_ID_ELEMENT)

        script = btn.get_attribute("href")
        with ScriptedPart(driver, script):
            # noinspection PyBroadException
            try:
                edit_btn = driver.find_element_by_id("lnkEdit")
            except Exception:
                pass
            else:
                edit_btn.click()

            task_txt = driver.find_element_by_name("inputTask")
            task_txt.clear()
            body = self.body.replace("`", "\`").replace("$", "\$")      # noqa
            driver.execute_script(f"""$('[name="inputTask"]').val(`{body}`)""")

            is_replace_checked = bool(driver.find_element_by_name("chkReplaceNlToBr").get_attribute("checked"))
            if is_replace_checked == self.html_raw:
                driver.execute_script(f"""$('input[name="chkReplaceNlToBr"]').click()""")

            self._set_for_who(driver, self.dedicated_to_who)
            # noinspection PyBroadException
            try:
                btn = driver.find_element_by_id("btnUpdate")
            except Exception:
                btn = driver.find_element_by_id("btnAdd")

            btn.click()

        return None
