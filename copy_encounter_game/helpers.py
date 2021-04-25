from __future__ import annotations

from dataclasses import dataclass

from selenium import webdriver

from copy_encounter_game.constants import ADMIN_URL

__all__ = [
    "init",
    "ScriptedPart",
]


def init(
        creds: dict,
        domain: str,
        chrome_driver_path: str,
) -> webdriver.Chrome:
    driver = webdriver.Chrome(
        executable_path=chrome_driver_path,
    )
    driver.get(ADMIN_URL.format(domain=domain))

    login = driver.find_element_by_id("txtLogin")
    login.send_keys(creds["user"])
    pwd = driver.find_element_by_id("txtPassword")
    pwd.send_keys(creds["password"])

    sbm = driver.find_element_by_xpath("/html/body/div[1]/form/div/div[1]/input[3]")
    sbm.submit()
    return driver


@dataclass
class ScriptedPart:
    driver: webdriver.Chrome
    script: str

    def __enter__(self):
        self.driver.execute_script(self.script)
        self.driver.switch_to_window(self.driver.window_handles[1])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.close()
        self.driver.switch_to_window(self.driver.window_handles[0])
        return None
