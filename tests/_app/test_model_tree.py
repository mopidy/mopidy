import re

import pydantic
from rich.console import Console
from rich.text import Text

from mopidy._app.model_tree import ModelTree
from mopidy.models import Track
from mopidy.types import Uri

LONG_URI = "http://example.com/" + "a" * 100 + "/end"


class Child(pydantic.BaseModel):
    name: str


class Parent(pydantic.BaseModel):
    uri: Uri | None = None
    name: str | None = None
    playable: bool | None = None
    length: int | None = None
    data: bytes | None = None
    child: Child | None = None
    children: tuple[Child, ...] = ()
    tags: frozenset[str] = frozenset()
    uris: tuple[Uri, ...] = ()


def render(model: pydantic.BaseModel) -> str:
    tree = ModelTree("root")
    tree.add_model(model)
    console = Console(record=True, width=80)
    console.print(tree)
    return "\n".join(line.rstrip() for line in console.export_text().splitlines())


def unwrap(output: str) -> str:
    return re.sub(r"[\s│├└─]+", "", output)


def test_add_model_shows_fields_as_key_value_leaves():
    output = render(Parent(name="foo", playable=True))

    assert output.splitlines() == [
        "root",
        "├── name      foo",
        "├── playable  yes",
        "└── child     none",
    ]


def test_add_model_leaves_out_fields_that_are_none():
    output = render(Parent(name="foo"))

    assert "uri" not in output
    assert "playable" not in output


def test_add_model_shows_none_for_a_missing_related_model():
    output = render(Parent())

    assert output.splitlines() == ["root", "└── child  none"]


def test_add_model_shows_a_related_model_as_a_branch():
    output = render(Parent(child=Child(name="bar")))

    assert output.splitlines() == ["root", "└── child", "    └── name  bar"]


def test_add_model_numbers_the_items_of_a_tuple():
    output = render(Parent(child=Child(name="a"), uris=(Uri("x:1"), Uri("x:2"))))

    assert output.splitlines()[-3:] == [
        "└── uris",
        "    ├── 1  x:1",
        "    └── 2  x:2",
    ]


def test_add_model_sorts_the_items_of_a_frozenset():
    output = render(Parent(child=Child(name="a"), tags=frozenset({"b", "a"})))

    assert output.splitlines()[-3:] == [
        "└── tags",
        "    ├── 1  a",
        "    └── 2  b",
    ]


def test_add_model_leaves_out_empty_collections():
    output = render(Parent())

    assert "children" not in output
    assert "tags" not in output


def test_add_model_does_not_show_the_type_name_of_mopidy_models():
    output = render(Track(uri=Uri("x:1")))

    assert "model" not in output


def test_add_model_formats_length_as_minutes_and_seconds():
    output = render(Parent(length=64608))

    assert "length  64608 (1:04.608)" in output


def test_add_model_formats_bytes_as_the_size():
    output = render(Parent(data=b"abc"))

    assert "data   3 bytes" in output


def test_add_model_wraps_uris():
    output = render(Parent(uri=Uri(LONG_URI), uris=(Uri(LONG_URI),)))

    assert unwrap(output).count(LONG_URI) == 2
    assert "…" not in output


def test_add_model_shortens_other_long_values():
    output = render(Parent(name="b" * 100))

    assert "b" * 100 not in output
    assert "…" in output


def test_add_model_keeps_the_key_column_width_for_long_values():
    output = render(Parent(name="b" * 100, playable=True))

    assert "├── name      bbb" in output


def test_add_leaf_wraps_if_asked():
    tree = ModelTree("root")
    tree.add_leaf("error", "b" * 100, width=len("error"), wrap=True)
    console = Console(record=True, width=80)
    console.print(tree)

    assert unwrap(console.export_text()).count("b" * 100) == 1


def test_add_text():
    tree = ModelTree("root")
    tree.add_text(Text("no entries"))
    console = Console(record=True, width=80)
    console.print(tree)

    assert console.export_text().splitlines()[1] == "└── no entries"
