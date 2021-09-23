from __future__ import annotations

from dataclasses import dataclass, fields

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

__all__ = [
    "ScriptedPart",
    "chunks",
    "DedicatedItem",
    "wait", "wait_url_contains",
    "PrettyPrinter",
]


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
    wait_for_visible: bool = True,
) -> None:
    type_ = getattr(By, type_)
    wait_func = "presence_of_element_located" if wait_for_visible else "invisibility_of_element_located"
    try:
        wait_func_obj = getattr(ec, wait_func)
        element_present = wait_func_obj((type_, value))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        pass
    return None


def wait_url_contains(
    driver: webdriver.Chrome,
    value: str,
    timeout: int = 2,
    contains: bool = True,
) -> None:
    wait_func = "url_contains" if contains else "url_not_contains"
    try:
        wait_func_obj = getattr(ec, wait_func)
        element_present = wait_func_obj(value)
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        pass
    return None


@dataclass
class PrettyPrinter:
    def __str__(self):
        lines = [self.__class__.__name__ + ':']
        for f in fields(self):
            lines += '{}: {!r}'.format(f.name, getattr(self, f.name)).split('\n')
        return '\n    '.join(lines)

    def __repr__(self):
        return str(self)


# noinspection PyPep8Naming
class url_not_contains(object):
    """ An expectation for checking that the current url DOESN'T contain a
    case-sensitive substring.
    url is the fragment of url expected,
    returns True when the url matches, False otherwise
    """
    def __init__(self, url):
        self.url = url

    def __call__(self, driver):
        return self.url not in driver.current_url


ec.url_not_contains = url_not_contains
