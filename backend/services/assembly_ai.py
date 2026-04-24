from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Sequence

from backend.services.assembly_documents import (
    build_overview_assets,
    enrich_step_visuals,
    export_instructions_pdf,
)


STORAGE_DIR = os.path.join("backend", "storage")


def _load_parts(job_id: str) -> List[Dict[str, Any]]:
    parts_path = os.path.join(STORAGE_DIR, f"{job_id}_parts.json")
    if not os.path.exists(parts_path):
        raise FileNotFoundError(f"Parts metadata not found for job {job_id}")

    with open(parts_path, "r", encoding="utf-8") as file_obj:
        parts = json.load(file_obj)

    if not parts:
        raise ValueError("No parts found in metadata")
    return parts


def _part_sort_key(part: Dict[str, Any]) -> tuple:
    type_order = {"panel": 0, "other": 1, "connector": 2}
    dims = sorted([float(value) for value in part.get("dimensions", [0, 0, 0])], reverse=True)
    largest = dims[0] if dims else 0.0
    volume = float(part.get("volume", 0.0))
    return (type_order.get(part.get("type", "other"), 1), -largest, -volume, part["id"])


def build_assembly_prompt(parts: Sequence[Dict[str, Any]]) -> str:
    parts_description = []
    for part in sorted(parts, key=_part_sort_key):
        dims = part.get("dimensions", [0, 0, 0])
        parts_description.append(
            f"- ID: {part['id']}, Label: {part.get('label', part.get('type', 'part'))}, "
            f"Type: {part['type']}, Quantity: {part['quantity']}, "
            f"Dimensions (mm): {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f}"
        )

    return f"""You are an expert furniture assembly planner.

You will receive:
1. A visual reference image of the extracted assembly overview.
2. A structured list of parts extracted from a CAD model.

PARTS LIST:
{chr(10).join(parts_description)}

RULES:
1. Start with the biggest structural panels as the base.
2. Add structural panels before small connectors whenever possible.
3. Keep each step practical and incremental.
4. Each step must reference parts by exact part ID.
5. Use only the parts listed above.
6. Generate between 4 and 10 steps depending on complexity.
7. "parts_used" must contain only the NEW parts introduced in the current step.
8. Do not invent screws, tools, hardware, or IDs that are not in the parts list.
9. Prefer grouping repeated connectors into one finishing step when sensible.

Respond with JSON only:
{{
  "title": "Assembly Instructions",
  "steps": [
    {{
      "step_number": 1,
      "title": "Short step title",
      "description": "One concise instruction sentence.",
      "parts_used": [
        {{ "part_id": "part_0", "quantity_in_step": 2 }}
      ]
    }}
  ]
}}"""


def _strip_json_payload(response_text: str) -> str:
    content = response_text.strip()
    if content.startswith("```"):
        lines = [line for line in content.splitlines() if not line.strip().startswith("```")]
        content = "\n".join(lines).strip()

    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    return match.group(0) if match else content


