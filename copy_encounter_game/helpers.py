from __future__ import annotations

from dataclasses import dataclass

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

__all__ = [
    "init",
    "ScriptedPart",
    "chunks",
    "DedicatedItem",
    "wait",
]


def init(
        creds: dict,
        domain: str,
        chrome_driver_path: str = None,
        driver: webdriver.Chrome = None,
) -> webdriver.Chrome:

    return driver


@dataclass
class ScriptedPart:
    driver: webdriver.Chrome
    script: str
    explicitely_close_window: bool = True
    wait_for_value: str = None
    wait_for_type: str = "ID"
    timeout: int = 2

    def __enter__(self):
        self.driver.execute_script(self.script)
        self.driver.switch_to.window(self.driver.window_handles[1])
        if self.wait_for_value:
            self.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.explicitely_close_window:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        return None

    def wait(self) -> None:
        return wait(self.driver, self.wait_for_value, self.wait_for_type, self.timeout)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class DedicatedItem:

    @staticmethod
    def _get_for_who(driver: webdriver.Chrome) -> int:
        hint_for = driver.execute_script(
            """
                        var opt = $('select.input')[0].options;
                        var team_id = null;
                        for (let i = 0; i < opt.length;i++) {
                            if (opt[i].selected) {
                                 team_id = opt[i].value;
                            }
                        }
                        team_id = parseInt(team_id)
                        return team_id;
                    """
        )
        return hint_for

    @staticmethod
    def _set_for_who(driver: webdriver.Chrome, who: int) -> None:
        driver.execute_script(
            f"""
                            var opt = $('select.input')[0].options;
                            for (let i = 0; i < opt.length;i++) {{
                                if (opt[i].value == {who}) {{
                                     opt[i].selected = true;
                                }}
                            }}
                        """
        )
        return None


def wait(
    driver: webdriver.Chrome,
    value: str,
    type_: str = "ID",
    timeout: int = 2,
) -> None:
    type_ = getattr(By, type_)
    try:
        element_present = ec.presence_of_element_located((type_, value))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        pass
    return None
