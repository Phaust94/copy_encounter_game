
import typing
import pickle

from copy_encounter_game.game import Game

__all__ = [
    "save_game",
    "load_game",
]


def save_game(
        source_game_id: int,
        domain: str,
        creds: typing.Dict[str, str],
        path_to_store_game: str,
        chrome_driver_path: str,
        levels_subset: typing.Set[int] = None,
) -> None:
    orig_game = Game.from_html(
        source_game_id,
        domain,
        creds,
        chrome_driver_path=chrome_driver_path,
        levels_subset=levels_subset,
    )

    with open(path_to_store_game, "wb") as f:
        pickle.dump(orig_game, f)
    return None


def load_game(
        target_game_id: int,
        domain: str,
        creds: typing.Dict[str, str],
        game_file_path: str,
        chrome_driver_path: str,
        game_manipulation: typing.Callable[[Game], Game] = None,
) -> None:
    with open(game_file_path, "rb") as f:
        orig_game: Game = pickle.load(f)

    orig_game.domain = domain
    orig_game.game_id = target_game_id
    if game_manipulation is not None:
        orig_game = game_manipulation(orig_game)
    orig_game.to_html(creds, chrome_driver_path)
    return None
