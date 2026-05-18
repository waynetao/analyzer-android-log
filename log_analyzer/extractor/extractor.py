import os
import zipfile
import tarfile
import shutil
import logging

logger = logging.getLogger(__name__)


class LogExtractor:
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = temp_dir
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

    @staticmethod
    def _is_safe_path(member_path: str, extract_dir: str) -> bool:
        """验证解压路径是否安全，防止路径遍历攻击（Zip Slip / Tar Slip）"""
        abs_extract = os.path.abspath(extract_dir)
        abs_target = os.path.abspath(os.path.join(extract_dir, member_path))
        return abs_target.startswith(abs_extract + os.sep) or abs_target == abs_extract

    def extract(self, file_path: str) -> str:
        # 优先判断目录，避免 tarfile.is_tarfile 尝试 open() 目录导致 PermissionError
        if os.path.isdir(file_path):
            # 如果是目录，自动解压目录中的所有压缩包
            return self._extract_directory(file_path)
        elif zipfile.is_zipfile(file_path):
            return self._extract_zip(file_path)
        elif tarfile.is_tarfile(file_path):
            return self._extract_tar(file_path)
        else:
            # 单个文件，直接返回其所在目录
            return os.path.dirname(os.path.abspath(file_path))
    
    def _extract_directory(self, dir_path: str) -> str:
        """解压目录中的所有压缩包到临时目录"""
        extract_dir = os.path.join(self.temp_dir, "extracted_" + os.path.basename(dir_path))
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        
        # 查找并解压所有压缩包
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                if zipfile.is_zipfile(file_path):
                    with zipfile.ZipFile(file_path, "r") as zip_ref:
                        self._safe_extract_zip(zip_ref, extract_dir)
                    logger.info(f"  解压: {filename}")
                elif tarfile.is_tarfile(file_path):
                    with tarfile.open(file_path, "r:*") as tar_ref:
                        self._safe_extract_tar(tar_ref, extract_dir)
                    logger.info(f"  解压: {filename}")
                else:
                    # 非压缩文件直接复制
                    if os.path.isfile(file_path):
                        shutil.copy2(file_path, extract_dir)
            except (OSError, zipfile.BadZipFile, tarfile.TarError) as e:
                logger.warning(f"  跳过 {filename}: {e}")
        
        return extract_dir

    def _safe_extract_zip(self, zip_ref: zipfile.ZipFile, extract_dir: str):
        """安全解压 ZIP 文件，防止路径遍历"""
        for member in zip_ref.namelist():
            if not self._is_safe_path(member, extract_dir):
                logger.warning(f"  跳过不安全路径: {member}")
                continue
            zip_ref.extract(member, extract_dir)

    def _safe_extract_tar(self, tar_ref: tarfile.TarFile, extract_dir: str):
        """安全解压 TAR 文件，防止路径遍历"""
        for member in tar_ref.getmembers():
            if not self._is_safe_path(member.name, extract_dir):
                logger.warning(f"  跳过不安全路径: {member.name}")
                continue
            # 额外安全检查：跳过符号链接和特殊文件
            if member.issym() or member.islnk():
                logger.warning(f"  跳过符号链接: {member.name}")
                continue
            tar_ref.extract(member, extract_dir)

    def _extract_zip(self, zip_path: str) -> str:
        extract_dir = os.path.join(
            self.temp_dir, os.path.splitext(os.path.basename(zip_path))[0]
        )
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            self._safe_extract_zip(zip_ref, extract_dir)
        return extract_dir

    def _extract_tar(self, tar_path: str) -> str:
        extract_dir = os.path.join(
            self.temp_dir, os.path.splitext(os.path.basename(tar_path))[0]
        )
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        with tarfile.open(tar_path, "r:*") as tar_ref:
            self._safe_extract_tar(tar_ref, extract_dir)
        return extract_dir

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
