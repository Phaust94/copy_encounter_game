from __future__ import annotations

import time
from dataclasses import dataclass, field
import typing
import pickle
import os

from selenium import webdriver

from copy_encounter_game.game.level import Level
from copy_encounter_game.helpers import PrettyPrinter
from copy_encounter_game.constants import MANAGER_URL
from copy_encounter_game.game.meta_info import LevelName
from copy_encounter_game.game.game_files import GameFiles
from copy_encounter_game.game.game_custom_info import GameCustomInfo

__all__ = [
    "Game",
]


@dataclass(repr=False)
class Game(PrettyPrinter):
    _domain: str
    _game_id: int
    levels: typing.List[Level] = field(default_factory=list)
    files: GameFiles = field(default_factory=GameFiles)

    @property
    def game_id(self) -> int:
        return self._game_id

    @game_id.setter
    def game_id(self, value: int):
        self._game_id = value
        for level in self.levels:
            level.game_id = value

    @property
    def domain(self) -> str:
        return self._domain

    @domain.setter
    def domain(self, value: str):
        self._domain = value
        for level in self.levels:
            level.domain = value

    @property
    def n_levels(self) -> int:
        return len(self.levels)

    @classmethod
    def get_n_levels(
            cls,
            driver: webdriver.Chrome,
            domain: str,
            game_id: int
    ) -> int:
        mgr_url = MANAGER_URL.format(domain=domain, gid=game_id)
        driver.get(mgr_url)
        n_levels = driver.execute_script("""return $('input[name*="txtLevelName_"]').length;""")
        return n_levels

    @classmethod
    def from_html(
            cls,
            game_id: int,
            domain: str, creds: typing.Dict[str, str],
            chrome_driver_path: str,
            levels_subset: typing.Set[int] = None,
            sleep_time: int = 10,
            download_files: bool = False,
            files_location: str = None,
            path_template: str = None,
            read_cache: bool = False,
            past_game: bool = False,
    ) -> Game:
        gci = GameCustomInfo(domain, game_id, creds, chrome_driver_path)
        driver = gci.driver
        n_levels = cls.get_n_levels(driver, domain, game_id)

        if download_files:
            files = GameFiles.from_html(driver, game_id, domain, files_location)
        else:
            files = GameFiles()

        levels = []
        levels_to_copy = list(range(1, n_levels + 1))
        if levels_subset is not None:
            levels_to_copy = [el for el in levels_to_copy if el in levels_subset]
        for i, level_id in enumerate(levels_to_copy):

            tmp_file = path_template.format(lvl_id=level_id)
            if read_cache and os.path.exists(tmp_file):
                level = Level.from_file(tmp_file)
            else:
                level = Level.from_html(
                    driver, domain, game_id, level_id,
                    past_game=past_game,
                )
                level.to_file(tmp_file)

                if i < len(levels_to_copy) - 1:
                    time.sleep(sleep_time)

            levels.append(level)
        inst = cls(domain, game_id, levels, files)
        return inst

    def to_html(
            self,
            creds: typing.Dict[str, str],
            chrome_driver_path: str,
            sleep_time: int = 10,
            upload_files: bool = False,
            keep_existing_hints: bool = False,
            keep_existing_penalized_hints: bool = False,
            keep_existing_bonuses: bool = False,
            keep_existing_answers: bool = False,
    ) -> None:
        gci = GameCustomInfo(
            self.domain, self.game_id, creds, chrome_driver_path,
            keep_existing_hints=keep_existing_hints,
            keep_existing_penalized_hints=keep_existing_penalized_hints,
            keep_existing_bonuses=keep_existing_bonuses,
            keep_existing_answers=keep_existing_answers,
        )
        for i, level in enumerate(self.levels):
            level.to_html(gci)
            if i < len(self.levels) - 1:
                time.sleep(sleep_time)

        if upload_files:
            self.files.to_html(gci.driver, self.game_id, self.domain)

        return None

    def to_file(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)
        return None

    @classmethod
    def from_file(cls, path: str) -> Game:
        with open(path, "rb") as f:
            orig_game: Game = pickle.load(f)
        return orig_game

    @property
    def level_to_id(self) -> typing.Dict[int, Level]:
        res = {level.level_id: level for level in self.levels}
        return res

    def __rshift__(self, other: Game) -> Game:
        assert self.domain == other.domain and self.game_id == other.game_id, "Can't merge two unrelated games"
        new_levels = {**other.level_to_id, **self.level_to_id}
        new_levels = sorted(new_levels.values(), key=lambda x: x.level_id)
        # noinspection PyArgumentList
        res = self.__class__(self._domain, self._game_id, new_levels)
        return res

    def __setstate__(self, state: typing.Dict[str, typing.Any]):
        for lvl in state["levels"]:
            lvl: Level
            n = lvl.name
            n.__class__ = LevelName
            lvl.name = n
        self.__dict__ = state
        return None

