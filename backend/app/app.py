import json
import threading
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

from .constants import VERSION  # backend version tag

# ---- Internal State (in‑memory) ----
_api_cache: Dict[str, Dict[str, Any]] = {}
_device_lock = threading.Lock()
_device_index: Dict[str, Any] = {}  # serial -> odrive handle


# ---- Helpers ----
def _repo_root() -> Path:
    # Derive repo root relative to this file (backend/app/app.py -> repo/)
    return Path(__file__).resolve().parents[2]


def _api_json_path(fw_major: int) -> Path:
    # Map major firmware to JSON filename (no hardcoded absolute path)
    if fw_major == 0:
        # 0.5.6
        return _repo_root() / "odriveApiReference05x.json"
    if fw_major == 6:
        return _repo_root() / "odriveApiReference06x.json"
    raise ValueError(f"Unsupported firmware major version: {fw_major}")


def _load_api_metadata(fw_major: int) -> Dict[str, Any]:
    key = str(fw_major)
    if key not in _api_cache:
        path = _api_json_path(fw_major)
        with path.open("r", encoding="utf-8") as f:
            _api_cache[key] = json.load(f)
    return _api_cache[key]


def _detect_fw_major(odrv) -> int:
    # ODrive objects expose fw_version_major attribute
    try:
        return int(getattr(odrv, "fw_version_major"))
    except Exception as e:
        raise RuntimeError(f"Failed to read firmware major: {e}") from e


def _serialize_device(odrv) -> Dict[str, Any]:
    fw_major = getattr(odrv, "fw_version_major", None)
    fw_minor = getattr(odrv, "fw_version_minor", None)
    fw_rev = getattr(odrv, "fw_version_revision", None)
    sn = getattr(odrv, "serial_number", None)
    return {
        "serial_number": str(sn) if sn is not None else None,
        "fw_version": f"{fw_major}.{fw_minor}.{fw_rev}",
        "fw_version_major": fw_major,
        "fw_version_minor": fw_minor,
        "fw_version_revision": fw_rev,
    }


def _resolve_attr(root: Any, dotted: str) -> Any:
    cur = root
    for part in dotted.split("."):
        if not hasattr(cur, part):
            raise AttributeError(f"Path segment '{part}' not found while resolving '{dotted}'")
        cur = getattr(cur, part)
    return cur


def _set_attr(root: Any, dotted: str, value: Any):
    parts = dotted.split(".")
    target_parent = _resolve_attr(root, ".".join(parts[:-1])) if len(parts) > 1 else root
    leaf = parts[-1]
    if not hasattr(target_parent, leaf):
        raise AttributeError(f"Leaf attribute '{leaf}' not found in path '{dotted}'")
    setattr(target_parent, leaf, value)


def _get_or_attach_device(serial: str):
    with _device_lock:
        if serial in _device_index:
            return _device_index[serial]
    # Lazy attach (find matching device)
    # imported late to avoid cost at startup
    import odrive
    from fibre import ObjectLostError  # noqa

    od = odrive.find_any(timeout=1.0)
    if not od:
        raise ValueError(f"Device with serial '{serial}' not found")
    found_serial = str(getattr(od, "serial_number", "")).lower()
    if found_serial != serial.lower():
        raise ValueError(f"Device with serial '{serial}' not found (found '{found_serial}')")
    with _device_lock:
        _device_index[serial] = od
    return od


# ---- Flask App Factory ----
def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    @app.route("/api/backend/version", methods=["GET"])
    def backend_version():
        return jsonify({
            "backend_version": VERSION,
            "api_cache_keys": list(_api_cache.keys())
        })

    @app.route("/api/devices", methods=["GET"])
    def list_devices():
        import odrive
        od = odrive.find_any(timeout=1.0)
        found: List[Dict[str, Any]] = []
        with _device_lock:
            _device_index.clear()
            if od:
                ser = str(getattr(od, "serial_number", ""))
                _device_index[ser] = od
                found.append(_serialize_device(od))
        return jsonify(found)

    @app.route("/api/devices/<serial>/api-metadata", methods=["GET"])
    def device_api_metadata(serial: str):
        odrv = _get_or_attach_device(serial)
        fw_major = _detect_fw_major(odrv)
        meta = _load_api_metadata(fw_major)
        # Optionally filter (query param ?section=properties|commands)
        section = request.args.get("section")
        if section:
            if section not in meta:
                return jsonify({"error": f"Section '{section}' not in metadata"}), 400
            return jsonify({section: meta[section], "version": meta.get("version")})
        return jsonify(meta)

    @app.route("/api/devices/<serial>/read", methods=["POST"])
    def read_properties(serial: str):
        """
        Body:
        {
          "paths": ["axis0.controller.input_pos", "..."]
        }
        """
        data = request.get_json(silent=True) or {}
        paths: List[str] = data.get("paths") or []
        if not paths:
            return jsonify({"error": "paths required"}), 400
        odrv = _get_or_attach_device(serial)
        results = {}
        for p in paths:
            try:
                val = _resolve_attr(odrv, p)
                # If val is a complex object (module class), skip raw serialization
                if isinstance(val, (int, float, bool, str)):
                    results[p] = val
                else:
                    results[p] = f"<object:{val.__class__.__name__}>"
            except Exception as e:
                results[p] = {"error": str(e)}
        return jsonify(results)

    @app.route("/api/devices/<serial>/write", methods=["POST"])
    def write_properties(serial: str):
        """
        Body:
        {
          "writes": [
            {"path": "axis0.controller.input_pos", "value": 1.234},
            ...
          ]
        }
        """
        payload = request.get_json(silent=True) or {}
        writes = payload.get("writes")
        if not isinstance(writes, list) or not writes:
            return jsonify({"error": "writes must be non-empty list"}), 400
        odrv = _get_or_attach_device(serial)
        results = []
        for item in writes:
            path = item.get("path")
            value = item.get("value")
            if not path:
                results.append({"path": path, "status": "error", "error": "missing path"})
                continue
            try:
                _set_attr(odrv, path, value)
                results.append({"path": path, "status": "ok"})
            except Exception as e:
                results.append({"path": path, "status": "error", "error": str(e)})
        return jsonify(results)

    @app.route("/api/devices/<serial>/command", methods=["POST"])
    def invoke_command(serial: str):
        """
        Body:
        {
          "path": "axis0.controller.move_incremental",
          "args": [displacement, from_input_pos]
        }
        """
        body = request.get_json(silent=True) or {}
        path = body.get("path")
        args = body.get("args", [])
        if not path:
            return jsonify({"error": "path required"}), 400
        odrv = _get_or_attach_device(serial)
        try:
            func = _resolve_attr(odrv, path)
            if not callable(func):
                return jsonify({"error": f"Attribute at '{path}' not callable"}), 400
            result = func(*args)
            return jsonify({"path": path, "result": result})
        except Exception as e:
            return jsonify({"error": str(e), "path": path}), 400

    return app