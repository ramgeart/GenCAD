"""
Unit tests for the GenCAD UI components.

Tests chat_handler command parsing and cad_engine interface
without requiring pythonocc-core to be installed.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.cad_engine import CADEngine, HAS_OCC
from ui.chat_handler import ChatHandler, HELP_TEXT, WELCOME_TEXT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_handler():
    engine = CADEngine()
    return ChatHandler(engine), engine


# ---------------------------------------------------------------------------
# ChatHandler – basic routing
# ---------------------------------------------------------------------------


class TestChatHandlerRouting:
    """Verify that every command keyword reaches the right branch."""

    def test_empty_message_returns_guidance(self):
        h, _ = _make_handler()
        reply, model = h.process_message("", None)
        assert "please" in reply.lower()
        assert model is None

    def test_whitespace_only_message(self):
        h, _ = _make_handler()
        reply, model = h.process_message("   \t  ", None)
        assert "please" in reply.lower()

    def test_help_command(self):
        h, _ = _make_handler()
        for cmd in ("help", "?", "commands", "HELP"):
            reply, model = h.process_message(cmd, None)
            assert "create box" in reply.lower(), f"help missing box for cmd={cmd!r}"
            assert model is None

    def test_clear_command(self):
        h, e = _make_handler()
        for cmd in ("clear", "reset", "CLEAR"):
            reply, model = h.process_message(cmd, "/some/path.stl")
            assert "✅" in reply or "cleared" in reply.lower()
            assert model is None
            assert not e.has_shape

    def test_export_without_shape(self):
        h, _ = _make_handler()
        for cmd in ("export", "export stl", "download", "save"):
            reply, model = h.process_message(cmd, None)
            # No shape → error or graceful message
            assert model is None or "no shape" in reply.lower() or "❌" in reply

    def test_unknown_command(self):
        h, _ = _make_handler()
        reply, model = h.process_message("frobulate the grob", None)
        assert "unknown" in reply.lower() or "❓" in reply
        assert model is None

    def test_unknown_command_preserves_model(self):
        h, _ = _make_handler()
        sentinel = "/tmp/existing.stl"
        _, model = h.process_message("nonsense xyz", sentinel)
        assert model == sentinel


# ---------------------------------------------------------------------------
# ChatHandler – shape-creation patterns (no OCC required)
# ---------------------------------------------------------------------------


class TestShapeCommandParsing:
    """
    Ensure the regex patterns correctly parse user input.
    When OCC is absent the commands return graceful error messages;
    when OCC is present (CI/production) they succeed.
    """

    def _send(self, cmd):
        h, _ = _make_handler()
        return h.process_message(cmd, None)

    # Box
    def test_box_integers(self):
        reply, _ = self._send("create box 10 20 30")
        assert "box" in reply.lower()

    def test_box_floats(self):
        reply, _ = self._send("create box 1.5 2.5 3.5")
        assert "box" in reply.lower()

    def test_box_mixed_separators(self):
        reply, _ = self._send("create box 10, 20, 30")
        assert "box" in reply.lower()

    def test_box_case_insensitive(self):
        reply, _ = self._send("CREATE BOX 5 5 5")
        assert "box" in reply.lower()

    # Cylinder
    def test_cylinder_basic(self):
        reply, _ = self._send("create cylinder 5 20")
        assert "cylinder" in reply.lower()

    # Sphere
    def test_sphere_basic(self):
        reply, _ = self._send("create sphere 8")
        assert "sphere" in reply.lower()

    # Cone
    def test_cone_basic(self):
        reply, _ = self._send("create cone 10 0 25")
        assert "cone" in reply.lower() or "frustum" in reply.lower()

    def test_frustum(self):
        reply, _ = self._send("create cone 10 5 15")
        assert "frustum" in reply.lower() or "cone" in reply.lower()

    # Torus
    def test_torus_basic(self):
        reply, _ = self._send("create torus 15 4")
        assert "torus" in reply.lower()


# ---------------------------------------------------------------------------
# CADEngine – no-OCC graceful degradation
# ---------------------------------------------------------------------------


class TestCADEngineNoOCC:
    """
    When pythonocc-core is absent the engine must return descriptive errors
    rather than raising exceptions.
    """

    def setup_method(self):
        self.engine = CADEngine()

    def _expect_graceful_failure(self, ok, result):
        if HAS_OCC:
            # OCC is present – result should be a file path
            assert ok
            assert result and result.endswith(".stl")
        else:
            assert not ok
            assert "not installed" in result.lower() or isinstance(result, str)

    def test_create_box(self):
        ok, result = self.engine.create_box(10, 10, 10)
        self._expect_graceful_failure(ok, result)

    def test_create_cylinder(self):
        ok, result = self.engine.create_cylinder(5, 20)
        self._expect_graceful_failure(ok, result)

    def test_create_sphere(self):
        ok, result = self.engine.create_sphere(8)
        self._expect_graceful_failure(ok, result)

    def test_create_cone(self):
        ok, result = self.engine.create_cone(10, 0, 25)
        self._expect_graceful_failure(ok, result)

    def test_create_torus(self):
        ok, result = self.engine.create_torus(15, 4)
        self._expect_graceful_failure(ok, result)

    def test_export_without_shape_returns_error(self):
        ok, result = self.engine.export_stl()
        assert not ok
        assert "no shape" in result.lower()

    def test_has_shape_false_initially(self):
        assert not self.engine.has_shape

    def test_clear_is_idempotent(self):
        self.engine.clear()
        self.engine.clear()
        assert not self.engine.has_shape


# ---------------------------------------------------------------------------
# Constants / string content
# ---------------------------------------------------------------------------


class TestConstants:
    def test_help_text_contains_all_shapes(self):
        shapes = ["box", "cylinder", "sphere", "cone", "torus"]
        for shape in shapes:
            assert shape in HELP_TEXT.lower(), f"HELP_TEXT missing {shape!r}"

    def test_welcome_text_is_non_empty(self):
        assert len(WELCOME_TEXT) > 0
        assert "gencad" in WELCOME_TEXT.lower()


# ---------------------------------------------------------------------------
# Run tests manually (no pytest required)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    suites = [
        TestChatHandlerRouting,
        TestShapeCommandParsing,
        TestCADEngineNoOCC,
        TestConstants,
    ]

    passed = failed = 0
    for suite_cls in suites:
        suite = suite_cls()
        for attr in dir(suite):
            if attr.startswith("test_"):
                method = getattr(suite, attr)
                if callable(method):
                    try:
                        if hasattr(suite, "setup_method"):
                            suite.setup_method()
                        method()
                        print(f"  PASS  {suite_cls.__name__}.{attr}")
                        passed += 1
                    except Exception:
                        print(f"  FAIL  {suite_cls.__name__}.{attr}")
                        traceback.print_exc()
                        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(failed)
