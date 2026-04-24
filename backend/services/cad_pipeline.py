from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, List, Tuple

from backend.services.job_manager import job_manager


STORAGE_DIR = os.path.join("backend", "storage")


def _dims_match(v1: float, v2: float, tol: float = 0.12) -> bool:
    baseline = max(abs(v1), abs(v2), 1.0)
    return abs(v1 - v2) <= baseline * tol


def _classify_part(dimensions: Tuple[float, float, float], volume: float) -> Tuple[str, str]:
    ordered = sorted(dimensions)
    min_dim, mid_dim, max_dim = ordered
    avg_dim = sum(ordered) / 3.0
    slender_ratio = min_dim / max(avg_dim, 1.0)

    if max_dim < 60.0 and volume < 12000:
        return "connector", "small-volume connector candidate"
    if max_dim > 120.0 and slender_ratio < 0.18:
        return "panel", "large thin plate-like component"
    return "other", "generic solid component"


def _part_label(part_type: str, index: int) -> str:
    labels = {
        "panel": "Panel",
        "connector": "Connector",
        "other": "Part",
    }
    return f"{labels.get(part_type, 'Part')} {index + 1}"


def _group_key(dimensions: Tuple[float, float, float], volume: float) -> Tuple[int, int, int, int]:
    ordered = sorted(dimensions)
    return (
        round(ordered[0]),
        round(ordered[1]),
        round(ordered[2]),
        round(volume),
    )


def _should_group(part_type: str, dimensions: Tuple[float, float, float], volume: float) -> bool:
    return part_type == "connector" or (max(dimensions) < 90.0 and volume < 20000)


def process_step_file(job_id: str, file_path: str) -> None:
    async def run() -> None:
        try:
            await job_manager.update_job(job_id, "processing", 10, "Parsing STEP geometry")
            import cadquery as cq

            await job_manager.update_job(job_id, "processing", 25, "Extracting solids")
            shape = cq.importers.importStep(file_path)
            solids = shape.solids().vals()

            if not solids:
                raise ValueError("No solids were extracted from the STEP file")

            assembly = cq.Assembly()
            grouped_parts: List[Dict[str, Any]] = []

            await job_manager.update_job(job_id, "processing", 42, "Classifying and grouping parts")
            for solid_index, solid in enumerate(solids):
                assembly.add(solid)

                volume = float(solid.Volume())
                bbox = solid.BoundingBox()
                dimensions = (float(bbox.xlen), float(bbox.ylen), float(bbox.zlen))
                part_type, classification_reason = _classify_part(dimensions, volume)
                group_small = _should_group(part_type, dimensions, volume)

                matched_group = None
                if group_small:
                    group_signature = _group_key(dimensions, volume)
                    for existing in grouped_parts:
                        if not existing.get("grouped"):
                            continue
                        if existing.get("signature") != group_signature:
                            continue

                        existing_dims = existing["dimensions"]
                        if _dims_match(volume, existing["volume"]) and all(
                            _dims_match(dimensions[idx], existing_dims[idx]) for idx in range(3)
                        ):
                            matched_group = existing
                            break

                instance_payload = {
                    "instanceId": f"instance_{solid_index}",
                    "dimensions": list(dimensions),
                    "volume": volume,
                }

                if matched_group:
                    matched_group["quantity"] += 1
                    matched_group["instances"].append(instance_payload)
                    continue

                group_index = len(grouped_parts)
                grouped_parts.append(
                    {
                        "id": f"part_{group_index}",
                        "label": _part_label(part_type, group_index),
                        "type": part_type,
                        "classificationReason": classification_reason,
                        "dimensions": list(dimensions),
                        "volume": volume,
                        "quantity": 1,
                        "grouped": group_small,
                        "signature": _group_key(dimensions, volume) if group_small else None,
                        "instances": [instance_payload],
                        "solid": solid,
                    }
                )

            await job_manager.update_job(job_id, "processing", 63, "Generating 2D part drawings")
            metadata: List[Dict[str, Any]] = []

            for group in grouped_parts:
                svg_filename = f"{job_id}_{group['id']}.svg"
                svg_path = os.path.join(STORAGE_DIR, svg_filename)
                svg_url = None

                try:
                    cq.exporters.export(
                        group["solid"],
                        svg_path,
                        "SVG",
                        opt={"projectionDir": (-1, -2, 0.5), "showHidden": False},
                    )
                    svg_url = f"/api/files/{svg_filename}"
                except Exception as exc:  # noqa: BLE001
                    print(f"Failed to export SVG for {group['id']}: {exc}")

                metadata.append(
                    {
                        "id": group["id"],
                        "label": group["label"],
                        "type": group["type"],
                        "classificationReason": group["classificationReason"],
                        "quantity": group["quantity"],
                        "dimensions": group["dimensions"],
                        "volume": group["volume"],
                        "grouped": group["grouped"],
                        "instances": group["instances"],
                        "svgUrl": svg_url,
                    }
                )

            metadata_path = os.path.join(STORAGE_DIR, f"{job_id}_parts.json")
            with open(metadata_path, "w", encoding="utf-8") as file_obj:
                json.dump(metadata, file_obj, ensure_ascii=False, indent=2)

            await job_manager.update_job(job_id, "processing", 82, "Triangulating 3D scene")
            glb_path = os.path.join(STORAGE_DIR, f"{job_id}.glb")
            assembly.save(glb_path, "GLTF")

            await job_manager.update_job(job_id, "completed", 100, "STEP processing complete", f"/api/files/{job_id}.glb")
        except Exception as exc:  # noqa: BLE001
            await job_manager.update_job(job_id, "failed", 0, str(exc))

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(run())
        else:
            loop.run_until_complete(run())
    except RuntimeError:
        asyncio.run(run())
