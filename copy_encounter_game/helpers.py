from __future__ import annotations

from dataclasses import dataclass

from selenium import webdriver

from copy_encounter_game.constants import ADMIN_URL

__all__ = [
    "init",
    "ScriptedPart",
    "chunks",
    "DedicatedItem",
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
    explicitely_close_window: bool = True

    def __enter__(self):
        self.driver.execute_script(self.script)
        self.driver.switch_to_window(self.driver.window_handles[1])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.explicitely_close_window:
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
        return None


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
