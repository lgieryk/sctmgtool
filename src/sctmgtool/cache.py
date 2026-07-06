# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

import pickle
from multiprocessing import Process, Manager, Lock, Event, Value
from pathlib import Path
import hashlib
import logging
import sctmgtool


class Cache:
    MAJOR_REVISION = hashlib.sha256(sctmgtool.__version__.encode("utf-8")).hexdigest()
    FILENAME = "cache.pkl"

    def __init__(self, /, minor_revision: int, save_path: Path):
        manager = Manager()
        self.revision = (self.MAJOR_REVISION, minor_revision)
        self.save_file_path = save_path / Cache.FILENAME

        try:
            logging.info("Cache path: %s", self.save_file_path)
            with open(self.save_file_path, "rb") as file:
                rev, data = pickle.load(file)
                if rev == self.revision:
                    self.data = manager.dict(data)
                else:
                    logging.warning("Cache version error; starting a new one from scratch")
                    self.data = manager.dict()
        except (FileNotFoundError, AttributeError):
            logging.warning("Cache access error; starting a new one from scratch")
            self.data = manager.dict()

        self.lock = Lock()
        self.stop_event = Event()
        self.workers = []
        self.new_inserts = Value("i", 0)

    def start_worker_func(self, worker_func: callable, arguments=None):
        if arguments is None:
            worker = Process(target=worker_func)
        else:
            worker = Process(target=worker_func, args=arguments)
        worker.start()
        self.workers.append(worker)

    def stop_and_save(self):
        self.stop_event.set()

        for worker in self.workers:
            worker.join()

        if self.new_inserts.value == 0:
            return

        with self.lock:
            with open(self.save_file_path, "wb") as file:
                pickle.dump((self.revision, dict(self.data)), file)

    def __getitem__(self, obj):
        key = self.obj_to_key(obj)

        if key in self.data:
            return self.data[key]

        value = self.compute_func(obj)

        with self.lock:
            self.data.setdefault(key, value)

        with self.new_inserts.get_lock():
            self.new_inserts.value += 1

        return value

    def obj_to_key(self, obj):
        return obj

    def compute_func(self, _obj):
        raise NotImplementedError()
