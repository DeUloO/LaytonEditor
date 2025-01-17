import io
import os
import re

import ndspy.rom
from ndspy.fnt import *

from formats.binary import *
from .compression import *


class Archive:
    """
    Abstract interface representing a file archive.
    """
    files: List[bytes] = []
    """List of the data contained in the files."""
    opened_files: list = []
    """List of the currently opened files."""

    def open(self, file: Union[AnyStr, int], mode: str = "rb") -> Union[io.BytesIO, io.TextIOWrapper]:
        pass

    def add_file(self, file: str) -> Optional[int]:
        """
        Adds a file at the specified path.

        Parameters
        ----------
        file : str
            The path where the file should be created.

        Returns
        -------
        int
            The id of the created file.
        """
        pass

    def remove_file(self, file: str):
        """
        Removes the file at the specified path.

        Parameters
        ----------
        file : str
            Path of the file which should be removed.
        """
        pass

    def rename_file(self, path: str, new_filename: str):
        """
        Renames the file at the specified path to the specified file name.

        Parameters
        ----------
        path : str
            Path of the file which should be renamed.
        new_filename : str
            New filename for the file.
        """
        pass


class RomFile(io.BytesIO):
    """
    Wrapper as io.BytesIO for a file in a ROM.
    """
    def __init__(self, archive, index: int, operation: str = "w"):
        if operation not in ["r", "w", "a"]:
            raise NotImplementedError(f"operation: {operation}")
        self.archive = archive
        self.id = index
        self.opp = operation
        if self not in self.archive.opened_files:
            self.archive.opened_files.append(self)
        super().__init__(self.archive.files[index] if operation in ["r", "a"] else b"")
        if operation == "a":
            self.read()

    def writable(self) -> bool:
        return self.opp in ["w", "a"]

    def close(self):
        self.flush()
        super().close()
        if self in self.archive.opened_files:
            self.archive.opened_files.remove(self)

    def fileno(self) -> int:
        return self.id

    def flush(self):
        if not self.closed:
            if self.opp != "r":
                self.archive.files[self.id] = self.getvalue()
            super().flush()

    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, *args):
        self.close()
        super().__exit__(*args)

    def __del__(self):
        self.close()


class CompressedIOWrapper(io.BytesIO):
    """
    Wrapper for a compressed file.
    """
    def __init__(self, stream, double_typed: Optional[bool] = None):
        """
        Parameters
        ----------
        stream : io.BytesIO
            Stream to use for internal data.
        double_typed : bool
            Whether the file has its compression type specified twice.
        """
        self._stream = stream

        current, self.double_typed = decompress(stream.read(), double_typed)

        super().__init__(current)

    def close(self):
        self.flush()
        super().close()
        self._stream.close()

    def flush(self):
        if self._stream.writable():
            self._stream.truncate(0)
            self._stream.seek(0)
            self._stream.write(compress(self.getvalue(), double_typed=self.double_typed))
        super().flush()
        self._stream.flush()

    def __enter__(self):
        super().__enter__()
        return self


