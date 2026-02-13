"""
缓存系统
========

提供缓存功能，用于提高应用程序性能，减少对外部资源的访问。

功能特点：
- 内存缓存
- 文件缓存
- TTL（生存时间）支持
- LRU（最近最少使用）淘汰策略
- 缓存命中统计
"""

import time
import pickle
import threading
from typing import Any, Dict, Optional, Callable, Type

from loguru import logger

from nanobot.monitor.structured_logger import get_structured_logger


class CacheEntry:
    """
    缓存条目

    表示单个缓存项
    """

    __slots__ = ("key", "value", "ttl", "created_at", "accessed_at")

    def __init__(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ):
        """
        初始化缓存条目

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒）
        """
        self.key = key
        self.value = value
        self.ttl = ttl
        self.created_at = time.time()
        self.accessed_at = self.created_at

    def is_expired(self) -> bool:
        """
        检查条目是否过期

        Returns:
            如果过期返回 True，否则返回 False
        """
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def update_access_time(self):
        """
        更新访问时间
        """
        self.accessed_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示

        Returns:
            字典表示的缓存条目
        """
        return {
            "key": self.key,
            "value": self.value,
            "ttl": self.ttl,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
        }


class Cache:
    """
    通用缓存基类

    提供基本的缓存操作接口
    """

    def __init__(self, logger=None):
        if logger is None:
            self.logger = get_structured_logger()
        else:
            self.logger = logger
        self._hits = 0
        self._misses = 0

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 如果未找到返回的默认值

        Returns:
            缓存值或默认值
        """
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒）
        """
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            如果删除成功返回 True，否则返回 False
        """
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在

        Args:
            key: 缓存键

        Returns:
            如果存在返回 True，否则返回 False
        """
        raise NotImplementedError

    def clear(self):
        """
        清除所有缓存
        """
        raise NotImplementedError

    def keys(self) -> list:
        """
        获取所有缓存键

        Returns:
            缓存键列表
        """
        raise NotImplementedError

    def size(self) -> int:
        """
        获取缓存大小

        Returns:
            缓存项数量
        """
        raise NotImplementedError

    def get_hit_count(self) -> int:
        """
        获取缓存命中次数

        Returns:
            命中次数
        """
        return self._hits

    def get_miss_count(self) -> int:
        """
        获取缓存未命中次数

        Returns:
            未命中次数
        """
        return self._misses

    def get_hit_rate(self) -> float:
        """
        获取缓存命中率

        Returns:
            命中率（0-1）
        """
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.get_hit_rate(),
            "size": self.size(),
        }


class MemoryCache(Cache):
    """
    内存缓存实现

    使用 LRU（最近最少使用）淘汰策略。
    """

    def __init__(
        self,
        max_size: int = 1000,
        logger=None,
    ):
        """
        初始化内存缓存

        Args:
            max_size: 缓存最大容量
            logger: 日志记录器（可选）
        """
        super().__init__(logger)
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 如果未找到返回的默认值

        Returns:
            缓存值或默认值
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry:
                if entry.is_expired():
                    del self._cache[key]
                    self._misses += 1
                    return default

                entry.update_access_time()
                self._hits += 1
                return entry.value

            self._misses += 1
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒）
        """
        with self._lock:
            # 如果键已存在，删除旧条目
            if key in self._cache:
                del self._cache[key]

            # 如果超过最大容量，删除最近最少使用的条目
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            # 添加新条目
            self._cache[key] = CacheEntry(key, value, ttl)

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            如果删除成功返回 True，否则返回 False
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在

        Args:
            key: 缓存键

        Returns:
            如果存在返回 True，否则返回 False
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                if entry.is_expired():
                    del self._cache[key]
                    return False
                return True
            return False

    def clear(self):
        """
        清除所有缓存
        """
        with self._lock:
            self._cache.clear()

    def keys(self) -> list:
        """
        获取所有缓存键

        Returns:
            缓存键列表
        """
        with self._lock:
            return list(self._cache.keys())

    def size(self) -> int:
        """
        获取缓存大小

        Returns:
            缓存项数量
        """
        with self._lock:
            return len(self._cache)

    def _evict_lru(self):
        """
        淘汰最近最少使用的条目
        """
        if not self._cache:
            return

        # 找到访问时间最早的条目
        oldest_key = None
        oldest_access = float("inf")

        for key, entry in self._cache.items():
            if entry.accessed_at < oldest_access:
                oldest_access = entry.accessed_at
                oldest_key = key

        if oldest_key:
            del self._cache[oldest_key]

    def get_entries(self) -> Dict[str, CacheEntry]:
        """
        获取所有缓存条目

        Returns:
            所有缓存条目
        """
        with self._lock:
            return dict(self._cache)


