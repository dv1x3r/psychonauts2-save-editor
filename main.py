from __future__ import annotations
from abc import ABC, abstractmethod
from io import BufferedReader
from uuid import UUID
from rich.pretty import pprint
import json


class ISerializable(ABC):
    def print(self):
        pprint(self.to_dict())

    def to_dict(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))

    @abstractmethod
    def read(self, reader: BinaryReader):
        raise NotImplementedError

    # @abstractmethod
    # def write(self, writer: StreamWriter) -> ISerializable:
    #     raise NotImplementedError


class BinaryReader:
    def __init__(self, buffer: BufferedReader):
        self.buffer = buffer

    def read_object(self, ObjectClass: type[ISerializable]):
        instance = ObjectClass()
        instance.read(self)
        return instance

    def read_bytes(self, size: int):
        return self.buffer.read(size)

    def read_int16(self):
        return int.from_bytes(self.buffer.read(2), 'little')

    def read_int32(self):
        return int.from_bytes(self.buffer.read(4), 'little')

    def read_str(self):
        if (length := self.read_int32()) == 0:
            return None
        return self.read_bytes(length).decode('utf-8')[:-1]

    def read_uuid(self):
        return str(UUID(bytes_le=self.read_bytes(16)))


class BinaryWriter:
    def __init__(self, buffer: BufferedReader):
        self.buffer = buffer

    def write_object(self, ObjectClass: type[ISerializable]):
        return ObjectClass().write(self)


class GvasProperty:
    pass


class CustomFormatEntry(ISerializable):
    def __init__(self):
        self.id: str
        self.value: int

    def read(self, reader: BinaryReader):
        self.id = reader.read_uuid()
        self.value = reader.read_int32()


class CustomFormat(ISerializable):
    def __init__(self):
        self.version: int
        self.count: int
        self.entries: list[CustomFormatEntry]

    def read(self, reader: BinaryReader):
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

    def read(self, reader: BinaryReader):
        self.major = reader.read_int16()
        self.minor = reader.read_int16()
        self.patch = reader.read_int16()
        self.build = reader.read_int32()
        self.build_id = reader.read_str()


class Gvas(ISerializable):
    def __init__(self):
        self.format: str
        self.save_game_version: int
        self.package_version: int
        self.engine_version: EngineVersion
        self.custom_format: CustomFormat

    def read(self, reader: BinaryReader):
        self.format = reader.read_bytes(4).decode('utf-8')
        self.save_game_version = reader.read_int32()
        self.package_version = reader.read_int32()
        self.engine_version = reader.read_object(EngineVersion)
        self.custom_format = reader.read_object(CustomFormat)


if __name__ == '__main__':
    f = open('samples/04. tooth fall/Psychonauts2Save_0.sav', 'rb')
    reader = BinaryReader(f)
    gvas = Gvas()
    gvas.read(reader)
    gvas.print()
