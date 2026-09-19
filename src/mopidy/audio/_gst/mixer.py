from __future__ import annotations

from typing import TYPE_CHECKING

from pykka.typing import proxy_method

from mopidy.types import Percentage

if TYPE_CHECKING:
    from mopidy._exts.softwaremixer.mixer import SoftwareMixerProxy
    from mopidy._lib.gi import Gst


class GstSoftwareMixerAdapter:
    _mixer: SoftwareMixerProxy
    _element: Gst.Element | None

    def __init__(self, mixer: SoftwareMixerProxy) -> None:
        self._mixer = mixer
        self._element = None

    def setup(
        self,
        element: Gst.Element,
        gst_mixer: GstSoftwareMixerAdapterProxy,
    ) -> None:
        self._element = element
        self._mixer.setup(gst_mixer)

    def teardown(self) -> None:
        self._mixer.teardown()

    def get_volume(self) -> Percentage:
        assert self._element
        return Percentage(round(self._element.get_property("volume") * 100))

    def set_volume(self, volume: Percentage) -> None:
        assert self._element
        self._element.set_property("volume", volume / 100.0)
        self._mixer.trigger_volume_changed(self.get_volume())

    def get_mute(self) -> bool:
        assert self._element
        return self._element.get_property("mute")

    def set_mute(self, mute: bool) -> None:
        assert self._element
        self._element.set_property("mute", bool(mute))
        self._mixer.trigger_mute_changed(self.get_mute())


class GstSoftwareMixerAdapterProxy:
    get_volume = proxy_method(GstSoftwareMixerAdapter.get_volume)
    set_volume = proxy_method(GstSoftwareMixerAdapter.set_volume)
    get_mute = proxy_method(GstSoftwareMixerAdapter.get_mute)
    set_mute = proxy_method(GstSoftwareMixerAdapter.set_mute)
