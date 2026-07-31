import hashlib
import os
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import Column, MetaData, String, Table, create_engine, select
from sqlalchemy.exc import IntegrityError

import sctmgtool

APP_REVISION = sctmgtool.__version__
CHARTS_REVISION = 3
CACHE_REVISION = f"{APP_REVISION}/{CHARTS_REVISION}"


class ImageCache:
    def __init__(self, cache_dir: Path, database_url: str):
        self.cache_dir = cache_dir
        self.image_dir = cache_dir / APP_REVISION / str(CHARTS_REVISION)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)
        metadata = MetaData()
        self.entries = Table(
            "image_cache",
            metadata,
            Column("result_key", String(512), primary_key=True),
            Column("file_name", String(80), nullable=False),
        )
        metadata.create_all(self.engine)
        self.lock = threading.Lock()

    @staticmethod
    def _database_key(result_key: str) -> str:
        return f"{CACHE_REVISION}:{result_key}"

    def _file_name(self, result_key: str) -> str:
        cache_key = self._database_key(result_key)
        return f"{hashlib.sha256(cache_key.encode('utf-8')).hexdigest()}.webp"

    def _find_file(self, result_key: str) -> Path | None:
        with self.engine.connect() as connection:
            file_name = connection.execute(
                select(self.entries.c.file_name).where(self.entries.c.result_key == self._database_key(result_key))
            ).scalar_one_or_none()

        if file_name is None:
            return None

        image_path = self.image_dir / file_name
        return image_path if image_path.is_file() else None

    def _register_file(self, result_key: str, file_name: str) -> None:
        try:
            with self.engine.begin() as connection:
                connection.execute(self.entries.insert().values(result_key=self._database_key(result_key), file_name=file_name))
        except IntegrityError:
            pass

    def get_or_create(self, result_key: str, generate_image: Callable[[], bytes]) -> Path:
        image_path = self._find_file(result_key)
        if image_path is not None:
            return image_path

        with self.lock:
            image_path = self._find_file(result_key)
            if image_path is not None:
                return image_path

            file_name = self._file_name(result_key)
            image_path = self.image_dir / file_name
            with tempfile.NamedTemporaryFile(mode="wb", dir=self.image_dir, delete=False) as temporary_file:
                temporary_file.write(generate_image())
                temporary_path = Path(temporary_file.name)

            os.replace(temporary_path, image_path)
            self._register_file(result_key, file_name)
            return image_path
