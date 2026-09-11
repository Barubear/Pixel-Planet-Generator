"""本地生成记录：按图像参数与 seed 防止重复生成。"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random


DEFAULT_REGISTRY_DIR = ".generated_seeds"


def _signature(kind, seed, parameters):
    payload = {"kind": kind, "seed": seed, "parameters": parameters}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest(), payload


def _registry_path(kind, registry_dir):
    return Path(registry_dir) / f"{kind}.jsonl"


def is_registered(kind, seed, parameters, registry_dir=DEFAULT_REGISTRY_DIR):
    """检查相同生成类型、seed 与图像参数是否已成功生成过。"""
    signature, _ = _signature(kind, seed, parameters)
    path = _registry_path(kind, registry_dir)
    if not path.is_file():
        return False
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                if json.loads(line).get("signature") == signature:
                    return True
            except json.JSONDecodeError:
                continue
    return False


def prepare_seed(kind, seed, parameters_for_seed, ensure_unique=False, registry_dir=DEFAULT_REGISTRY_DIR):
    """返回可用 seed；开启 ensure_unique 时拒绝或重试重复图像配置。"""
    if seed is not None:
        if ensure_unique and is_registered(kind, seed, parameters_for_seed(seed), registry_dir):
            raise ValueError("该 seed 与当前图像参数已生成过；请更换 seed 或关闭 ensure_unique")
        return seed

    source = random.SystemRandom()
    for _ in range(10_000):
        candidate = source.randint(0, 999999)
        if not ensure_unique or not is_registered(kind, candidate, parameters_for_seed(candidate), registry_dir):
            return candidate
    raise RuntimeError("无法找到未生成过的 seed，请清理登记文件或扩大 seed 范围")


def record_generation(kind, seed, parameters, registry_dir=DEFAULT_REGISTRY_DIR):
    """在图像成功写入后追加一条本地生成登记。"""
    signature, payload = _signature(kind, seed, parameters)
    path = _registry_path(kind, registry_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "signature": signature,
        **payload,
    }
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
