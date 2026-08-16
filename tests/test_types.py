import pytest

from mopidy.models import Album
from mopidy.types import Date, DateOrYear, Year


@pytest.mark.parametrize(
    ("cls", "value"),
    [
        (DateOrYear, "1977"),
        (Date, "1977-01-01"),
        (Year, "1977"),
    ],
)
def test_deprecated_date_types_warn(cls, value):
    with pytest.warns(DeprecationWarning, match="Use ReleaseDate instead"):
        result = cls(value)

    assert result == value
    assert isinstance(result, str)


def test_deprecated_date_types_are_accepted_by_models():
    with pytest.warns(DeprecationWarning, match="Use ReleaseDate instead"):
        date = Date("1977-01-01")

    album = Album(name="Album", date=date)

    assert album.date == "1977-01-01"
    assert type(album.date) is str


def test_date_and_year_are_subtypes_of_date_or_year():
    assert issubclass(Date, DateOrYear)
    assert issubclass(Year, DateOrYear)
