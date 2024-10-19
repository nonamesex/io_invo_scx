import struct
from io import BufferedReader

"""
Custom implementation of BinaryReader class, similar to C# version
Supports both Big and Little endianness and some non-standard types, like:
float16, GUID, sized string, null-terminated string
"""
class BinaryReader:
    def __init__(self, file):
        self.__stream__: BufferedReader = open(file, "rb")

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.__stream__.close()

    def seek(self, size = 0, whence = 1):
        return self.__stream__.seek(size, whence)

    def tell (self):
        return self.__stream__.tell()

    # Common types
    def ReadBoolean(self, endian = "<"):
        ret: bool = struct.unpack(f"{endian}?", self.__stream__.read(1))[0]
        return ret

    def ReadChar(self, endian = "<"):
        ret: str = struct.unpack(f"{endian}c", self.__stream__.read(1))[0]
        return ret

    # Floating-point types
    def ReadDouble(self, endian = "<"):
        ret: float = struct.unpack(f"{endian}d", self.__stream__.read(8))[0]
        return ret

    def ReadHalf(self, endian = "<"):
        ret: float = struct.unpack(f"{endian}e", self.__stream__.read(2))[0]
        return ret

    def ReadSingle(self, endian = "<"):
        ret: float = struct.unpack(f"{endian}f", self.__stream__.read(4))[0]
        return ret

    # Signed types
    def ReadSByte(self, endian = "<"):
        ret: int = struct.unpack(f"{endian}b", self.__stream__.read(1))[0]
        return ret

    def ReadInt16(self, endian = "<"):
        ret: int = struct.unpack(f"{endian}h", self.__stream__.read(2))[0]
        return ret

    def ReadInt32(self, endian = "<"):
        ret: int = struct.unpack(f"{endian}i", self.__stream__.read(4))[0]
        return ret

    def ReadInt64(self, endian = "<"):
        ret: int = struct.unpack(f"{endian}q", self.__stream__.read(8))[0]
        return ret

    # Unsigned types
    def ReadByte(self, endian = "<"):
        ret: int = struct.unpack(f"{endian}B", self.__stream__.read(1))[0]
        return ret

    def ReadUInt16(self, endian = "<"):
        ret: int = struct.unpack(f"{endian}H", self.__stream__.read(2))[0]
        return ret

    def ReadUInt32(self, endian = "<"):
        ret: int = struct.unpack(f"{endian}I", self.__stream__.read(4))[0]
        return ret

    def ReadUInt64(self, endian = "<"):
        ret: int = struct.unpack(f"{endian}Q", self.__stream__.read(8))[0]
        return ret

    # Custom types
    def ReadGuid(self, endian = "<"):
        ret: str = struct.unpack(f"{endian}16B", self.__stream__.read(16))[0]
        return ret

    def ReadSizedString(self, size, endian = "<"):
        ret: str = struct.unpack(f"{endian}{size}s", self.__stream__.read(size))[0].decode("utf-8")
        return ret

    def ReadNullTerminatedSizedString(self, size, endian = "<"):
        ret = bytearray()
        for i in range(size):
            c = bytearray(struct.unpack(f"{endian}B", self.__stream__.read(1)))
            if c != b"\\x00":
                ret += c
        return ret.decode("utf8")

    def ReadNullTerminatedString(self, endian = "<"):
        while True:
            ret = bytearray()
            c = bytearray(struct.unpack(f"{endian}B", self.__stream__.read(1)))
            if c == b"\\x00":
                return ret.decode("utf8")
            ret += c

    def ReadBytes(self, size: int):
        return self.__stream__.read(size)
