class FileData:
    def __init__(self, *, name: str, file_path: str, size: int, hash: str):
        self.name = name
        self.file_path = file_path
        self.size = size
        self.hash = hash
