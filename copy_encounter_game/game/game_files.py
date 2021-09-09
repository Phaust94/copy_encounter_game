"""
Game files list
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
import typing

import requests
from selenium import webdriver

from copy_encounter_game.constants import MANAGER_URL, CHUNK_SIZE_FILES
from copy_encounter_game.helpers import chunks, ScriptedPart, PrettyPrinter

__all__ = [
    "GameFiles",
]


@dataclass(repr=False)
class GameFiles(PrettyPrinter):
    file_urls: typing.List[str] = field(default_factory=list)
    file_location: str = None

    @property
    def file_names(self) -> typing.List[str]:
        fnames = [
            file.split("/")[-1]
            for file in self.file_urls
        ]
        return fnames

    @staticmethod
    def assume_manager_url(
            driver: webdriver.Chrome,
            game_id: int,
            domain: str,
    ) -> None:

        mgr_url = MANAGER_URL.format(domain=domain, gid=game_id)
        if driver.current_url != mgr_url:
            driver.get(mgr_url)

        return None

    @classmethod
    def find_file_urls(
            cls,
            driver: webdriver.Chrome,
            game_id: int,
            domain: str,
    ) -> typing.List[str]:
        cls.assume_manager_url(driver, game_id, domain)

        script = """
                var urls = [];
                $('.border_rad2').find('a').filter(function (i, el) {if (el.id.match(/lnkViewFile/)) {return el}}).each(
                    function (i, el){urls.push(el.href)}
                );
                return urls;
                """

        file_urls = driver.execute_script(script)
        return file_urls

    @classmethod
    def find_file_names(
            cls,
            driver: webdriver.Chrome,
            game_id: int,
            domain: str,
    ) -> typing.List[str]:
        file_urls = cls.find_file_urls(driver, game_id, domain)
        fnames = [
            file.split("/")[-1]
            for file in file_urls
        ]
        return fnames

    @classmethod
    def from_html(
            cls,
            driver: webdriver.Chrome,
            game_id: int,
            domain: str,
            files_location: typing.Optional[str] = None,
    ) -> GameFiles:

        file_urls = cls.find_file_urls(driver, game_id, domain)
        inst = cls(file_urls, files_location)
        if files_location:
            inst.download_files(files_location)
        return inst

    def download_files(self, location: str) -> None:
        for url, name in zip(self.file_urls, self.file_names):
            res = requests.get(url)
            res.raise_for_status()
            fpath = os.path.join(location, name)
            with open(fpath, "wb") as handle:
                handle.write(res.content)
        return None

    def to_html(
            self,
            driver: webdriver.Chrome,
            game_id: int,
            domain: str,
    ) -> None:

        assert self.file_location is not None, "Can't upload files without explicit location"

        existing_fnames = self.find_file_names(driver, game_id, domain)

        self.assume_manager_url(driver, game_id, domain)

        fnames = [f for f in self.file_names if f not in existing_fnames]
        url_to_click = f"javascript:Editor('./FileUploader.aspx?gid={game_id}', 'FileUploader_{game_id}');"

        for chunk in chunks(fnames, CHUNK_SIZE_FILES):
            with ScriptedPart(driver, url_to_click, explicitely_close_window=False):
                for i, el in enumerate(chunk):
                    tg = driver.find_element_by_css_selector(f'[name="inputFile{i + 1}"]')
                    path = os.path.join(self.file_location, el)
                    tg.send_keys(path)

                upload_btn = driver.find_element_by_css_selector("[title='Upload']")
                upload_btn.click()

        return None
