"""
media_converter.py - clean, reusable FFmpeg conversion layer for DropFlow.

Supported directions
--------------------
* any supported video -> MP4
* MP4 -> MKV / AVI / MOV / WEBM / GIF
* MP4 -> MP3 / AAC / WAV / M4A / FLAC

Video-to-video conversions try a lossless stream copy first (``-c copy``).
If the target container rejects the source streams, the converter falls back
to a compatible re-encode automatically.

The module has no Tk/UI dependencies.  Callbacks run in the worker thread, so a
GUI should marshal them onto its own event loop (DropFlow does this with its
existing progress queue).

Basic usage
-----------
    from media_converter import MediaConverter, ConversionCallbacks

    conv = MediaConverter()
    result = conv.convert("clip.mkv", "mp4", callbacks=ConversionCallbacks(
        on_start=lambda src, fmt: print("start", src, fmt),
        on_progress=lambda pct, msg: print(pct, msg),
        on_success=lambda res: print("done", res.output, res.method),
        on_error=lambda exc: print("failed", exc),
    ))

Async usage
-----------
    handle = conv.convert_async("clip.mp4", "mp3", output_path="clip.mp3")
    # ... later
    handle.join()
    if handle.error:
        ...
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

LOG = logging.getLogger("DropFlow.MediaConverter")
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

VIDEO_INPUT_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv",
    ".m4v", ".mpg", ".mpeg", ".ts", ".3gp", ".ogv",
}
VIDEO_OUTPUT_FORMATS = {"mp4", "mkv", "avi", "mov", "webm", "gif"}
AUDIO_OUTPUT_FORMATS = {"mp3", "aac", "wav", "m4a", "flac"}
SUPPORTED_OUTPUT_FORMATS = VIDEO_OUTPUT_FORMATS | AUDIO_OUTPUT_FORMATS

FORMAT_LABELS = {
    "mp4": "MP4 video (H.264 + AAC)",
    "mkv": "MKV video",
    "avi": "AVI video",
    "mov": "MOV video",
    "webm": "WEBM video (VP9 + Opus)",
    "gif": "Animated GIF",
    "mp3": "MP3 audio",
    "aac": "AAC audio",
    "wav": "WAV audio (PCM)",
    "m4a": "M4A audio (AAC)",
    "flac": "FLAC audio (lossless)",
}


class MediaConversionError(RuntimeError):
    """Any conversion or validation failure."""


class MediaValidationError(MediaConversionError):
    """The input/output request is invalid."""


class MediaCancelled(MediaConversionError):
    """The conversion was cancelled through cancel_event."""


@dataclass
class ConversionResult:
    input: Path
    output: Path
    output_format: str
    method: str                 # "remux", "reencode", or "audio"
    duration: float | None
    size: int
    elapsed: float


@dataclass
class ConversionCallbacks:
    on_start: Callable[[Path, str], None] | None = None
    on_progress: Callable[[float, str], None] | None = None
    on_success: Callable[[ConversionResult], None] | None = None
    on_error: Callable[[Exception], None] | None = None


class ConversionHandle:
    """Handle returned by MediaConverter.convert_async()."""

    def __init__(self, converter: "MediaConverter", input_path: str | Path,
                 output_format: str, output_path: str | Path | None,
                 overwrite: bool, callbacks: ConversionCallbacks):
        self.converter = converter
        self.input_path = input_path
        self.output_format = output_format
        self.output_path = output_path
        self.overwrite = overwrite
        self.callbacks = callbacks
        self.cancel_event = threading.Event()
        self.result: ConversionResult | None = None
        self.error: Exception | None = None
        self._thread = threading.Thread(target=self._run, name="MediaConversion",
                                        daemon=True)

    def start(self):
        self._thread.start()
        return self

    def _run(self):
        try:
            self.result = self.converter.convert(
                self.input_path, self.output_format,
                output_path=self.output_path,
                overwrite=self.overwrite,
                callbacks=self.callbacks,
                cancel_event=self.cancel_event,
            )
        except Exception as exc:  # noqa: BLE001
            self.error = exc

    def cancel(self):
        self.cancel_event.set()

    def join(self, timeout: float | None = None):
        self._thread.join(timeout)
        return self.result

    def is_alive(self) -> bool:
        return self._thread.is_alive()


class MediaConverter:
    """FFmpeg-backed universal media converter."""

    def __init__(self, ffmpeg_path: str | Path | None = None,
                 ffprobe_path: str | Path | None = None):
        self.ffmpeg = self._resolve_ffmpeg(ffmpeg_path)
        self.ffprobe = self._resolve_ffprobe(ffprobe_path)
        self._encoders: set[str] | None = None

    # ------------------------------------------------------------------ #
    #  Tool discovery
    # ------------------------------------------------------------------ #
    @staticmethod
    def _verify_ffmpeg(path: Path) -> bool:
        try:
            res = subprocess.run(
                [str(path), "-version"], stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", timeout=12,
                creationflags=CREATE_NO_WINDOW)
            return res.returncode == 0
        except Exception:
            return False

    def _resolve_ffmpeg(self, provided: str | Path | None) -> str:
        candidates: list[str] = []
        if provided:
            candidates.append(str(provided))
        if os.environ.get("FFMPEG_PATH"):
            candidates.append(os.environ["FFMPEG_PATH"])
        found = shutil.which("ffmpeg")
        if found:
            candidates.append(found)
        candidates += [
            str(Path(__file__).resolve().parent / "ffmpeg.exe"),
            str(Path(__file__).resolve().parent / "ffmpeg"),
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            str(Path(os.environ.get("LOCALAPPDATA", "")) /
                "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"),
        ]
        try:  # optional bundled build used by imageio-ffmpeg
            import imageio_ffmpeg  # type: ignore
            candidates.append(imageio_ffmpeg.get_ffmpeg_exe())
        except Exception:
            pass
        seen: set[str] = set()
        for candidate in candidates:
            try:
                path = Path(candidate)
                key = os.path.normcase(str(path))
                if key in seen or not path.is_file():
                    continue
                seen.add(key)
                if self._verify_ffmpeg(path):
                    return str(path)
            except Exception:
                continue
        raise MediaConversionError(
            "FFmpeg was not found.\n\n"
            "Install FFmpeg and put ffmpeg.exe on PATH, or set the FFMPEG_PATH "
            "environment variable.  https://ffmpeg.org/")

    def _resolve_ffprobe(self, provided: str | Path | None) -> str | None:
        candidates: list[str] = []
        if provided:
            candidates.append(str(provided))
        if os.environ.get("FFPROBE_PATH"):
            candidates.append(os.environ["FFPROBE_PATH"])
        sibling = Path(self.ffmpeg).with_name("ffprobe.exe")
        candidates.append(str(sibling))
        found = shutil.which("ffprobe")
        if found:
            candidates.append(found)
        for candidate in candidates:
            try:
                path = Path(candidate)
                if path.is_file():
                    return str(path)
            except Exception:
                pass
        return None

    def _has_encoder(self, name: str) -> bool:
        if self._encoders is None:
            encoders: set[str] = set()
            try:
                res = subprocess.run(
                    [self.ffmpeg, "-encoders"], stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", timeout=15,
                    creationflags=CREATE_NO_WINDOW)
                for line in (res.stdout or "").splitlines():
                    parts = line.split()
                    if len(parts) >= 2 and len(parts[0]) >= 3:
                        encoders.add(parts[1])
            except Exception:
                LOG.exception("Could not list FFmpeg encoders")
            self._encoders = encoders
        return name in self._encoders

    # ------------------------------------------------------------------ #
    #  Validation / paths
    # ------------------------------------------------------------------ #
    @staticmethod
    def normalize_format(output_format: str) -> str:
        fmt = str(output_format or "").strip().lower().lstrip(".")
        if fmt not in SUPPORTED_OUTPUT_FORMATS:
            raise MediaValidationError(
                f"Unsupported output format: {output_format!r}. "
                f"Supported: {', '.join(sorted(SUPPORTED_OUTPUT_FORMATS))}.")
        return fmt

    @staticmethod
    def default_output_path(input_path: str | Path, output_format: str) -> Path:
        src = Path(input_path)
        fmt = MediaConverter.normalize_format(output_format)
        return src.with_name(f"{src.stem}_converted.{fmt}")

    def validate(self, input_path: str | Path, output_format: str,
                 output_path: str | Path | None = None,
                 overwrite: bool = False) -> tuple[Path, str, Path]:
        src = Path(input_path)
        if not src.exists():
            raise MediaValidationError(f"Input file does not exist: {src}")
        if not src.is_file():
            raise MediaValidationError(f"Input is not a file: {src}")
        if src.suffix.lower() not in VIDEO_INPUT_EXTS:
            raise MediaValidationError(
                f"Unsupported input format: {src.suffix or '(no extension)'}. "
                f"Supported: {', '.join(sorted(VIDEO_INPUT_EXTS))}.")
        fmt = self.normalize_format(output_format)
        out = Path(output_path) if output_path else self.default_output_path(src, fmt)
        if out.suffix.lower() != f".{fmt}":
            raise MediaValidationError(
                f"Output extension {out.suffix!r} does not match requested "
                f"format {fmt!r} (expected .{fmt}).")
        try:
            if out.resolve() == src.resolve():
                raise MediaValidationError("Output would overwrite the input file.")
        except OSError:
            pass
        if out.exists() and not overwrite:
            raise MediaValidationError(f"Output file already exists: {out}")
        if not out.parent.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
        return src, fmt, out

    # ------------------------------------------------------------------ #
    #  Public conversion API
    # ------------------------------------------------------------------ #
    def convert(self, input_path: str | Path, output_format: str,
                output_path: str | Path | None = None, *,
                overwrite: bool = False,
                callbacks: ConversionCallbacks | None = None,
                cancel_event: threading.Event | None = None) -> ConversionResult:
        callbacks = callbacks or ConversionCallbacks()
        out: Path | None = None
        started = time.monotonic()
        try:
            src, fmt, out = self.validate(input_path, output_format, output_path,
                                          overwrite=overwrite)
            if overwrite and out.exists():
                out.unlink()
            self._callback(callbacks.on_start, src, fmt)
            duration = self._probe_duration(src)
            if fmt in AUDIO_OUTPUT_FORMATS:
                self._encode_audio(src, out, fmt, duration, callbacks, cancel_event)
                method = "audio"
            elif fmt == "gif":
                self._reencode(src, out, fmt, duration, callbacks, cancel_event)
                method = "reencode"
            else:
                if self._try_remux(src, out, fmt, duration, callbacks, cancel_event):
                    method = "remux"
                else:
                    self._reencode(src, out, fmt, duration, callbacks, cancel_event)
                    method = "reencode"
            if not out.exists() or out.stat().st_size == 0:
                raise MediaConversionError("FFmpeg finished without creating a valid output file.")
            result = ConversionResult(
                input=src, output=out, output_format=fmt, method=method,
                duration=duration, size=out.stat().st_size,
                elapsed=time.monotonic() - started)
            self._callback(callbacks.on_success, result)
            return result
        except Exception as exc:  # noqa: BLE001
            if out is not None:
                try:
                    out.unlink(missing_ok=True)
                except Exception:
                    pass
            self._callback(callbacks.on_error, exc)
            if isinstance(exc, (MediaConversionError, MediaValidationError)):
                raise
            raise MediaConversionError(str(exc)) from exc

    def convert_async(self, input_path: str | Path, output_format: str,
                      output_path: str | Path | None = None, *,
                      overwrite: bool = False,
                      callbacks: ConversionCallbacks | None = None) -> ConversionHandle:
        return ConversionHandle(
            self, input_path, output_format, output_path, overwrite,
            callbacks or ConversionCallbacks()).start()

    # ------------------------------------------------------------------ #
    #  Encoding strategies
    # ------------------------------------------------------------------ #
    def _try_remux(self, src: Path, out: Path, fmt: str, duration: float | None,
                   callbacks: ConversionCallbacks,
                   cancel_event: threading.Event | None) -> bool:
        if fmt == "gif":
            return False
        cmd = self._base_cmd(src)
        cmd += ["-map", "0:v:0", "-map", "0:a:0?", "-c", "copy"]
        if fmt in ("mp4", "mov"):
            cmd += ["-movflags", "+faststart"]
        cmd += ["-progress", "pipe:1", "-nostats", str(out)]
        rc, err = self._run_ffmpeg(cmd, duration, callbacks, "Remuxing", cancel_event)
        if rc == 0 and out.exists() and out.stat().st_size > 0:
            return True
        LOG.info("Stream copy to %s failed (%s); falling back to re-encode: %s",
                 fmt, rc, self._tail(err, 300))
        try:
            out.unlink(missing_ok=True)
        except Exception:
            pass
        return False

    def _reencode(self, src: Path, out: Path, fmt: str, duration: float | None,
                  callbacks: ConversionCallbacks,
                  cancel_event: threading.Event | None) -> None:
        cmd = self._base_cmd(src)
        if fmt == "gif":
            cmd += [
                "-map", "0:v:0", "-an",
                "-vf", ("fps=12,scale=trunc(iw/2)*2:-2:flags=lanczos,"
                        "split[s0][s1];[s0]palettegen=max_colors=256[p];"
                        "[s1][p]paletteuse=dither=bayer"),
                "-loop", "0",
            ]
        else:
            cmd += ["-map", "0:v:0", "-map", "0:a:0?"]
            cmd += self._video_args(fmt)
        cmd += ["-progress", "pipe:1", "-nostats", str(out)]
        rc, err = self._run_ffmpeg(cmd, duration, callbacks, "Encoding", cancel_event)
        if rc != 0:
            raise MediaConversionError(
                f"FFmpeg re-encode failed ({self._tail(err, 600)})")

    def _encode_audio(self, src: Path, out: Path, fmt: str, duration: float | None,
                      callbacks: ConversionCallbacks,
                      cancel_event: threading.Event | None) -> None:
        cmd = self._base_cmd(src)
        cmd += ["-vn", "-map", "0:a:0"] + self._audio_args(fmt)
        cmd += ["-progress", "pipe:1", "-nostats", str(out)]
        rc, err = self._run_ffmpeg(cmd, duration, callbacks, "Extracting audio",
                                   cancel_event)
        if rc != 0:
            detail = self._tail(err, 600)
            if "matches no streams" in detail or "does not contain" in detail:
                raise MediaConversionError("This file has no audio track.")
            raise MediaConversionError(f"FFmpeg audio extraction failed ({detail})")

    def _video_args(self, fmt: str) -> list[str]:
        if fmt in ("mp4", "mov", "mkv", "avi"):
            if not self._has_encoder("libx264"):
                raise MediaConversionError(
                    "This FFmpeg build does not include the libx264 encoder.")
            args = ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p"]
            if fmt == "avi":
                if not self._has_encoder("libmp3lame"):
                    raise MediaConversionError(
                        "This FFmpeg build does not include the libmp3lame encoder "
                        "needed for AVI audio.")
                args += ["-c:a", "libmp3lame", "-b:a", "192k"]
            else:
                if not self._has_encoder("aac"):
                    raise MediaConversionError(
                        "This FFmpeg build does not include the AAC encoder.")
                args += ["-strict", "-2", "-c:a", "aac", "-b:a", "192k"]
            if fmt in ("mp4", "mov"):
                args += ["-movflags", "+faststart"]
            return args
        if fmt == "webm":
            video = "libvpx-vp9" if self._has_encoder("libvpx-vp9") else "libvpx"
            if not self._has_encoder(video):
                raise MediaConversionError(
                    "This FFmpeg build does not include a VP8/VP9 encoder for WEBM.")
            audio = "libopus" if self._has_encoder("libopus") else "libvorbis"
            if not self._has_encoder(audio):
                raise MediaConversionError(
                    "This FFmpeg build does not include an Opus/Vorbis encoder for WEBM.")
            return ["-c:v", video, "-crf", "32", "-b:v", "0",
                    "-c:a", audio, "-b:a", "128k"]
        raise MediaConversionError(f"No video encoder configured for {fmt!r}.")

    def _audio_args(self, fmt: str) -> list[str]:
        if fmt == "mp3":
            if not self._has_encoder("libmp3lame"):
                raise MediaConversionError(
                    "This FFmpeg build does not include the libmp3lame encoder.")
            return ["-c:a", "libmp3lame", "-b:a", "192k"]
        if fmt in ("aac", "m4a"):
            if not self._has_encoder("aac"):
                raise MediaConversionError(
                    "This FFmpeg build does not include the AAC encoder.")
            args = ["-strict", "-2", "-c:a", "aac", "-b:a", "192k"]
            if fmt == "m4a":
                args += ["-movflags", "+faststart"]
            return args
        if fmt == "wav":
            return ["-c:a", "pcm_s16le"]
        if fmt == "flac":
            return ["-c:a", "flac"]
        raise MediaConversionError(f"No audio encoder configured for {fmt!r}.")

    # ------------------------------------------------------------------ #
    #  FFmpeg process plumbing
    # ------------------------------------------------------------------ #
    def _base_cmd(self, src: Path) -> list[str]:
        return [self.ffmpeg, "-loglevel", "error", "-y", "-i", str(src)]

    def _probe_duration(self, src: Path) -> float | None:
        if not self.ffprobe:
            return None
        try:
            res = subprocess.run(
                [self.ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(src)],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, encoding="utf-8",
                errors="replace", timeout=20, creationflags=CREATE_NO_WINDOW)
            value = (res.stdout or "").strip().splitlines()[0]
            return float(value)
        except Exception:
            return None

    def _run_ffmpeg(self, cmd: list[str], duration: float | None,
                    callbacks: ConversionCallbacks, phase: str,
                    cancel_event: threading.Event | None) -> tuple[int, str]:
        self._callback(callbacks.on_progress, 0.0, phase)
        proc = subprocess.Popen(
            cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8",
            errors="replace", bufsize=1, creationflags=CREATE_NO_WINDOW)
        out_lines: list[str] = []
        err_lines: list[str] = []
        last_pct = [-1]

        def reader(pipe, sink, progress: bool):
            try:
                for line in iter(pipe.readline, ""):
                    sink.append(line)
                    if progress and duration and duration > 0:
                        match = re.search(r"out_time_(?:us|ms)=(\d+)", line)
                        if match:
                            pct = min(99.0, max(0.0,
                                int(match.group(1)) / (duration * 1_000_000) * 100.0))
                            rounded = int(pct)
                            if rounded != last_pct[0]:
                                last_pct[0] = rounded
                                self._callback(callbacks.on_progress, pct,
                                               f"{phase} {rounded}%")
            except Exception:
                pass
            finally:
                try:
                    pipe.close()
                except Exception:
                    pass

        t_out = threading.Thread(target=reader, args=(proc.stdout, out_lines, True),
                                 daemon=True)
        t_err = threading.Thread(target=reader, args=(proc.stderr, err_lines, False),
                                 daemon=True)
        t_out.start()
        t_err.start()
        try:
            while True:
                rc = proc.poll()
                if rc is not None:
                    break
                if cancel_event is not None and cancel_event.is_set():
                    self._kill_tree(proc)
                    try:
                        proc.wait(timeout=8)
                    except Exception:
                        pass
                    raise MediaCancelled("Conversion cancelled.")
                time.sleep(0.08)
        finally:
            t_out.join(2)
            t_err.join(2)
        if cancel_event is not None and cancel_event.is_set():
            raise MediaCancelled("Conversion cancelled.")
        return int(rc), "".join(err_lines) + "".join(out_lines)

    @staticmethod
    def _kill_tree(proc: subprocess.Popen) -> None:
        if proc.poll() is not None:
            return
        try:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW,
                           timeout=8)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    @staticmethod
    def _tail(text: str, limit: int = 600) -> str:
        compact = " ".join((text or "").split())
        return compact[-limit:]

    @staticmethod
    def _callback(callback, *args) -> None:
        if callback is None:
            return
        try:
            callback(*args)
        except Exception:
            LOG.exception("Media conversion callback failed")
