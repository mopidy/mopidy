from mopidy.audio.base.scan import ScannerBase, ScanResult
from mopidy.audio.ffpmpv.ffprobe import ffprobe_format_name_to_mime, run_ffprobe

_Result = ScanResult  # Compatibility re-export


class Scanner(ScannerBase):
    def scan(self, uri: str, timeout: float | None = None) -> ScanResult:
        res = run_ffprobe(uri, timeout=timeout or (self._timeout_ms / 1000))
        format_res = res.get("format", {})
        tags = format_res.get("tags", {})
        duration_msec = int(float(format_res.get("duration", 0)) * 1000)
        format_name = format_res.get("format_name")

        return ScanResult(
            uri=uri,
            tags=tags,
            duration=duration_msec,
            seekable=uri.startswith("file://"),
            mime=ffprobe_format_name_to_mime.get(format_name),
            playable=True,  # TODO: this should maybe be figured out too?
        )