def _sanitize_steps(raw_steps: Sequence[Dict[str, Any]], parts_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    sanitized: List[Dict[str, Any]] = []
    already_used = set()

    for raw_step in raw_steps:
        cleaned_parts = []
        for raw_part in raw_step.get("parts_used", []):
            part_id = raw_part.get("part_id")
            quantity = int(raw_part.get("quantity_in_step", 1) or 1)
            if part_id not in parts_map:
                continue
            if part_id in already_used:
                continue

            max_quantity = int(parts_map[part_id].get("quantity", 1))
            quantity = max(1, min(quantity, max_quantity))
            cleaned_parts.append({"part_id": part_id, "quantity_in_step": quantity})
            already_used.add(part_id)

        if not cleaned_parts:
            continue

        sanitized.append(
            {
                "step_number": len(sanitized) + 1,
                "title": raw_step.get("title", f"Step {len(sanitized) + 1}"),
                "description": raw_step.get("description", "Assemble the highlighted parts."),
                "parts_used": cleaned_parts,
            }
        )

    return sanitized


def _merge_missing_parts(steps: List[Dict[str, Any]], parts_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    assigned = {item["part_id"] for step in steps for item in step.get("parts_used", [])}
    missing = [part for part_id, part in parts_map.items() if part_id not in assigned]
    if not missing:
        return steps

    connectors = [part for part in missing if part.get("type") == "connector"]
    remaining = [part for part in missing if part.get("type") != "connector"]

    for part in remaining:
        steps.append(
            {
                "step_number": len(steps) + 1,
                "title": f"Add {part.get('label', part['id'])}",
                "description": f"Position {part['id']} and align it with the partially assembled structure.",
                "parts_used": [{"part_id": part["id"], "quantity_in_step": int(part.get("quantity", 1))}],
            }
        )

    if connectors:
        steps.append(
            {
                "step_number": len(steps) + 1,
                "title": "Finish with connectors",
                "description": "Install the remaining connectors and tighten the final joints.",
                "parts_used": [
                    {"part_id": part["id"], "quantity_in_step": int(part.get("quantity", 1))}
                    for part in connectors
                ],
            }
        )

    for index, step in enumerate(steps, start=1):
        step["step_number"] = index
    return steps


def _compress_steps_to_limit(steps: List[Dict[str, Any]], max_steps: int = 10) -> List[Dict[str, Any]]:
    compressed = [dict(step) for step in steps]
    while len(compressed) > max_steps:
        donor = compressed.pop()
        receiver = compressed[-1]
        receiver["parts_used"] = receiver.get("parts_used", []) + donor.get("parts_used", [])
        receiver["title"] = "Complete the remaining assembly"
        receiver["description"] = (
            receiver.get("description", "").rstrip(".")
            + ". Then "
            + donor.get("description", "").lstrip().rstrip(".").lower()
            + "."
        )

    for index, step in enumerate(compressed, start=1):
        step["step_number"] = index
    return compressed


def _heuristic_steps(parts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    panels = [part for part in parts if part.get("type") == "panel"]
    connectors = [part for part in parts if part.get("type") == "connector"]
    others = [part for part in parts if part.get("type") not in {"panel", "connector"}]

    panels.sort(key=_part_sort_key)
    connectors.sort(key=_part_sort_key)
    others.sort(key=_part_sort_key)

    steps: List[Dict[str, Any]] = []

    if panels:
        base_batch = panels[: min(2, len(panels))]
        steps.append(
            {
                "step_number": 1,
                "title": "Build the base frame",
                "description": "Lay down the main structural panels and square the base before adding more pieces.",
                "parts_used": [
                    {"part_id": part["id"], "quantity_in_step": int(part.get("quantity", 1))}
                    for part in base_batch
                ],
            }
        )
        remaining_panels = panels[len(base_batch) :]
    else:
        remaining_panels = []

    batch_size = 2
    while remaining_panels:
        batch = remaining_panels[:batch_size]
        remaining_panels = remaining_panels[batch_size:]
        steps.append(
            {
                "step_number": len(steps) + 1,
                "title": "Extend the structure",
                "description": "Attach the next structural components and keep the assembly aligned.",
                "parts_used": [
                    {"part_id": part["id"], "quantity_in_step": int(part.get("quantity", 1))}
                    for part in batch
                ],
            }
        )

    for part in others:
        steps.append(
            {
                "step_number": len(steps) + 1,
                "title": f"Add {part.get('label', part['id'])}",
                "description": f"Fit {part['id']} into the structure and verify its orientation before continuing.",
                "parts_used": [{"part_id": part["id"], "quantity_in_step": int(part.get("quantity", 1))}],
            }
        )

    if connectors:
        connector_batch = max(1, min(3, len(connectors)))
        while connectors:
            batch = connectors[:connector_batch]
            connectors = connectors[connector_batch:]
            steps.append(
                {
                    "step_number": len(steps) + 1,
                    "title": "Secure the joints",
                    "description": "Install the highlighted connectors to lock the current structure in place.",
                    "parts_used": [
                        {"part_id": part["id"], "quantity_in_step": int(part.get("quantity", 1))}
                        for part in batch
                    ],
                }
            )

    if not steps:
        generic_parts = sorted(parts, key=_part_sort_key)
        for part in generic_parts:
            steps.append(
                {
                    "step_number": len(steps) + 1,
                    "title": f"Place {part['id']}",
                    "description": f"Position {part['id']} and integrate it into the assembly.",
                    "parts_used": [{"part_id": part["id"], "quantity_in_step": int(part.get("quantity", 1))}],
                }
            )

    return steps[:10]


async def _call_gemini(prompt: str, image_path: str | None) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")

    import google.generativeai as genai
    from PIL import Image

    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    model = genai.GenerativeModel(model_name)

    content: List[Any] = [prompt]
    if image_path and os.path.exists(image_path):
        content.append(Image.open(image_path))

    response = await asyncio.to_thread(model.generate_content, content)
    payload = _strip_json_payload(response.text)
    return json.loads(payload)


async def _call_openrouter(prompt: str, image_path: str | None) -> Dict[str, Any]:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set")

    model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash-preview")
    content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as file_obj:
            encoded = base64.b64encode(file_obj.read()).decode("ascii")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{encoded}"},
            }
        )

    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "CAD Assembly Generator",
    }

    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter request failed: {exc}") from exc

    message = payload["choices"][0]["message"]["content"]
    if isinstance(message, list):
        text_chunks = [item.get("text", "") for item in message if item.get("type") == "text"]
        message = "\n".join(text_chunks)
    return json.loads(_strip_json_payload(message))