class FileCache(Cache):
    """
    文件缓存实现

    将缓存存储在文件系统中。
    """

    def __init__(
        self,
        cache_dir: str = "~/.nanobot/cache",
        max_size: int = 1000,
        logger=None,
    ):
        """
        初始化文件缓存

        Args:
            cache_dir: 缓存文件存储目录
            max_size: 缓存最大容量
            logger: 日志记录器（可选）
        """
        super().__init__(logger)
        self.cache_dir = __import__("pathlib").Path(cache_dir).expanduser()
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

        # 确保缓存目录存在
        self.cache_dir.mkdir(exist_ok=True, parents=True)

        # 加载现有的缓存条目
        self._load_cache()

    def _load_cache(self):
        """
        从磁盘加载缓存
        """
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, "rb") as f:
                        entry: CacheEntry = pickle.load(f)

                    # 检查是否过期
                    if entry.is_expired():
                        cache_file.unlink()
                    else:
                        self._cache[entry.key] = entry
                except Exception as e:
                    logger.debug(f"Error loading cache file {cache_file}: {e}")
                    try:
                        cache_file.unlink()
                    except Exception as e2:
                        logger.debug(f"Failed to delete corrupted cache file: {e2}")

            # 确保缓存不超过最大容量
            while len(self._cache) > self.max_size:
                self._evict_lru()
        except Exception as e:
            logger.error(f"Error loading cache: {e}")

    def _save_entry(self, entry: CacheEntry):
        """
        保存条目到磁盘

        Args:
            entry: 要保存的缓存条目
        """
        try:
            cache_file = self.cache_dir / f"{entry.key}.cache"
            with open(cache_file, "wb") as f:
                pickle.dump(entry, f)
        except Exception as e:
            logger.error(f"Error saving cache entry {entry.key}: {e}")

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 如果未找到返回的默认值

        Returns:
            缓存值或默认值
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry:
                if entry.is_expired():
                    del self._cache[key]
                    try:
                        (self.cache_dir / f"{key}.cache").unlink()
                    except Exception:
                        pass
                    self._misses += 1
                    return default

                entry.update_access_time()
                self._save_entry(entry)
                self._hits += 1
                return entry.value

            self._misses += 1
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒）
        """
        with self._lock:
            # 如果键已存在，删除旧条目
            if key in self._cache:
                del self._cache[key]
                try:
                    (self.cache_dir / f"{key}.cache").unlink()
                except Exception:
                    pass

            # 如果超过最大容量，删除最近最少使用的条目
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            # 添加新条目
            entry = CacheEntry(key, value, ttl)
            self._cache[key] = entry
            self._save_entry(entry)

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            如果删除成功返回 True，否则返回 False
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                try:
                    (self.cache_dir / f"{key}.cache").unlink()
                except Exception:
                    pass
                return True
            return False

    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在

        Args:
            key: 缓存键

        Returns:
            如果存在返回 True，否则返回 False
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                if entry.is_expired():
                    del self._cache[key]
                    try:
                        (self.cache_dir / f"{key}.cache").unlink()
                    except Exception:
                        pass
                    return False
                return True
            return False

    def clear(self):
        """
        清除所有缓存
        """
        with self._lock:
            # 删除所有缓存文件
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.debug(f"Error deleting cache file {cache_file}: {e}")
            self._cache.clear()

    def keys(self) -> list:
        """
        获取所有缓存键

        Returns:
            缓存键列表
        """
        with self._lock:
            return list(self._cache.keys())

    def size(self) -> int:
        """
        获取缓存大小

        Returns:
            缓存项数量
        """
        with self._lock:
            return len(self._cache)

    def _evict_lru(self):
        """
        淘汰最近最少使用的条目
        """
        if not self._cache:
            return

        # 找到访问时间最早的条目
        oldest_key = None
        oldest_access = float("inf")

        for key, entry in self._cache.items():
            if entry.accessed_at < oldest_access:
                oldest_access = entry.accessed_at
                oldest_key = key

        if oldest_key:
            del self._cache[oldest_key]
            try:
                (self.cache_dir / f"{oldest_key}.cache").unlink()
            except Exception:
                pass

    def get_entries(self) -> Dict[str, CacheEntry]:
        """
        获取所有缓存条目

        Returns:
            所有缓存条目
        """
        with self._lock:
            return dict(self._cache)


# 全局缓存实例
_memory_cache_instance: Optional[MemoryCache] = None
_file_cache_instance: Optional[FileCache] = None


def get_memory_cache() -> MemoryCache:
    """
    获取全局内存缓存实例

    Returns:
        内存缓存实例
    """
    global _memory_cache_instance
    if _memory_cache_instance is None:
        _memory_cache_instance = MemoryCache()
    return _memory_cache_instance


def get_file_cache() -> FileCache:
    """
    获取全局文件缓存实例

    Returns:
        文件缓存实例
    """
    global _file_cache_instance
    if _file_cache_instance is None:
        _file_cache_instance = FileCache()
    return _file_cache_instance


# 便捷方法
def cache_get(key: str, default: Optional[Any] = None) -> Any:
    """
    便捷方法：从默认缓存获取值

    Args:
        key: 缓存键
        default: 如果未找到返回的默认值

    Returns:
        缓存值或默认值
    """
    return get_memory_cache().get(key, default)


def cache_set(key: str, value: Any, ttl: Optional[int] = None):
    """
    便捷方法：设置默认缓存值

    Args:
        key: 缓存键
        value: 缓存值
        ttl: 生存时间（秒）
    """
    get_memory_cache().set(key, value, ttl)


def cache_delete(key: str) -> bool:
    """
    便捷方法：删除默认缓存值

    Args:
        key: 缓存键

    Returns:
        如果删除成功返回 True，否则返回 False
    """
    return get_memory_cache().delete(key)


def cache_exists(key: str) -> bool:
    """
    便捷方法：检查缓存键是否存在

    Args:
        key: 缓存键

    Returns:
        如果存在返回 True，否则返回 False
    """
    return get_memory_cache().exists(key)


def cache_clear():
    """
    便捷方法：清除默认缓存
    """
    get_memory_cache().clear()


def cache_size() -> int:
    """
    便捷方法：获取默认缓存大小

    Returns:
        缓存项数量
    """
    return get_memory_cache().size()


def get_cache_stats() -> Dict[str, Any]:
    """
    获取缓存统计信息（便捷方法）

    Returns:
        统计信息字典
    """
    return get_memory_cache().get_stats()
