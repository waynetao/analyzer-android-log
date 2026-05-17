import os
import zipfile
import tarfile
import shutil


class LogExtractor:
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = temp_dir
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

    def extract(self, file_path: str) -> str:
        if zipfile.is_zipfile(file_path):
            return self._extract_zip(file_path)
        elif tarfile.is_tarfile(file_path):
            return self._extract_tar(file_path)
        elif os.path.isdir(file_path):
            # 如果已经是目录，直接返回该目录
            return file_path
        else:
            # 单个文件，直接返回其所在目录
            return os.path.dirname(os.path.abspath(file_path))

    def _extract_zip(self, zip_path: str) -> str:
        extract_dir = os.path.join(
            self.temp_dir, os.path.splitext(os.path.basename(zip_path))[0]
        )
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        return extract_dir

    def _extract_tar(self, tar_path: str) -> str:
        extract_dir = os.path.join(
            self.temp_dir, os.path.splitext(os.path.basename(tar_path))[0]
        )
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        with tarfile.open(tar_path, "r:*") as tar_ref:
            tar_ref.extractall(extract_dir)
        return extract_dir

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