async def _generate_steps_with_ai(parts: Sequence[Dict[str, Any]], image_path: str | None) -> Dict[str, Any]:
    prompt = build_assembly_prompt(parts)
    preferred = os.environ.get("ASSEMBLY_AI_PROVIDER", "").strip().lower()
    providers = [preferred] if preferred else ["gemini", "openrouter"]

    last_error: Exception | None = None
    for provider in providers:
        if provider not in {"gemini", "openrouter"}:
            continue
        try:
            if provider == "gemini":
                return await _call_gemini(prompt, image_path)
            return await _call_openrouter(prompt, image_path)
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    if last_error is not None:
        raise last_error
    raise ValueError("No AI provider configured")


async def generate_assembly_instructions(job_id: str) -> Dict[str, Any]:
    parts = _load_parts(job_id)
    assets = build_overview_assets(job_id, parts, STORAGE_DIR)

    parts_map = {part["id"]: part for part in parts}
    raw_result: Dict[str, Any] | None = None
    ai_error: str | None = None

    try:
        raw_result = await _generate_steps_with_ai(parts, assets.get("overviewPngPath"))
    except Exception as exc:  # noqa: BLE001
        ai_error = str(exc)

    if raw_result:
        steps = _sanitize_steps(raw_result.get("steps", []), parts_map)
        steps = _merge_missing_parts(steps, parts_map)
        steps = _compress_steps_to_limit(steps)
        title = raw_result.get("title", "Assembly Instructions")
    else:
        steps = _heuristic_steps(parts)
        steps = _merge_missing_parts(steps, parts_map)
        steps = _compress_steps_to_limit(steps)
        title = "Assembly Instructions"

    instructions: Dict[str, Any] = {
        "title": title,
        "steps": steps,
        "parts_list": parts,
        "overviewSvgUrl": assets["overviewSvgUrl"],
        "overviewPngUrl": assets["overviewPngUrl"],
        "overviewSvgPath": assets["overviewSvgPath"],
        "overviewPngPath": assets["overviewPngPath"],
        "generationMode": "ai" if raw_result else "heuristic",
    }

    if ai_error:
        instructions["generationWarning"] = ai_error

    for step in instructions["steps"]:
        for part_ref in step.get("parts_used", []):
            part_data = parts_map.get(part_ref["part_id"])
            if part_data:
                part_ref["svgUrl"] = part_data.get("svgUrl")
                part_ref["type"] = part_data.get("type", "other")
                part_ref["dimensions"] = part_data.get("dimensions", [])
                part_ref["label"] = part_data.get("label", part_data["id"])

    instructions = enrich_step_visuals(job_id, instructions, STORAGE_DIR)
    pdf_path = export_instructions_pdf(job_id, instructions, STORAGE_DIR)
    instructions["pdfUrl"] = f"/api/files/{os.path.basename(pdf_path)}"
    instructions["pdfPath"] = pdf_path

    instructions_path = os.path.join(STORAGE_DIR, f"{job_id}_instructions.json")
    with open(instructions_path, "w", encoding="utf-8") as file_obj:
        json.dump(instructions, file_obj, ensure_ascii=False, indent=2)

    return instructions
