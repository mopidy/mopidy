import pathlib


def path_to_data_dir(name):
    path = pathlib.Path(__file__).parent / "data" / name
    return path.resolve()
