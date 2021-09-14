"""
Level answer
"""

from __future__ import annotations

from dataclasses import dataclass
import typing

from selenium import webdriver

from copy_encounter_game.helpers import chunks, PrettyPrinter


__all__ = [
    "Answer",
    "MAX_ANSWERS_PER_SECTOR",
    "AnswerOption",
]

MAX_ANSWERS_PER_SECTOR = 10


@dataclass(repr=False)
class AnswerOption(PrettyPrinter):
    text: str
    dedicated_to_who: int = 0


@dataclass(repr=False)
class Answer(PrettyPrinter):
    options: typing.List[AnswerOption]
    name: typing.Optional[str] = None
    order_id: int = None

    SHOW_ANSWERS_ID = "AnswersTable_ctl00_lnkShowAnswers"

    @classmethod
    def from_options(
        cls,
        options: typing.Union[
            str,
            typing.List[typing.Union[str, AnswerOption]],
        ],
        name: str = None,
    ) -> Answer:

        if isinstance(options, str):
            options = [options]

        new_opt = []
        for opt in options:
            if isinstance(opt, str):
                opt = AnswerOption(opt)
            new_opt.append(opt)
        inst = cls(new_opt, name)
        return inst

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
            url: typing.Optional[str], name: typing.Optional[str],
            domain: str, order_id: int = None,
    ) -> Answer:
        url = f"http://{domain}{url}"
        driver.get(url)
        script = """
            var ans = [];
            $('input')
              .filter(function() {
                return this.name.match(/txtAnswer_[0-9]{2,}/);
              }).each(function() {ans.push($(this).val())});
            var to_who = [];
            $('select')
              .filter(function() {
                return this.name.match(/ddlAnswerFor_[0-9]{2,}/);
              }).each(function() {
                $(this.options).each(function() {
                    if (this.selected) {
                        to_who.push(parseInt(this.value));
                    }
                })
              });
              return [ans, to_who]
            """
        res = driver.execute_script(script)
        answers_inst = [
            AnswerOption(ans, who)
            for ans, who in zip(*res)
        ]

        inst = cls(answers_inst, name, order_id)
        return inst

    def to_html(
        self,
        driver: webdriver.Chrome, has_sectors: bool = False,
        is_first_time: bool = True,
    ) -> None:
        assert len(self.options) <= MAX_ANSWERS_PER_SECTOR, "Too many answers per sector in one go"
        for i, option in enumerate(self.options):
            option_txt = option.text.replace('"', '\\\"').replace("`", "\\`")
            driver.execute_script(f"""$('input[name="txtAnswer_{i}"]').val(`{option_txt}`)""")
            driver.execute_script(f"""
            $('select[name="ddlAnswerFor_{i}"]').each(
            function() {{
                $(this.options).each(function() {{
                    if (this.value == {option.dedicated_to_who}) {{
                        this.selected = true;
                    }}
                }})
            }}
            )""")

        if self.name is not None:
            driver.execute_script(f"""$('input[name="txtSectorName"]').val("{self.name}")""")

        # noinspection PyBroadException
        opts = {
            (True, True): "btnSaveSector",
            (False, False): "AnswersTable_ctl00_NewAnswerEditor_ctl00_btnSave",
            (False, True): "AnswersTable_ctl00_NewAnswerEditor_ctl00_btnSave",
        }
        if (has_sectors, is_first_time) in opts:
            btn_name = opts[(has_sectors, is_first_time)]
            script = f"""$('input[name="{btn_name}"]').click()"""
        elif (has_sectors, is_first_time) == (True, False):
            script = f"""$('input[title="Save"]').click()"""
        else:
            raise ValueError("Impossible")
        driver.execute_script(script)

        return None

    def parts(self) -> typing.Generator[Answer, None, None]:
        for batch in chunks(self.options, MAX_ANSWERS_PER_SECTOR):
            inst_pt = Answer(batch, self.name)
            yield inst_pt