class NintendoDSRom(ndspy.rom.NintendoDSRom, Archive):
    """
    Archive wrapping around ndspy.rom.NintendoDSRom
    """
    opened_files: List[RomFile]
    _loaded_archives: dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._opened_files = []
        """List of currently opened files."""
        self._loaded_archives: Dict[str, PlzArchive] = {}
        """List of currently loaded archives."""

        self._get_archive_call = False

    def get_archive(self, path):
        """
        Gets the plz archive from the specified path. An archive should not be opened in any other way.

        Parameters
        ----------
        path : str
            Path of the plz archive.

        Returns
        -------
        PlzArchive
            The PLZ archive as a PlzArchive object.
        """
        if path not in self._loaded_archives:
            self._get_archive_call = True
            self._loaded_archives[path] = PlzArchive(path, rom=self)
            self._get_archive_call = False
        return self._loaded_archives[path]

    def save(self, *args, **kwargs):
        # Save all archives before saving the ROM.
        self._get_archive_call = True
        for arch in self._loaded_archives:
            self._loaded_archives[arch].save()
        self._get_archive_call = False
        return super(NintendoDSRom, self).save(*args, **kwargs)

    # TODO: Unify archive opening and make sure archive are opened only once
    def open(self, file: Union[AnyStr, int], mode: str = "rb") -> Union[io.BytesIO, io.TextIOWrapper]:
        """
        Open the corresponding file in the ROM.

        Parameters
        ----------
        file : str | int
            The path or the id of the file.
        mode : str
            The mode for opening the file ('r', 'w', 'a' and the options 'b', '+')

        Returns
        -------
        RomFile | io.TextIOWrapper
            The opened rom file.
        """

        match = re.findall(r"^([rwa])(b?)(\+?)$", mode)
        if not match:
            raise ValueError(f"invalid mode: '{mode}'")
        create = False
        text = True
        if match:
            if match[0][1] == "b":
                text = False
            if match[0][2] == "+":
                create = True

        if isinstance(file, int):
            fileid = file
            file = self.filenames.filenameOf(file)
        else:
            fileid = self.filenames.idOf(file)
            if not fileid and create:
                fileid = self.add_file(file)
                if not fileid:
                    raise FileNotFoundError(f"file '{file}' could not be opened nor created")
            if not fileid:
                raise FileNotFoundError(f"file '{file}' could not be opened")

        if file.lower().endswith(".plz") and not self._get_archive_call:
            # Alert on the log of this action.
            logging.warning("PLZ archive not opened from get_archive!", stack_info=True)

        rom_file = RomFile(self, fileid, match[0][0])
        if text:
            return io.TextIOWrapper(rom_file)
        return rom_file

    def add_file(self, file: str) -> Optional[int]:
        folder_name, filename = os.path.split(file)
        folder_add = self.filenames[folder_name]
        new_file_id = folder_add.firstID + len(folder_add.files)

        # Insert our new file into this ID
        self.files.insert(new_file_id, b"")

        # Add our file to the folder
        folder_add.files.append(filename)

        # Change the firstID of all the folders after our base folder.
        def increment_first_index_if_needed(new_id, root: Folder):
            if root.firstID >= new_id and root != folder_add:
                root.firstID += 1

            for fd in root.folders:
                increment_first_index_if_needed(new_id, fd[1])

        increment_first_index_if_needed(new_file_id, self.filenames)

        # increment the id of loaded files after our base id
        for fp in self._opened_files:
            if fp.id > new_file_id:
                fp.id += 1

            if fp.id == new_file_id:
                fp.close()

        return new_file_id

    def remove_file(self, file: str):
        folder_name, filename = os.path.split(file)
        folder: Folder = self.filenames[folder_name]
        fileid = self.filenames.idOf(file)
        folder.files.remove(filename)
        del self.files[fileid]

        def decrement_first_index_if_needed(removed_id, root: Folder):
            if root.firstID > removed_id:
                root.firstID -= 1

            for fd in root.folders:
                decrement_first_index_if_needed(removed_id, fd[1])

        decrement_first_index_if_needed(fileid, self.filenames)
        for fp in self._opened_files:
            if fp.id > fileid:
                fp.id -= 1

            if fp.id == fileid:
                fp.close()

    def rename_file(self, path: str, new_filename: str):
        folder_name, filename = os.path.split(path)
        folder: Folder = self.filenames[folder_name]
        index = folder.files.index(filename)
        folder.files[index] = new_filename

    def move_file(self, old_path, new_path):
        """
        Moves the specified file from old_path to new_path.

        Parameters
        ----------
        old_path : str
            The old path of the file.
        new_path : str
            The new path of the file.
        """

        # TODO: What happens with archives?

        with self.open(old_path, "rb") as f:
            data = f.read()
        self.remove_file(old_path)
        with self.open(new_path, "wb+") as f:
            f.write(data)

    # TODO: Docstrings for folder methods.

    @staticmethod
    def folder_split(path) -> List[str]:
        return [x for x in path.split("/") if x]

    def folder_get_parent(self, path) -> Folder:
        *basedirs, subdir = self.folder_split(path)
        if basedirs:
            base_path = "/".join(basedirs) + "/"
            return self.filenames[base_path]
        else:  # The folder is located at the root.
            return self.filenames

    def add_folder(self, path):
        parent = self.folder_get_parent(path)
        new_folder = Folder(firstID=len(self.files))
        parent.folders.append((self.folder_split(path)[-1], new_folder))

    def remove_folder(self, path):
        folder = self.filenames[path]
        if not folder:
            raise Exception(f"Directory {path} does not exist.")
        if folder.files or folder.folders:
            raise Exception(f"Directory {path} not empty.")

        parent = self.folder_get_parent(path)

        parent.folders.remove((self.folder_split(path)[-1], folder))

    def rename_folder(self, old_path, new_path):
        folder = self.filenames[old_path]

        # get parents
        old_parent = self.folder_get_parent(old_path)
        new_parent = self.folder_get_parent(new_path)

        # generate folder items.
        old_folder_item = (self.folder_split(old_path)[-1], folder)
        new_folder_item = (self.folder_split(new_path)[-1], folder)

        if old_parent != new_parent:
            old_parent.folders.remove(old_folder_item)
            new_parent.folders.append(new_folder_item)
        else:  # same parent, keep the folder index
            index = old_parent.folders.index(old_folder_item)
            new_parent.folders[index] = new_folder_item


