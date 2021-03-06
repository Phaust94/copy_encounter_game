
import typing
import os

from copy_encounter_game.game import Game, Answer, Autopass, AnswerBlock, Task, Bonus, Hint, LevelName, SectorsToCover

__all__ = [
    "save_game",
    "load_game",
]


def save_game(
        source_game_id: int,
        source_domain: str,
        creds: typing.Dict[str, str],
        path_to_store_game: str,
        chrome_driver_path: str,
        levels_subset: typing.Set[int] = None,
        keep_existing: bool = True,
        download_files: bool = False,
        files_location: typing.Optional[str] = None,
        past_game: bool = False,
        skip_entities: typing.Set[typing.Union[
            type(Answer), type(Autopass), type(AnswerBlock), type(Task),
            type(Bonus), type(Hint), type(LevelName), type(SectorsToCover),
        ]] = None,
) -> None:
    skip_entities = skip_entities or set()
    dir_ = os.path.dirname(path_to_store_game)
    fname, ext = os.path.splitext(path_to_store_game)
    temp_fp = os.path.join(
        dir_,
        f"{fname}_temp_lvl{{lvl_id}}.{ext}"
    )

    existing_game = None
    if keep_existing:
        try:
            existing_game = Game.from_file(path_to_store_game)
        except FileNotFoundError:
            pass

    orig_game = Game.from_html(
        source_game_id,
        source_domain,
        creds,
        chrome_driver_path=chrome_driver_path,
        levels_subset=levels_subset,
        download_files=download_files,
        files_location=files_location,
        path_template=temp_fp,
        read_cache=not keep_existing or not existing_game,
        past_game=past_game,
        skip_entities=skip_entities,
    )

    if existing_game:
        orig_game = orig_game >> existing_game

    orig_game.to_file(path_to_store_game)
    return None


def load_game(
        target_game_id: int,
        target_domain: str,
        creds: typing.Dict[str, str],
        game_file_path: str,
        chrome_driver_path: str,
        game_manipulation: typing.Callable[[Game], Game] = None,
        upload_files: bool = False,
        keep_existing_hints: bool = False,
        keep_existing_penalized_hints: bool = False,
        keep_existing_bonuses: bool = False,
        keep_existing_answers: bool = False,
) -> None:
    orig_game = Game.from_file(game_file_path)

    orig_game.domain = target_domain
    orig_game.game_id = target_game_id
    if game_manipulation is not None:
        orig_game = game_manipulation(orig_game)
    orig_game.to_html(
        creds, chrome_driver_path,
        upload_files=upload_files,
        keep_existing_hints=keep_existing_hints,
        keep_existing_penalized_hints=keep_existing_penalized_hints,
        keep_existing_bonuses=keep_existing_bonuses,
        keep_existing_answers=keep_existing_answers,
    )
    return None
