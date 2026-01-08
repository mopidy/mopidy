from importlib import metadata
from typing import override

import cyclopts
import pytest
from dirty_equals import IsInstance
from pytest_mock import MockerFixture

from mopidy import ext
from mopidy._app.extensions import ExtensionManager, ExtensionRecord, ExtensionStatus
from mopidy.config import Config, ConfigSchema, types
from mopidy.exceptions import ExtensionError


class DummyExtension(ext.Extension):
    dist_name = "Mopidy-Dummy"
    ext_name = "dummy"
    version = "1.2.3"

    @override
    def get_default_config(self) -> str:
        return "[foobar]\nenabled = true"

    @override
    def get_command(self) -> cyclopts.App:
        app = cyclopts.App()

        @app.command
        def do_something():
            pass

        return app


@pytest.fixture
def entry_point(mocker: MockerFixture) -> metadata.EntryPoint:
    entry_point = mocker.Mock(spec=metadata.EntryPoint)
    entry_point.group = "mopidy.ext"
    entry_point.name = DummyExtension.ext_name
    entry_point.value = "mopidy_foobar:FoobarExtension"
    entry_point.load = mocker.Mock(return_value=DummyExtension)
    return entry_point


@pytest.fixture
def record(entry_point: metadata.EntryPoint) -> ExtensionRecord:
    return ExtensionRecord.load(entry_point)


def test_load(entry_point: metadata.EntryPoint):
    record = ExtensionRecord.load(entry_point)

    assert record.ext_name == DummyExtension.ext_name
    assert record.entry_point == entry_point
    assert record.status == ExtensionStatus.ENABLED

    assert record.extension == IsInstance(DummyExtension)
    assert record.dist_name == DummyExtension.dist_name
    assert record.version == DummyExtension.version
    assert record.config_schema == IsInstance(ConfigSchema)
    assert record.config_defaults == "[foobar]\nenabled = true"
    assert record.command == IsInstance(cyclopts.App)


def test_load_wrong_group(
    entry_point: metadata.EntryPoint,
    caplog: pytest.LogCaptureFixture,
):
    entry_point.group = "wrong.group"

    record = ExtensionRecord.load(entry_point)

    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR
    assert (
        "Entry point 'dummy' is in invalid group 'wrong.group', expected 'mopidy.ext'"
        in caplog.text
    )


