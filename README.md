This library allows to copy an Encounter game from one domain to another, or just create a copy on the same domain.

As of version 1.2.0, this script only works for Real, Poins and Brainstorm game types.

The usage is simple:
First, scrape a game from Encounter engine and store it to a local file:

```python
from copy_encounter_game import save_game

CHROME_DRIVER_PATH = r"C:\Users\PATH_TO_SCRHOMEDRIVER_FILE.exe"

CREDS = {
    "user": "ENCOUNTER_USERNAME",
    "password": "ENCOUNTER_PASSWORD",
}
SOURCE_GAME_ID = <SOURCE_GAME_ID>
SOURCE_DOMAIN = "demo.en.cx"

LEVELS_SUBSET = None
# Might be either None, or a set of int level ids, starting from 1

PATH_STORE_GAME = r"D:\data\quest\{domain}_{gid}.pcl"
fn = PATH_STORE_GAME.format(domain=SOURCE_DOMAIN, gid=SOURCE_GAME_ID)
save_game(
    SOURCE_GAME_ID, SOURCE_DOMAIN, CREDS,
    fn,
    CHROME_DRIVER_PATH, 
    levels_subset=LEVELS_SUBSET
)
```

Then, reinstantiate an existing local game file onto a new existing game:
```python

from copy_encounter_game import load_game, Game

CHROME_DRIVER_PATH = r"C:\Users\PATH_TO_SCRHOMEDRIVER_FILE.exe"


CREDS = {
    "user": "ENCOUNTER_USERNAME",
    "password": "ENCOUNTER_PASSWORD",
}
TARGET_GAME_ID = <TARGET_GAME_ID>
TARGET_DOMAIN = "kharkiv.en.cx"


def game_manipulation(game: Game) -> Game:
    # A function called on a Game instance to potentially modify game code
    return game


PATH_STORE_GAME = r"D:\data\quest\{domain}_{gid}.pcl"
SOURCE_GAME_ID = <SOURCE_GAME_ID>
SOURCE_DOMAIN = "demo.en.cx"
fn = PATH_STORE_GAME.format(domain=SOURCE_DOMAIN, gid=SOURCE_GAME_ID)
load_game(
    TARGET_GAME_ID, TARGET_DOMAIN, CREDS,
    fn, CHROME_DRIVER_PATH,
    game_manipulation=game_manipulation
)
```