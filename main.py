from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BufferedReader
from uuid import UUID
from rich.pretty import pprint
import json


class ISerializable(ABC):

    def print(self):
        pprint(json.loads(json.dumps(self, default=lambda o: o.__dict__)))

    @abstractmethod
    def read(self, reader: BinaryReader):
        raise NotImplementedError

    # @abstractmethod
    def write(self, writer: BinaryWriter) -> ISerializable:
        raise NotImplementedError


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


@dataclass
class CustomFormatEntry(ISerializable):
    id: str = None
    value: int = None

    def read(self, reader: BinaryReader):
        self.id = reader.read_uuid()
        self.value = reader.read_int32()


@dataclass
class CustomFormat(ISerializable):
    version: int = None
    count: int = None
    entries: list[CustomFormatEntry] = None

    def read(self, reader: BinaryReader):
        self.version = reader.read_int32()
        self.entries = [reader.read_object(CustomFormatEntry)
                        for _ in range(reader.read_int32())]


@dataclass
class EngineVersion(ISerializable):
    major: int = None
    minor: int = None
    patch: int = None
    build: int = None
    build_id: str = None

    def read(self, reader: BinaryReader):
        self.major = reader.read_int16()
        self.minor = reader.read_int16()
        self.patch = reader.read_int16()
        self.build = reader.read_int32()
        self.build_id = reader.read_str()


@dataclass
class Gvas(ISerializable):
    format: str = None
    save_game_version: int = None
    package_version: int = None
    engine_version: EngineVersion = None
    custom_format: CustomFormat = None
    raw: str = None

    def read(self, reader: BinaryReader):
        self.format = reader.read_bytes(4).decode('utf-8')
        self.save_game_version = reader.read_int32()
        self.package_version = reader.read_int32()
        self.engine_version = reader.read_object(EngineVersion)
        self.custom_format = reader.read_object(CustomFormat)
        self.raw = reader.buffer.read().hex()


def obj_to_sav(source_object, sav_path: str):
    raise NotImplementedError


def sav_to_obj(sav_path: str):
    with open(sav_path, 'rb') as f:
        gvas = Gvas()
        gvas.read(BinaryReader(f))
    return gvas


def obj_to_json(source_object, json_path: str):
    with open(json_path, 'w') as f:
        f.write(json.dumps(source_object, default=lambda o: o.__dict__, indent=4))


def json_to_obj(json_path: str):
    with open(json_path, 'r') as f:
        json_file = f.read()
    return Gvas(**json.loads(json_file))


if __name__ == '__main__':
    sav_sample = 'samples/04. tooth fall/Psychonauts2Save_0.sav', 'rb'
    json_sample = 'samples/sample.json'

    o = json_to_obj(json_sample)
    o.print()