def test_load_fails(
    entry_point: metadata.EntryPoint,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    entry_point.load = mocker.Mock(side_effect=Exception("Failed to load"))

    record = ExtensionRecord.load(entry_point)

    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR
    assert "Loading of extension entry point 'dummy' failed" in caplog.text


def test_load_non_extension_class(
    entry_point: metadata.EntryPoint,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    entry_point.load = mocker.Mock(
        # Not a subclass of ext.Extension
        return_value=object
    )

    record = ExtensionRecord.load(entry_point)

    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR
    assert (
        "Entry point 'dummy' did not contain a valid extension class: <class 'object'>"
        in caplog.text
    )


def test_load_extension_init_fails(
    entry_point: metadata.EntryPoint,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    class ExtensionWithFailingInit(DummyExtension):
        def __init__(self):
            msg = "Initialization failed"
            raise Exception(msg)

    entry_point.load = mocker.Mock(return_value=ExtensionWithFailingInit)

    record = ExtensionRecord.load(entry_point)

    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR
    assert "Instantiating extension from entry point 'dummy' failed" in caplog.text


def test_load_entry_point_name_and_ext_name_mismatch(
    entry_point: metadata.EntryPoint,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    class ExtensionWithWrongExtName(DummyExtension):
        ext_name = "wrong_name"

    entry_point.load = mocker.Mock(return_value=ExtensionWithWrongExtName)

    record = ExtensionRecord.load(entry_point)

    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR
    assert (
        "Entry point name 'dummy' does not match extension's ext_name 'wrong_name'"
        in caplog.text
    )


def test_load_no_config_schema(
    entry_point: metadata.EntryPoint,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    class ExtensionWithNoConfigSchema(DummyExtension):
        @override
        def get_config_schema(self) -> ConfigSchema:
            return None  # pyright: ignore[reportReturnType]

    entry_point.load = mocker.Mock(return_value=ExtensionWithNoConfigSchema)

    record = ExtensionRecord.load(entry_point)

    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR
    assert "Extension 'dummy' does not have a config schema" in caplog.text


def test_load_config_schema_enabled_is_not_boolean(
    entry_point: metadata.EntryPoint,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    class ExtensionWithInvalidConfigSchema(DummyExtension):
        @override
        def get_config_schema(self) -> ConfigSchema:
            schema = super().get_config_schema()
            schema["enabled"] = types.String()
            return schema

    entry_point.load = mocker.Mock(return_value=ExtensionWithInvalidConfigSchema)

    record = ExtensionRecord.load(entry_point)

    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR
    assert (
        "Extension 'dummy' does not have the required 'enabled' config option"
        in caplog.text
    )


def test_load_config_schema_with_invalid_types(
    entry_point: metadata.EntryPoint,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    class ExtensionWithInvalidConfigSchemaTypes(DummyExtension):
        @override
        def get_config_schema(self) -> ConfigSchema:
            schema = super().get_config_schema()
            schema["some_option"] = "not_a_type"
            return schema

    entry_point.load = mocker.Mock(return_value=ExtensionWithInvalidConfigSchemaTypes)

    record = ExtensionRecord.load(entry_point)

    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR
    assert (
        "Extension 'dummy' config schema contains an invalid value "
        "for the option 'some_option'" in caplog.text
    )


def test_load_no_default_config(
    entry_point: metadata.EntryPoint,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    class ExtensionWithNoDefaultConfig(DummyExtension):
        @override
        def get_default_config(self) -> str:
            return ""

    entry_point.load = mocker.Mock(return_value=ExtensionWithNoDefaultConfig)

    record = ExtensionRecord.load(entry_point)

    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR
    assert "Extension 'dummy' does not have a default config" in caplog.text


def test_load_get_command_fails(
    entry_point: metadata.EntryPoint,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    class ExtensionWithFailingGetCommand(DummyExtension):
        @override
        def get_command(self) -> cyclopts.App:
            msg = "Failed to get command"
            raise Exception(msg)

    entry_point.load = mocker.Mock(return_value=ExtensionWithFailingGetCommand)

    record = ExtensionRecord.load(entry_point)

    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR
    assert "Loading command for extension 'dummy' failed" in caplog.text


def test_check(record: ExtensionRecord):
    config = Config({"dummy": {"enabled": True}})
    config_errors = {}

    error = record.check_config_and_env(config=config, config_errors=config_errors)

    assert error is None
    assert record.status == ExtensionStatus.ENABLED


def test_check_when_extension_failed_to_load(record: ExtensionRecord):
    record.status = ExtensionStatus.STOPPED_BY_LOAD_ERROR
    config = Config({"dummy": {"enabled": True}})
    config_errors = {}

    error = record.check_config_and_env(config=config, config_errors=config_errors)

    assert error is None
    assert record.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR


def test_check_disabled_by_config(record: ExtensionRecord):
    config = Config({"dummy": {"enabled": False}})
    config_errors = {}

    error = record.check_config_and_env(config=config, config_errors=config_errors)

    assert error == "Extension disabled by user config"
    assert record.status == ExtensionStatus.DISABLED


def test_check_disabled_by_config_error(record: ExtensionRecord):
    config = Config({"dummy": {"enabled": True}})
    config_errors = {"dummy": {"some_option": "Some config error"}}

    error = record.check_config_and_env(config=config, config_errors=config_errors)

    assert error == "Extension stopped due to config errors"
    assert record.status == ExtensionStatus.STOPPED_BY_CONFIG_ERROR


def test_check_disabled_by_self_check_with_no_extension(
    record: ExtensionRecord,
):
    config = Config({"dummy": {"enabled": True}})
    config_errors = {}
    record.extension = None

    error = record.check_config_and_env(config=config, config_errors=config_errors)

    assert error == "Extension stopped by self-check"
    assert record.status == ExtensionStatus.STOPPED_BY_SELF_CHECK


def test_check_disabled_by_validate_environment_failing_expectedly(
    record: ExtensionRecord,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    config = Config({"dummy": {"enabled": True}})
    config_errors = {}
    record.extension.validate_environment = mocker.Mock(  # type: ignore  # noqa: PGH003
        side_effect=ExtensionError("Environment not valid"),
    )

    error = record.check_config_and_env(config=config, config_errors=config_errors)

    assert error == "Extension stopped by self-check"
    assert record.status == ExtensionStatus.STOPPED_BY_SELF_CHECK
    assert "Extension 'dummy' disabled by self-check" in caplog.text


def test_check_disabled_by_validate_environment_unexpected_error(
    record: ExtensionRecord,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    config = Config({"dummy": {"enabled": True}})
    config_errors = {}
    record.extension.validate_environment = mocker.Mock(  # type: ignore  # noqa: PGH003
        side_effect=Exception("Unexpected error"),
    )

    error = record.check_config_and_env(config=config, config_errors=config_errors)

    assert error == "Extension stopped by self-check"
    assert record.status == ExtensionStatus.STOPPED_BY_SELF_CHECK
    assert "Extension 'dummy' self-check failed unexpectedly" in caplog.text


def test_manager_set_global_twice_fails():
    # Importing the app CLI will set a global ExtensionManager instance
    import mopidy._app.cli  # pyright: ignore[reportUnusedImport]  # noqa: F401, PLC0415

    assert ExtensionManager.get_global() is not None

    # Attempting to set another instance should fail
    manager = ExtensionManager()
    with pytest.raises(RuntimeError) as excinfo:
        ExtensionManager.set_global(manager)

    assert "ExtensionManager already set in context" in str(excinfo.value)


def test_manager_check(record: ExtensionRecord):
    extension_manager = ExtensionManager({"dummy": record})
    config = Config({"dummy": {"enabled": False}})
    config_errors = {}

    errors = extension_manager.check_config_and_env(
        config=config,
        config_errors=config_errors,
    )

    assert errors == {
        "dummy": "Extension disabled by user config",
    }
    assert record.status == ExtensionStatus.DISABLED


@pytest.mark.parametrize(
    ("status", "expected_log"),
    [
        (
            ExtensionStatus.ENABLED,
            "Enabled extensions: dummy",
        ),
        (
            ExtensionStatus.DISABLED,
            "Disabled extensions: dummy",
        ),
        (
            ExtensionStatus.STOPPED_BY_LOAD_ERROR,
            "Extensions which failed to load: dummy",
        ),
        (
            ExtensionStatus.STOPPED_BY_CONFIG_ERROR,
            "Extensions with config errors: dummy",
        ),
        (
            ExtensionStatus.STOPPED_BY_SELF_CHECK,
            "Extensions which failed self-check: dummy",
        ),
    ],
)
def test_manager_log_summary(
    record: ExtensionRecord,
    status: ExtensionStatus,
    caplog: pytest.LogCaptureFixture,
    expected_log: str,
):
    record.status = status
    extension_manager = ExtensionManager({"dummy": record})

    extension_manager.log_summary()

    assert expected_log in caplog.text
