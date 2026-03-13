"""
Chat handler for GenCAD UI.

Parses natural-language commands typed in the chatbot area and
delegates to :class:`CADEngine` to create / modify the CAD model
shown on the canvas.

Supported commands (case-insensitive)
--------------------------------------
Shape constructors:
  create box <w> <h> <d>
  create cylinder <radius> <height>
  create sphere <radius>
  create cone <r1> <r2> <height>
  create torus <major_r> <minor_r>

Utility:
  export [stl]   – return the current model as a downloadable STL
  clear          – remove the current shape from the canvas
  help           – show this command reference
"""

import re
from typing import Optional, Tuple

from ui.cad_engine import CADEngine

# ---------------------------------------------------------------------------
# Help text shown to the user
# ---------------------------------------------------------------------------

HELP_TEXT = """\
**Available commands**

🔷 **Shapes**
| Command | Example |
|---------|---------|
| `create box <w> <h> <d>` | `create box 10 10 10` |
| `create cylinder <r> <h>` | `create cylinder 5 20` |
| `create sphere <r>` | `create sphere 8` |
| `create cone <r1> <r2> <h>` | `create cone 10 0 20` |
| `create torus <R> <r>` | `create torus 15 4` |

📤 **Export**
| Command | Description |
|---------|-------------|
| `export stl` | Download the current model as STL |

🗑️ **Other**
| Command | Description |
|---------|-------------|
| `clear` | Remove the current shape from the canvas |
| `help` | Show this help message |
"""

WELCOME_TEXT = """\
👋 Welcome to **GenCAD** – your AI-powered CAD design assistant!

Use the chatbot to describe the shape you want and it will appear \
on the 3D canvas to the left. Type `help` to see all commands.

**Quick start:**
```
create box 20 10 5
create cylinder 8 25
create sphere 12
```
"""

# ---------------------------------------------------------------------------
# Regex patterns for each command
# ---------------------------------------------------------------------------

_NUM = r"([\d.]+)"
_SEP = r"[\s,]+"

_PATTERNS = {
    "box": re.compile(
        rf"create\s+box{_SEP}{_NUM}{_SEP}{_NUM}{_SEP}{_NUM}", re.I
    ),
    "cylinder": re.compile(
        rf"create\s+cylinder{_SEP}{_NUM}{_SEP}{_NUM}", re.I
    ),
    "sphere": re.compile(
        rf"create\s+sphere{_SEP}{_NUM}", re.I
    ),
    "cone": re.compile(
        rf"create\s+cone{_SEP}{_NUM}{_SEP}{_NUM}{_SEP}{_NUM}", re.I
    ),
    "torus": re.compile(
        rf"create\s+torus{_SEP}{_NUM}{_SEP}{_NUM}", re.I
    ),
}


class ChatHandler:
    """Translates chatbot messages into CAD operations."""

    def __init__(self, engine: CADEngine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_message(
        self,
        message: str,
        current_model: Optional[str],
    ) -> Tuple[str, Optional[str]]:
        """
        Process one user message and return ``(reply_text, stl_path)``.

        ``stl_path`` is ``None`` when the canvas should not change.
        """
        text = (message or "").strip()
        if not text:
            return (
                "Please enter a command.  Type `help` for available commands.",
                current_model,
            )

        lower = text.lower()

        # ---- help -------------------------------------------------------
        if lower in {"help", "?", "commands"}:
            return HELP_TEXT, current_model

        # ---- clear ------------------------------------------------------
        if lower in {"clear", "reset"}:
            self._engine.clear()
            return "✅ Canvas cleared.", None

        # ---- export -----------------------------------------------------
        if lower in {"export", "export stl", "download", "save"}:
            ok, result = self._engine.export_stl()
            if ok:
                return "✅ Model exported.  The STL file is ready to download.", result
            return f"❌ {result}", current_model

        # ---- shape constructors ----------------------------------------
        response, model = self._try_create_shape(lower, current_model)
        if response is not None:
            return response, model

        # ---- unknown ----------------------------------------------------
        return (
            f"❓ Unknown command: `{text}`\n\nType `help` to see available commands.",
            current_model,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _try_create_shape(
        self, lower: str, current_model: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Attempt to match a shape-creation command.

        Returns ``(None, None)`` when no pattern matches so the caller
        can fall through to the *unknown command* branch.
        """
        # Box
        m = _PATTERNS["box"].search(lower)
        if m:
            w, h, d = float(m.group(1)), float(m.group(2)), float(m.group(3))
            ok, result = self._engine.create_box(w, h, d)
            if ok:
                return f"✅ Box created — {w} × {h} × {d} mm", result
            return f"❌ Could not create box: {result}", current_model

        # Cylinder
        m = _PATTERNS["cylinder"].search(lower)
        if m:
            r, h = float(m.group(1)), float(m.group(2))
            ok, result = self._engine.create_cylinder(r, h)
            if ok:
                return f"✅ Cylinder created — radius {r} mm, height {h} mm", result
            return f"❌ Could not create cylinder: {result}", current_model

        # Sphere
        m = _PATTERNS["sphere"].search(lower)
        if m:
            r = float(m.group(1))
            ok, result = self._engine.create_sphere(r)
            if ok:
                return f"✅ Sphere created — radius {r} mm", result
            return f"❌ Could not create sphere: {result}", current_model

        # Cone
        m = _PATTERNS["cone"].search(lower)
        if m:
            r1, r2, h = float(m.group(1)), float(m.group(2)), float(m.group(3))
            ok, result = self._engine.create_cone(r1, r2, h)
            if ok:
                label = "Cone" if r2 == 0 else "Frustum"
                return (
                    f"✅ {label} created — bottom-r {r1} mm, top-r {r2} mm, "
                    f"height {h} mm",
                    result,
                )
            return f"❌ Could not create cone: {result}", current_model

        # Torus
        m = _PATTERNS["torus"].search(lower)
        if m:
            R, r = float(m.group(1)), float(m.group(2))
            ok, result = self._engine.create_torus(R, r)
            if ok:
                return (
                    f"✅ Torus created — major-radius {R} mm, "
                    f"minor-radius {r} mm",
                    result,
                )
            return f"❌ Could not create torus: {result}", current_model

        return None, None
