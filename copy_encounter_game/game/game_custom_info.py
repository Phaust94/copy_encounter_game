"""
Custom info about the game
"""

from dataclasses import dataclass, field
import typing

from selenium import webdriver

from copy_encounter_game.constants import ADMIN_URL
from copy_encounter_game.helpers import PrettyPrinter

__all__ = [
    "GameCustomInfo"
]


@dataclass(repr=False)
class GameCustomInfo(PrettyPrinter):
    domain: str
    game_id: int
    creds: typing.Dict[str, str]
    chrome_driver_path: str
    driver: webdriver.Chrome = field(default=None)
    keep_existing_hints: bool = False
    keep_existing_penalized_hints: bool = False
    keep_existing_bonuses: bool = False
    keep_existing_answers: bool = False

    def login(self) -> None:
        self.driver.get(ADMIN_URL.format(domain=self.domain))

        login = self.driver.find_element_by_id("txtLogin")
        login.send_keys(self.creds["user"])
        pwd = self.driver.find_element_by_id("txtPassword")
        pwd.send_keys(self.creds["password"])

        sbm = self.driver.find_element_by_xpath("/html/body/div[1]/form/div/div[1]/input[3]")
        sbm.submit()
        return None

    def navigate_to_level(self, level_id: int) -> None:
        from copy_encounter_game.game.level import Level
        url = Level.current_level_url(self.domain, self.game_id, level_id)
        self.driver.get(url)
        return None

    def __post_init__(self):
        if self.driver is None:
            self.driver = webdriver.Chrome(
                executable_path=self.chrome_driver_path,
            )
        self.login()
        return None

    def keep_existing_hint_type(self, type_: int) -> bool:
        to_keep = {
            0: self.keep_existing_hints,
            1: self.keep_existing_penalized_hints,
            2: self.keep_existing_bonuses,
        }[type_]
        return to_keep
