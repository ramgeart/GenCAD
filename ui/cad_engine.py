"""
CAD Engine for GenCAD UI.

Wraps pythonocc-core primitives to create, manipulate and export
simple CAD shapes that are displayed in the visual canvas.
"""
import os
import tempfile
from typing import Optional, Tuple

try:
    from OCC.Core.BRepPrimAPI import (
        BRepPrimAPI_MakeBox,
        BRepPrimAPI_MakeCylinder,
        BRepPrimAPI_MakeSphere,
        BRepPrimAPI_MakeCone,
        BRepPrimAPI_MakeTorus,
    )
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
    from OCC.Core.gp import gp_Ax2, gp_Dir, gp_Pnt
    from OCC.Core.TopoDS import TopoDS_Shape
    from OCC.Extend.DataExchange import write_stl_file

    HAS_OCC = True
except ImportError:  # pragma: no cover
    HAS_OCC = False


class CADEngine:
    """
    Manages the current CAD shape and exposes primitive construction
    and export helpers used by the chatbot handler.
    """

    def __init__(self) -> None:
        self._shape: Optional["TopoDS_Shape"] = None
        self._output_dir: str = tempfile.mkdtemp(prefix="gencad_ui_")
        self._stl_path: str = os.path.join(self._output_dir, "model.stl")

    # ------------------------------------------------------------------
    # Public shape constructors
    # ------------------------------------------------------------------

    def create_box(
        self, width: float, height: float, depth: float
    ) -> Tuple[bool, Optional[str]]:
        """Create a rectangular box and update the canvas."""
        if not HAS_OCC:
            return False, "pythonocc-core is not installed."
        self._shape = BRepPrimAPI_MakeBox(width, height, depth).Shape()
        return self._export_stl()

    def create_cylinder(
        self, radius: float, height: float
    ) -> Tuple[bool, Optional[str]]:
        """Create a cylinder and update the canvas."""
        if not HAS_OCC:
            return False, "pythonocc-core is not installed."
        self._shape = BRepPrimAPI_MakeCylinder(radius, height).Shape()
        return self._export_stl()

    def create_sphere(self, radius: float) -> Tuple[bool, Optional[str]]:
        """Create a sphere and update the canvas."""
        if not HAS_OCC:
            return False, "pythonocc-core is not installed."
        self._shape = BRepPrimAPI_MakeSphere(radius).Shape()
        return self._export_stl()

    def create_cone(
        self, radius1: float, radius2: float, height: float
    ) -> Tuple[bool, Optional[str]]:
        """Create a cone (or frustum when radius2 > 0) and update the canvas."""
        if not HAS_OCC:
            return False, "pythonocc-core is not installed."
        self._shape = BRepPrimAPI_MakeCone(radius1, radius2, height).Shape()
        return self._export_stl()

    def create_torus(
        self, major_radius: float, minor_radius: float
    ) -> Tuple[bool, Optional[str]]:
        """Create a torus and update the canvas."""
        if not HAS_OCC:
            return False, "pythonocc-core is not installed."
        self._shape = BRepPrimAPI_MakeTorus(major_radius, minor_radius).Shape()
        return self._export_stl()

    def fuse(self, other: "TopoDS_Shape") -> Tuple[bool, Optional[str]]:
        """Boolean-union the current shape with *other*."""
        if not HAS_OCC:
            return False, "pythonocc-core is not installed."
        if self._shape is None:
            return False, "No base shape to fuse with."
        fused = BRepAlgoAPI_Fuse(self._shape, other)
        if not fused.IsDone():
            return False, "Boolean fuse failed."
        self._shape = fused.Shape()
        return self._export_stl()

    # ------------------------------------------------------------------
    # Export / utility
    # ------------------------------------------------------------------

    def export_stl(self) -> Tuple[bool, Optional[str]]:
        """Export the current shape to STL and return the file path."""
        if self._shape is None:
            return False, "No shape to export."
        return self._export_stl()

    def clear(self) -> None:
        """Remove the current shape from the canvas."""
        self._shape = None

    @property
    def has_shape(self) -> bool:
        return self._shape is not None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _export_stl(self) -> Tuple[bool, Optional[str]]:
        try:
            write_stl_file(
                self._shape,
                self._stl_path,
                mode="binary",
                linear_deflection=0.1,
                angular_deflection=0.1,
            )
            return True, self._stl_path
        except Exception as exc:
            return False, str(exc)
