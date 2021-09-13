"""
Game meta info
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
import typing
import itertools
import pickle

from selenium import webdriver
import selenium.common.exceptions

from copy_encounter_game.game.meta_info import LevelName, Autopass, AnswerBlock, SectorsToCover
from copy_encounter_game.game.task import Task
from copy_encounter_game.game.hint import Hint, PenalizedHint
from copy_encounter_game.game.answer import Answer
from copy_encounter_game.game.bonus import Bonus
from copy_encounter_game.helpers import wait, PrettyPrinter, wait_url_contains
from copy_encounter_game.game.game_custom_info import GameCustomInfo

__all__ = [
    "Level",
]


@dataclass(repr=False)
class Level(PrettyPrinter):
    domain: str
    game_id: int
    level_id: int
    name: LevelName = LevelName()
    autopass: Autopass = Autopass()
    answer_block: AnswerBlock = AnswerBlock()
    sectors_to_cover: SectorsToCover = SectorsToCover()
    tasks: typing.List[Task] = field(default_factory=list)
    hints: typing.List[Hint] = field(default_factory=list)
    penalized_hints: typing.List[PenalizedHint] = field(default_factory=list)
    bonuses: typing.List[Bonus] = field(default_factory=list)
    answers: typing.List[Answer] = field(default_factory=list)

    LEVEL_URL = "http://{domain}/Administration/Games/LevelEditor.aspx?gid={gid}&level={lid}"

    @classmethod
    def current_level_url(cls, domain: str, game_id: int, level_id: int) -> str:
        return cls.LEVEL_URL.format(domain=domain, gid=game_id, lid=level_id)

    @classmethod
    def find_hint_urls(cls, driver: webdriver.Chrome, type_: int = 0) -> typing.List[str]:
        time.sleep(0.3)
        num = 2 + type_
        hint_hrefs = driver.execute_script(f"""
                        var tbl = $('table.bg_dark')[{num}];
                        var hints = $(tbl).find('table').find('tr');
                        var urls = $(hints).find('a');
                        var hrefs = [];
                        for (var i=0; i<urls.length; i++) {{ 
                            var href = urls[i].getAttribute('href');
                            hrefs.push(href);
                        }}
                        return hrefs
                        """)
        return hint_hrefs

    @classmethod
    def load_hints(cls, driver: webdriver.Chrome, type_: int = 0) -> typing.List[Hint]:
        hint_hrefs = cls.find_hint_urls(driver, type_)
        hints = []
        gtr = {
            0: Hint,
            1: PenalizedHint,
            2: Bonus,
        }[type_]
        for href in hint_hrefs:
            hint = gtr.from_html(driver, href)
            hints.append(hint)

        return hints

    @classmethod
    def load_tasks(cls, driver: webdriver.Chrome) -> typing.List[Task]:
        # noinspection PyBroadException
        try:
            driver.find_element_by_id(Task.TASK_ID_ELEMENT)
        except Exception:
            tasks = []
        else:
            tasks = [Task.from_html(driver)]

        return tasks

    @classmethod
    def load_answers(cls, driver: webdriver.Chrome, domain: str) -> typing.List[Answer]:
        # noinspection PyBroadException
        driver.find_element_by_id(Answer.SHOW_ANSWERS_ID).click()
        wait(driver, "hdnSectorNames_0")
        # noinspection PyBroadException
        try:
            edit_urls = driver.execute_script("""
            var edits = $("a[title='Edit']");
            var res = [];
            for (var i = 0; i < edits.length; i++) {
                res.push(edits[i].getAttribute("href"));
            }
            return res
            """)
            sector_names = driver.execute_script("""return $('#hdnSectorNames_0').val()""")
            if sector_names is None:
                sector_names = []
            else:
                sector_names = eval(f"{{{sector_names}}}").values()
        except Exception as e:
            print(e)
            answers = []
        else:
            if not sector_names:
                sector_names = [None]
            answers = [
                Answer.from_html(driver, url, name, domain)
                for url, name in zip(edit_urls, sector_names)
            ]

        return answers

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
            domain: str,
            game_id: int,
            level_id: int,
            past_game: bool = False,
    ) -> Level:
        driver.get(cls.current_level_url(domain, game_id, level_id))
        name = LevelName.from_html(driver, game_id, level_id)
        if not past_game:
            ap = Autopass.from_html(driver)
        else:
            ap = Autopass.from_past_html(driver)
        block = AnswerBlock.from_html(driver)
        sectors = SectorsToCover.from_html(driver)
        time.sleep(2)

        tasks = cls.load_tasks(driver)
        time.sleep(2)
        hint_types = []
        for type_ in range(3):
            hint_type = cls.load_hints(driver, type_)
            hint_types.append(hint_type)
            time.sleep(2)
        answers = cls.load_answers(driver, domain)

        # noinspection PyTypeChecker
        inst = cls(
            domain, game_id, level_id,
            name, ap, block,
            sectors,
            tasks, *hint_types,
            answers,
        )

        return inst

    def hint_edit_url(self, type_: int = 0):
        if type_ <= 1:
            path = "./PromptEdit.aspx?gid={gid}&level={lid}"
            if type_ == 1:
                path += "&penalty=1"
            args = [repr(path), repr(f'Prompt_{{gid}}_{{lid}}')]
        else:
            path = './BonusEdit.aspx?gid={gid}&level={lid}&action=add'
            args = [repr(path)]

        args_str = ",".join(args)
        hint_url = f"GameEditor({args_str});"
        hint_url = hint_url.format(
            gid=self.game_id,
            lid=self.level_id
        )
        return hint_url

    def store_hints(self, gci: GameCustomInfo, type_: int = 0) -> None:
        driver = gci.driver
        if gci.keep_existing_hint_type(type_):
            hint_urls = []
        else:
            hint_urls = self.find_hint_urls(driver, type_)
        hints = {
            0: self.hints,
            1: self.penalized_hints,
            2: self.bonuses,
        }[type_]
        for hint, hint_url in itertools.zip_longest(hints, hint_urls):
            if hint_url is None:
                hint_url = self.hint_edit_url(type_)
            elif hint is None:
                continue

            try:
                hint.to_html(driver, hint_url)
            except selenium.common.exceptions.JavascriptException:
                gci.login()
                gci.navigate_to_level(self.level_id)
                hint.to_html(driver, hint_url)

            time.sleep(2)
        return None

    @property
    def has_sectors(self) -> bool:
        return self.answers and not(len(self.answers) == 1 and self.answers[0].name is None)

    def store_answers(self, gci: GameCustomInfo) -> None:
        driver = gci.driver
        driver.find_element_by_id(Answer.SHOW_ANSWERS_ID).click()

        has_no_sectors = bool(not self.has_sectors and self.answers)
        initial_and_other_func = {
            True: (
                """$("a[title='Add answers']").click()""",
                """$("a[title='Add answers']").click()""",
            ),
            False: (
                """$("a[title='Add sector']").click()""",
                """$("a[title='Add answers']")[{j}].click()""",
            ),
        }[has_no_sectors]
        # TODO: fix this when many sectors with more than 10 codes. Currently fails after 1st sector completes
        for i, answer in enumerate(self.answers):
            funcs = itertools.chain(
                [(initial_and_other_func[0], True)],
                itertools.repeat((initial_and_other_func[1], False)),
            )
            for part, (func, is_first_time) in zip(answer.parts(), funcs):
                func_formatted = func.format(j=i+1)
                try:
                    driver.execute_script(func_formatted)
                    part.to_html(
                        driver,
                        has_sectors=not has_no_sectors,
                        is_first_time=is_first_time,
                    )
                    wait_url_contains(driver, "addanswers", contains=False)
                except selenium.common.exceptions.JavascriptException:
                    gci.login()
                    gci.navigate_to_level(self.level_id)
                    driver.execute_script(func_formatted)
                    part.to_html(
                        driver,
                        has_sectors=not has_no_sectors,
                        is_first_time=is_first_time,
                    )
        return None

    def to_html(self, gci: GameCustomInfo) -> None:
        driver = gci.driver
        gci.navigate_to_level(self.level_id)
        self.name.to_html(driver, self.game_id, self.level_id)
        self.autopass.to_html(driver)
        self.answer_block.to_html(driver)
        time.sleep(2)
        for task in self.tasks:
            task.to_html(driver)
            time.sleep(2)
        for type_ in range(3):
            self.store_hints(gci, type_)
            time.sleep(2)
        self.store_answers(gci)
        if self.has_sectors and len(self.answers) != 1:
            time.sleep(2)
            self.sectors_to_cover.to_html(driver)
        return None

    def to_file(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)
        return None

    @classmethod
    def from_file(cls, path: str) -> Level:
        with open(path, "rb") as f:
            orig_game: Level = pickle.load(f)
        return orig_game
