from __future__ import annotations
from abc import ABC, abstractmethod
from io import BufferedReader


class ISerializable(ABC):
    @abstractmethod
    def read(self, reader: StreamReader) -> ISerializable:
        raise NotImplementedError

    # @abstractmethod
    # def write(self, writer: StreamWriter) -> ISerializable:
    #     raise NotImplementedError


class StreamReader:
    def __init__(self, stream: BufferedReader):
        self.stream = stream

    def read_object(self, ObjectClass: type[ISerializable]):
        return ObjectClass().read(self)

    def read_bytes(self, size: int):
        return self.stream.read(size)

    def read_int16(self):
        return int.from_bytes(self.stream.read(2), 'little')

    def read_int32(self):
        return int.from_bytes(self.stream.read(4), 'little')

    def read_str(self):
        if (length := self.read_int32()) == 0:
            return None
        return self.read_bytes(length).decode('utf-8')

    def read_uuid(self):
        return str(self.read_bytes(16))


class StreamWriter:
    def __init__(self, stream: BufferedReader):
        self.stream = stream

    def write_object(self, ObjectClass: type[ISerializable]):
        return ObjectClass().write(self)


class GvasProperty:
    pass


class CustomFormatEntry(ISerializable):
    def __init__(self):
        self.id: str
        self.value: int

    def read(self, reader: StreamReader) -> CustomFormatEntry:
        self.id = reader.read_uuid()
        self.value = reader.read_int32()
        return self


class CustomFormat(ISerializable):
    def __init__(self):
        self.version: int
        self.count: int
        self.entries: list[CustomFormatEntry]

    def read(self, reader: StreamReader):
        self.version = reader.read_int32()
        self.entries = [reader.read_object(CustomFormatEntry)
                        for _ in range(reader.read_int32())]


class EngineVersion(ISerializable):
    def __init__(self):
        self.major: int
        self.minor: int
        self.patch: int
        self.build: int
        self.build_id: str

    def read(self, reader: StreamReader) -> EngineVersion:
        self.major = reader.read_int16()
        self.minor = reader.read_int16()
        self.patch = reader.read_int16()
        self.build = reader.read_int32()
        self.build_id = reader.read_str()
        return self


class GvasHeader(ISerializable):
    def __init__(self):
        self.format: str
        self.save_game_version: int
        self.package_version: int
        self.engine_version: EngineVersion
        self.custom_format: CustomFormat

    def read(self, reader: StreamReader) -> GvasHeader:
        self.format = reader.read_bytes(4).decode('utf-8')
        self.save_game_version = reader.read_int32()
        self.package_version = reader.read_int32()
        self.engine_version = reader.read_object(EngineVersion)
        self.custom_format = reader.read_object(CustomFormat)
        return self


class Gvas(ISerializable):
    def __init__(self):
        self.header: GvasHeader

    def read(self, reader: StreamReader) -> Gvas:
        self.header = reader.read_object(GvasHeader)
        return self


if __name__ == '__main__':
    f = open('samples/04. tooth fall/Psychonauts2Save_0.sav', 'rb')
    reader = StreamReader(f)
    gvas = Gvas().read(reader)
