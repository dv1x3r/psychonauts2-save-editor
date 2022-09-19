from io import BufferedReader


class StreamReader:
    def __init__(self, stream: BufferedReader):
        self.stream = stream

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


class GvasProperty:
    pass


class CustomFormat:
    def __init__(self):
        self.version: int
        self.data_count: int
        self.data_entries: list

    def read(self, reader: StreamReader):
        self.version = reader.read_int32()
        self.data_count = reader.read_int32()
        self.data_entries = []
        for i in range(self.data_count):
            self.data_entries.append(
                {
                    'id': reader.read_uuid(),
                    'value': reader.read_int32(),
                }
            )
        print(self.__dict__)


class EngineVersion:
    def __init__(self):
        self.major: int
        self.minor: int
        self.patch: int
        self.build: int
        self.build_id: str

    def read(self, reader: StreamReader):
        self.major = reader.read_int16()
        self.minor = reader.read_int16()
        self.patch = reader.read_int16()
        self.build = reader.read_int32()
        self.build_id = reader.read_str()
        return self


class GvasHeader:
    def __init__(self):
        self.format: str
        self.save_game_version: int
        self.package_version: int
        self.engine_version: EngineVersion
        self.custom_format: CustomFormat

    def read(self, reader: StreamReader):
        self.format = reader.read_bytes(4).decode('utf-8')
        self.save_game_version = reader.read_int32()
        self.package_version = reader.read_int32()
        self.engine_version = EngineVersion().read(reader)
        self.custom_format = CustomFormat().read(reader)
        return self


class Gvas:
    def __init__(self):
        self.header: GvasHeader

    def read(self, reader: StreamReader):
        self.header = GvasHeader().read(reader)
        return self


if __name__ == '__main__':
    f = open('samples/04. tooth fall/Psychonauts2Save_0.sav', 'rb')
    reader = StreamReader(f)
    gvas = Gvas().read(reader)