class FileFormat:
    """
    An abstract class representing a file format on a Nintendo DS rom.

    Derived classes implement reading and saving methods for their specific file format.
    """

    _compressed_default = 0
    """
    The compression on this file format.
    
    - 0 - No compression
    - 1 - Compressed file
    - 2 - Double typed compressed file
    """

    _last_compressed = _compressed_default
    """The compression last used when opening the file."""
    _last_filename: Optional[str] = None
    """The last filename used when opening the file."""
    _last_rom: Archive = None
    """The last rom used when opening the file."""

    def __init__(self, filename: str = None, file=None, compressed=None, rom: NintendoDSRom = None, **kwargs):
        if filename is not None:
            self._last_filename = filename
            self._last_rom = rom
            file = rom.open(filename, "rb") if rom else open(filename, "rb")

        if compressed is None:
            compressed = self._compressed_default
        if compressed:
            file = CompressedIOWrapper(file, double_typed=(compressed == 2))
        self._last_compressed = compressed

        if file is not None:
            self.read_stream(file)

        for kwarg in kwargs:
            self.__dict__[kwarg] = kwargs[kwarg]

        if filename is not None:
            file.close()  # we opened the file here, we close the file here

    def save(self, filename=None, file=None, compressed=None, rom: NintendoDSRom = None):
        should_close = False
        if not file:
            should_close = True
            if filename:
                file = rom.open(filename, "wb+") if rom else open(filename, "wb+")
                self._last_filename = filename
                self._last_rom = rom
            elif self._last_filename:
                if self._last_rom:
                    file = self._last_rom.open(self._last_filename, "wb+")
                else:
                    open(self._last_filename, "wb+")

        if compressed is None:
            compressed = self._last_compressed
        if compressed:
            file = CompressedIOWrapper(file, double_typed=(compressed == 2))

        self.write_stream(file)

        # Close file if we opened it here
        if should_close:
            file.close()

    def read_stream(self, stream):
        """Abstract function used for reading the file data."""
        pass

    def write_stream(self, stream):
        """Abstract function used for writing the file data."""
        pass


class PlzArchive(Archive, FileFormat):
    """
    A Plz Archive, a file containing other files within, so that they are compressed.
    """
    _compressed_default = 1

    filenames: List[str] = []
    """List of the names of the files present in the plz archive."""
    files: List[bytes] = []
    """List of the data of the files present in the plz archive."""

    def read_stream(self, stream):
        if isinstance(stream, BinaryReader):
            rdr = stream
        else:
            rdr = BinaryReader(stream)

        self.filenames = []
        self.files = []

        header_size = rdr.read_uint32()
        archive_file_size = rdr.read_uint32()
        assert rdr.read(4) == b"PCK2"
        rdr.seek(header_size)

        while rdr.c < archive_file_size:
            start_pos = rdr.c

            file_header_size = rdr.read_uint32()
            file_total_size = rdr.read_uint32()
            rdr.seek(4, io.SEEK_CUR)
            file_size = rdr.read_uint32()

            filename = rdr.read_string(encoding="shift-jis")

            rdr.seek(start_pos + file_header_size)
            file = rdr.read(file_size)
            rdr.seek(start_pos + file_total_size)

            self.filenames.append(filename)
            self.files.append(file)

    def write_stream(self, stream):
        if isinstance(stream, BinaryWriter):
            wtr = stream
        else:
            wtr = BinaryWriter(stream)

        wtr.write_uint32(16)
        wtr.write_uint32(0)  # placeholder file_size
        wtr.write(b"PCK2")
        wtr.write_uint32(0)

        for i in range(len(self.files)):
            header_size = 16 + len(self.filenames[i]) + 1
            header_size += 4 - header_size % 4

            total_size = header_size + len(self.files[i])
            total_size += 4 - total_size % 4
            c = wtr.c
            wtr.write_uint32(header_size)
            wtr.write_uint32(total_size)
            wtr.write_uint32(0)
            wtr.write_uint32(len(self.files[i]))

            wtr.write_string(self.filenames[i])
            wtr.seek(c + header_size)
            wtr.write(self.files[i])
            # Seek while adding bytes
            while wtr.c != c + total_size:
                wtr.write_uint8(0)

        file_size = len(wtr)
        wtr.seek(4)
        wtr.write_uint32(file_size)

    def open(self, file: Union[AnyStr, int], mode: str = "rb") -> Union[io.BytesIO, io.TextIOWrapper]:
        match = re.findall(r"^([rwa])(b?)(\+?)$", mode)
        if not match:
            raise ValueError(f"invalid mode: '{mode}'")
        create = False
        text = True
        if match:
            if match[0][1] == "b":
                text = False
            if match[0][2] == "+":
                create = True

        if isinstance(file, int):
            fileid = file
        else:
            try:
                fileid = self.filenames.index(file)
            except ValueError:
                fileid = None
            if fileid is None and create:
                fileid = self.add_file(file)
                if not fileid:
                    raise FileNotFoundError(f"file '{file}' could not be opened nor created")
            if fileid is None:
                raise FileNotFoundError(f"file '{file}' could not be opened")

        rom_file = RomFile(self, fileid, match[0][0])
        if text:
            return io.TextIOWrapper(rom_file)
        return rom_file

    def add_file(self, filename: str):
        new_file_id = len(self.files)
        self.files.append(b"")
        self.filenames.append(filename)

        return new_file_id

    def remove_file(self, filename: str):
        if filename not in self.filenames:
            return
        index = self.filenames.index(filename)
        self.files.pop(index)
        self.filenames.pop(index)

    def rename_file(self, old_filename, new_filename):
        if old_filename not in self.filenames:
            return
        index = self.filenames.index(old_filename)
        self.filenames[index] = new_filename
