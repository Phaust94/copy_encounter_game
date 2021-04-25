"""
Level answer
"""

from __future__ import annotations

from dataclasses import dataclass
import typing

from selenium import webdriver


__all__ = [
    "Answer",
]


@dataclass
class Answer:
    options: typing.List[str]
    name: str = None

    SHOW_ANSWERS_ID = "AnswersTable_ctl00_lnkShowAnswers"

    @classmethod
    def from_html(cls, driver: webdriver.Chrome, url: str, name: str, domain: str) -> Answer:
        url = f"http://{domain}{url}"
        driver.get(url)
        script = """
            var res = [];
            $('input')
              .filter(function() {
                return this.name.match(/txtAnswer_[0-9]{2,}/);
              }).each(function() {res.push($(this).val())});
              return res
            """
        answers = driver.execute_script(script)

        inst = cls(answers, name)
        return inst

    def to_html(self, driver: webdriver.Chrome, has_sectors: bool = False) -> None:
        for i, option in enumerate(self.options):
            option = option.replace('"', '\\\"').replace("`", "\\`")
            driver.execute_script(f"""$('input[name="txtAnswer_{i}"]').val(`{option}`)""")

        if self.name is not None:
            driver.execute_script(f"""$('input[name="txtSectorName"]').val("{self.name}")""")

        # noinspection PyBroadException
        if has_sectors:
            driver.execute_script("""$('input[name="btnSaveSector"]').click()""")
        else:
            driver.execute_script("""$('input[name="AnswersTable_ctl00_NewAnswerEditor_ctl00_btnSave"]').click()""")

        return None
