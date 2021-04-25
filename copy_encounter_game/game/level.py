"""
Game meta info
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
import typing
import itertools

from selenium import webdriver

from copy_encounter_game.game.meta_info import GameName, Autopass, AnswerBlock
from copy_encounter_game.game.task import Task
from copy_encounter_game.game.hint import Hint, PenalizedHint
from copy_encounter_game.game.answer import Answer

__all__ = [
    "Level",
]


@dataclass
class Level:
    domain: str
    game_id: int
    level_id: int
    name: GameName = GameName()
    autopass: Autopass = Autopass()
    answer_block: AnswerBlock = AnswerBlock()
    tasks: typing.List[Task] = field(default_factory=list)
    hints: typing.List[Hint] = field(default_factory=list)
    penalized_hints: typing.List[PenalizedHint] = field(default_factory=list)
    answers: typing.List[Answer] = field(default_factory=list)

    LEVEL_URL = "http://{domain}/Administration/Games/LevelEditor.aspx?gid={gid}&level={lid}"

    @classmethod
    def current_level_url(cls, domain: str, game_id: int, level_id: int) -> str:
        return cls.LEVEL_URL.format(domain=domain, gid=game_id, lid=level_id)

    @classmethod
    def find_hint_urls(cls, driver: webdriver.Chrome, is_penalized: bool = False) -> typing.List[str]:
        time.sleep(0.3)
        num = 2 + is_penalized
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
    def load_hints(cls, driver: webdriver.Chrome, is_penalized: bool = False) -> typing.List[Hint]:
        hint_hrefs = cls.find_hint_urls(driver, is_penalized)
        hints = []
        gtr = PenalizedHint if is_penalized else Hint
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
        time.sleep(0.3)
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
            sector_names = eval(f"{{{sector_names}}}").values()
        except Exception:
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
    ) -> Level:
        driver.get(cls.current_level_url(domain, game_id, level_id))
        name = GameName.from_html(driver, game_id, level_id)
        ap = Autopass.from_html(driver)
        block = AnswerBlock.from_html(driver)

        tasks = cls.load_tasks(driver)
        hints = cls.load_hints(driver, False)
        penalized_hints = cls.load_hints(driver, True)
        answers = cls.load_answers(driver, domain)

        # noinspection PyTypeChecker
        inst = cls(
            domain, game_id, level_id,
            name, ap, block,
            tasks, hints,
            penalized_hints,
            answers,
        )

        return inst

    def store_hints(self, driver: webdriver.Chrome, penalized: bool = False) -> None:
        hint_urls = self.find_hint_urls(driver, penalized)
        hints = self.penalized_hints if penalized else self.hints
        for hint, hint_url in itertools.zip_longest(hints, hint_urls):
            if hint_url is None:
                path = "./PromptEdit.aspx?gid={gid}&level={lid}"
                if penalized:
                    path += "&penalty=1"
                hint_url = f"GameEditor({path!r}, 'Prompt_{{gid}}_{{lid}}');"
                hint_url = hint_url.format(
                    gid=self.game_id,
                    lid=self.level_id
                )
            elif hint is None:
                continue
            hint.to_html(driver, hint_url)
        return None

    def store_answers(self, driver: webdriver.Chrome) -> None:
        driver.find_element_by_id(Answer.SHOW_ANSWERS_ID).click()
        if len(self.answers) == 1 and self.answers[0].name is None:
            driver.execute_script("""$("a[title='Add answers']").click()""")
            self.answers[0].to_html(driver, has_sectors=False)
        else:
            for answer in self.answers:
                driver.execute_script("""$("a[title='Add sector']").click()""")
                answer.to_html(driver, has_sectors=True)
        return None

    def to_html(self, driver: webdriver.Chrome) -> None:
        driver.get(self.current_level_url(self.domain, self.game_id, self.level_id))
        self.name.to_html(driver, self.game_id, self.level_id)
        self.autopass.to_html(driver)
        self.answer_block.to_html(driver)
        for task in self.tasks:
            task.to_html(driver)
        for penalized in (False, True):
            self.store_hints(driver, penalized)
        self.store_answers(driver)
        return None
