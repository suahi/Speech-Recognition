from __future__ import annotations

from pathlib import Path


PE_MACHINE_AMD64 = 0x8664


class PeFormatError(ValueError):
    """Raised when the configured vendor SDK is not a 64-bit Windows DLL."""


def read_pe_machine(path: str | Path) -> int:
    dll_path = Path(path).resolve()
    try:
        with dll_path.open("rb") as handle:
            header = handle.read(64)
            if len(header) < 64 or header[:2] != b"MZ":
                raise PeFormatError(f"SDK 文件不是有效的 Windows DLL：{dll_path}")
            pe_offset = int.from_bytes(header[60:64], "little")
            handle.seek(pe_offset)
            pe_header = handle.read(6)
    except OSError as exc:
        raise PeFormatError(f"无法读取 SDK DLL：{dll_path}") from exc
    if len(pe_header) != 6 or pe_header[:4] != b"PE\x00\x00":
        raise PeFormatError(f"SDK 文件缺少有效 PE 头：{dll_path}")
    return int.from_bytes(pe_header[4:6], "little")


def require_x64_windows_dll(path: str | Path) -> None:
    machine = read_pe_machine(path)
    if machine != PE_MACHINE_AMD64:
        raise PeFormatError(
            f"SDK DLL 必须为 Windows x64 版本，当前 PE machine=0x{machine:04X}：{Path(path).resolve()}"
        )
