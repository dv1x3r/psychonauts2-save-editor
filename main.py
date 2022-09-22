from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from dataclasses_json import dataclass_json
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

    @abstractmethod
    def write(self, writer: BinaryWriter):
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
        return int.from_bytes(self.read_bytes(2), 'little')

    def read_int32(self):
        return int.from_bytes(self.read_bytes(4), 'little')

    def read_int64(self):
        return int.from_bytes(self.read_bytes(8), 'little')

    def read_str(self):
        if (length := self.read_int32()) == 0:
            return None
        return self.read_bytes(length).decode('ascii')[:-1]

    def read_uuid(self):
        return str(UUID(bytes_le=self.read_bytes(16)))

    def read_terminator(self):
        terminator = self.read_bytes(1)
        if terminator != b'\x00':
            raise Exception(f'Terminator is {terminator}, but expected 0x00')


class BinaryWriter:

    def __init__(self, buffer: BufferedReader):
        self.buffer = buffer

    def write_object(self, instance: ISerializable):
        instance.write(self)

    def write_bytes(self, data: bytes):
        self.buffer.write(data)

    def write_int16(self, data: int):
        self.write_bytes(int.to_bytes(data, 2, 'little'))

    def write_int32(self, data: int):
        self.write_bytes(int.to_bytes(data, 4, 'little'))

    def write_int64(self, data: int):
        self.write_bytes(int.to_bytes(data, 8, 'little'))

    def write_str(self, data: str):
        if data is None:
            self.write_int32(0)
        else:
            self.write_int32(len(data) + 1)
            self.write_bytes(data.encode())
            self.write_bytes(b'\x00')

    def write_uuid(self, data: str):
        self.write_bytes(UUID(str(data)).bytes_le)

    def write_terminator(self):
        self.write_bytes(b'\x00')


@dataclass
class UEProperty(ISerializable):
    name: str = None
    type: str = None
    length: int = None
    value: any = None

    def read(self, reader: BinaryReader):
        self.name = reader.read_str()
        self.type = reader.read_str()
        self.length = reader.read_int64()
        self.value = getattr(self, f'read_{self.type}')(reader, self.length)

    def read_UInt32Property(self, reader: BinaryReader, length: int):
        reader.read_terminator()
        return reader.read_int32()

    def read_ArrayProperty(self, reader: BinaryReader, length: int):
        item_type = reader.read_str()
        reader.read_terminator()
        item_length = reader.read_int32()
        return getattr(self, f'read_{item_type}')(reader, item_length)

    def read_ByteProperty(self, reader: BinaryReader, length: int):
        return reader.read_bytes(length).hex()

    def read_MapProperty(self, reader: BinaryReader, length: int):
        raise NotImplementedError

    def write(self, writer: BinaryWriter):
        writer.write_str(self.name)
        writer.write_str(self.type)
        writer.write_int64(self.length)
        getattr(self, f'write_{self.type}')(writer, self.length)


@dataclass
class CustomFormatEntry(ISerializable):
    id: str = None
    value: int = None

    def read(self, reader: BinaryReader):
        self.id = reader.read_uuid()
        self.value = reader.read_int32()

    def write(self, writer: BinaryWriter):
        writer.write_uuid(self.id)
        writer.write_int32(self.value)


@dataclass
class CustomFormat(ISerializable):
    version: int = None
    entries: list[CustomFormatEntry] = None

    def read(self, reader: BinaryReader):
        self.version = reader.read_int32()
        self.entries = [reader.read_object(CustomFormatEntry)
                        for _ in range(reader.read_int32())]

    def write(self, writer: BinaryWriter):
        writer.write_int32(self.version)
        writer.write_int32(len(self.entries))
        for entry in self.entries:
            writer.write_object(entry)


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

    def write(self, writer: BinaryWriter):
        writer.write_int16(self.major)
        writer.write_int16(self.minor)
        writer.write_int16(self.patch)
        writer.write_int32(self.build)
        writer.write_str(self.build_id)


@dataclass_json
@dataclass
class Gvas(ISerializable):
    format: str = None
    save_game_version: int = None
    package_version: int = None
    engine_version: EngineVersion = None
    custom_format: CustomFormat = None
    save_game_type: str = None
    properties: list[UEProperty] = None
    raw: str = None

    def read(self, reader: BinaryReader):
        self.format = reader.read_bytes(4).decode('ascii')
        self.save_game_version = reader.read_int32()
        self.package_version = reader.read_int32()
        self.engine_version = reader.read_object(EngineVersion)
        self.custom_format = reader.read_object(CustomFormat)
        self.save_game_type = reader.read_str()
        self.properties = []
        self.properties.append(reader.read_object(UEProperty))
        self.properties.append(reader.read_object(UEProperty))
        # self.properties.append(reader.read_object(UEProperty))
        self.raw = reader.buffer.read().hex()

    def write(self, writer: BinaryWriter):
        writer.write_bytes(b'GVAS')
        writer.write_int32(self.save_game_version)
        writer.write_int32(self.package_version)
        writer.write_object(self.engine_version)
        writer.write_object(self.custom_format)
        writer.write_str(self.save_game_type)
        writer.write_bytes(bytes.fromhex(self.raw))


def sav_to_gvas(sav_path: str):
    with open(sav_path, 'rb') as f:
        gvas = Gvas()
        gvas.read(BinaryReader(f))
    return gvas


def gvas_to_sav(gvas: Gvas, sav_path: str):
    with open(sav_path, 'wb') as f:
        gvas.write(BinaryWriter(f))


def gvas_to_json(gvas: Gvas, json_path: str):
    with open(json_path, 'w') as f:
        f.write(gvas.to_json(indent=4))


def json_to_gvas(json_path: str):
    with open(json_path, 'r') as f:
        json_dump = f.read()
    return Gvas.from_json(json_dump)


if __name__ == '__main__':
    sav_original_path = 'samples/04. tooth fall/Psychonauts2Save_0.sav'
    sav_patched_path = 'samples/patched.sav'
    json_path = 'samples/sample.json'
    gvas_original = sav_to_gvas(sav_original_path)
    gvas_to_json(gvas_original, json_path)
    # gvas_patched = json_to_gvas(json_path)
    # gvas_to_sav(gvas_patched, sav_patched_path)
    # gvas_patched.print()
