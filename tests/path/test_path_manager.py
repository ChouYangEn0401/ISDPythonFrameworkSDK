"""
tests/path/test_path_manager.py
================================

Unit + integration tests for path_manager.

Test groups
-----------
1.  Singleton behaviour
2.  set_proj_root
3.  register / unregister / has  (anchor is REQUIRED — no default)
4.  Anchor resolution — each PathMode, get() always returns absolute
5.  as_relative()  — re-express path as relative to a base
6.  exists()
7.  Waterfall — basic resolution
8.  Waterfall — ResolveIntent (READ / WRITE)
9.  Waterfall — pre-built presets
10. WaterfallTrace
11. Conflict resolution strategies
12. info() / list_tags()
13. EnvironmentResolver static methods
14. PathRegistry (internal unit)
15. Waterfall custom check=
16. [SCENARIO] PyInstaller bundled app
17. [SCENARIO] Tkinter desktop app (USER_* dirs, settings, cache)
18. [SCENARIO] ETL pipeline (read inputs, write outputs, fallback to tmp)

Run:
    python tests/path/test_path_manager.py
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Make src/ importable when running without install
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from isd_py_framework_sdk.path_manager import (
    SingletonPathManager,
    PathMode,
    Waterfall,
    ResolveIntent,
    WaterfallTrace,
    Attempt,
    IncrementSuffixStrategy,
    TimestampSuffixStrategy,
    OverwriteStrategy,
    SkipIfExistsStrategy,
    IPathManager,
    EnvironmentResolver,
)
from isd_py_framework_sdk.path_manager._meta import SingletonABCMeta
from isd_py_framework_sdk.path_manager._registry import PathEntry, PathRegistry
from isd_py_framework_sdk.path_manager._waterfall import _check_exists, _check_writable_location


# ---------------------------------------------------------------------------
#  Helper
# ---------------------------------------------------------------------------

def _fresh_manager() -> SingletonPathManager:
    """Return a clean SingletonPathManager by evicting the singleton instance."""
    SingletonABCMeta._instances.pop(SingletonPathManager, None)
    return SingletonPathManager()


# ===========================================================================
#  1. Singleton behaviour
# ===========================================================================

class TestSingleton(unittest.TestCase):

    def test_same_instance(self):
        pm1 = SingletonPathManager()
        pm2 = SingletonPathManager()
        self.assertIs(pm1, pm2)

    def test_isinstance_of_interface(self):
        pm = SingletonPathManager()
        self.assertIsInstance(pm, IPathManager)


# ===========================================================================
#  2. set_proj_root
# ===========================================================================

class TestSetProjRoot(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()

    def test_from_directory(self):
        self.pm.set_proj_root("C:/Users")
        self.pm.register("x", "sub", PathMode.PROJ_ABSOLUTE)
        self.assertEqual(self.pm.get("x"), (Path("C:/Users").resolve() / "sub").resolve())

    def test_from_file_levels_up_0(self):
        self.pm.set_proj_root(__file__, levels_up=0)
        expected = Path(__file__).resolve().parent
        self.pm.register("y", "data", PathMode.PROJ_ABSOLUTE)
        self.assertEqual(self.pm.get("y"), (expected / "data").resolve())

    def test_from_file_levels_up_2(self):
        self.pm.set_proj_root(__file__, levels_up=2)
        expected = Path(__file__).resolve().parent.parent.parent
        self.pm.register("z", "src", PathMode.PROJ_ABSOLUTE)
        self.assertEqual(self.pm.get("z"), (expected / "src").resolve())


# ===========================================================================
#  3. register / unregister / has  — anchor REQUIRED
# ===========================================================================

class TestRegistry(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()
        self.pm.set_proj_root(__file__, levels_up=2)

    def test_register_requires_anchor(self):
        """Calling register() without anchor must raise TypeError."""
        with self.assertRaises(TypeError):
            self.pm.register("bad", "data/inputs")  # type: ignore[call-arg]

    def test_register_and_has(self):
        self.pm.register("alpha", "data/inputs", PathMode.PROJ_ABSOLUTE, description="inputs")
        self.assertTrue(self.pm.has("alpha"))

    def test_overwrite_on_re_register(self):
        self.pm.register("beta", "old/path", PathMode.PROJ_ABSOLUTE)
        self.pm.register("beta", "new/path", PathMode.PROJ_ABSOLUTE)
        self.assertIn("new", str(self.pm.get("beta")))

    def test_unregister(self):
        self.pm.register("gamma", "some/path", PathMode.PROJ_ABSOLUTE)
        self.pm.unregister("gamma")
        self.assertFalse(self.pm.has("gamma"))

    def test_unregister_missing_raises(self):
        with self.assertRaises(KeyError):
            self.pm.unregister("nonexistent_tag_xyz")

    def test_get_missing_raises(self):
        with self.assertRaises(KeyError):
            self.pm.get("ghost_tag_9999")

    def test_list_tags(self):
        self.pm.register("t1", "p1", PathMode.PROJ_ABSOLUTE, description="desc1")
        self.pm.register("t2", "p2", PathMode.PROJ_ABSOLUTE, description="desc2")
        tags = self.pm.list_tags()
        self.assertEqual(tags.get("t1"), "desc1")
        self.assertEqual(tags.get("t2"), "desc2")


# ===========================================================================
#  4. Anchor resolution — get() always returns absolute Path
# ===========================================================================

class TestAnchorResolution(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()
        self.pm.set_proj_root(__file__, levels_up=2)
        self.proj_root = Path(__file__).resolve().parent.parent.parent

    def test_proj_absolute(self):
        self.pm.register("pa", "data/inputs", PathMode.PROJ_ABSOLUTE)
        p = self.pm.get("pa")
        self.assertTrue(p.is_absolute())
        self.assertEqual(p, (self.proj_root / "data/inputs").resolve())

    def test_proj_relative_same_as_proj_absolute(self):
        self.pm.register("pr", "data/outputs", PathMode.PROJ_RELATIVE)
        p = self.pm.get("pr")
        self.assertTrue(p.is_absolute())
        self.assertEqual(p, (self.proj_root / "data/outputs").resolve())

    def test_proj_raises_when_root_not_set(self):
        pm2 = _fresh_manager()
        pm2.register("oops", "data/x", PathMode.PROJ_ABSOLUTE)
        with self.assertRaises(RuntimeError):
            pm2.get("oops")

    def test_absolute_anchor(self):
        abs_path = Path(tempfile.gettempdir()) / "isd_test_abs.txt"
        self.pm.register("abs", str(abs_path), PathMode.ABSOLUTE)
        self.assertEqual(self.pm.get("abs"), abs_path.resolve())

    def test_exe_absolute(self):
        self.pm.register("exe", "configs/app.toml", PathMode.EXE_ABSOLUTE)
        p = self.pm.get("exe")
        self.assertTrue(p.is_absolute())
        self.assertIn("configs", str(p))

    def test_system_temp(self):
        self.pm.register("tmp", "run/cache", PathMode.SYSTEM_TEMP)
        p = self.pm.get("tmp")
        self.assertTrue(p.is_absolute())
        self.assertTrue(str(p).startswith(str(EnvironmentResolver.system_temp_root())))

    def test_cwd(self):
        self.pm.register("cwd_tag", "sub/file.txt", PathMode.CWD)
        p = self.pm.get("cwd_tag")
        self.assertTrue(p.is_absolute())
        self.assertEqual(p, (EnvironmentResolver.cwd() / "sub/file.txt").resolve())

    def test_user_home(self):
        self.pm.register("home_tag", ".myapp/config", PathMode.USER_HOME)
        p = self.pm.get("home_tag")
        self.assertTrue(p.is_absolute())
        self.assertIn(".myapp", str(p))

    def test_user_config(self):
        self.pm.set_app_name("test_isd_app")
        self.pm.register("cfg", "settings.toml", PathMode.USER_CONFIG)
        p = self.pm.get("cfg")
        self.assertTrue(p.is_absolute())
        self.assertIn("settings.toml", p.name)

    def test_user_data(self):
        self.pm.set_app_name("test_isd_app")
        self.pm.register("dat", "db.sqlite", PathMode.USER_DATA)
        p = self.pm.get("dat")
        self.assertTrue(p.is_absolute())

    def test_user_cache(self):
        self.pm.set_app_name("test_isd_app")
        self.pm.register("cch", "thumb.bin", PathMode.USER_CACHE)
        p = self.pm.get("cch")
        self.assertTrue(p.is_absolute())

    def test_script_dir(self):
        self.pm.register("sd", "data/ref.csv", PathMode.SCRIPT_DIR)
        p = self.pm.get("sd")
        self.assertTrue(p.is_absolute())

    def test_virtual_env_raises_when_missing(self):
        original = os.environ.pop("VIRTUAL_ENV", None)
        try:
            self.pm.register("venv_tag", "bin", PathMode.VIRTUAL_ENV)
            with self.assertRaises(RuntimeError):
                self.pm.get("venv_tag")
        finally:
            if original is not None:
                os.environ["VIRTUAL_ENV"] = original

    def test_virtual_env_when_active(self):
        os.environ["VIRTUAL_ENV"] = str(Path.home())
        try:
            self.pm.register("venv2", "lib", PathMode.VIRTUAL_ENV)
            p = self.pm.get("venv2")
            self.assertTrue(p.is_absolute())
        finally:
            del os.environ["VIRTUAL_ENV"]


# ===========================================================================
#  5. as_relative()
# ===========================================================================

class TestAsRelative(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()
        self.pm.set_proj_root(__file__, levels_up=2)

    def test_proj_absolute_as_relative(self):
        self.pm.register("data_in", "data/inputs", PathMode.PROJ_ABSOLUTE)
        rel = self.pm.as_relative("data_in", PathMode.PROJ_ABSOLUTE)
        self.assertFalse(rel.is_absolute())
        self.assertEqual(rel, Path("data/inputs"))

    def test_as_relative_raises_when_outside_base(self):
        self.pm.register("tmp", "run/cache", PathMode.SYSTEM_TEMP)
        with self.assertRaises(ValueError):
            self.pm.as_relative("tmp", PathMode.PROJ_ABSOLUTE)

    def test_absolute_anchor_expressed_relative_to_system_temp(self):
        tmp_root = EnvironmentResolver.system_temp_root()
        inner = tmp_root / "myapp" / "log.txt"
        self.pm.register("log", str(inner), PathMode.ABSOLUTE)
        rel = self.pm.as_relative("log", PathMode.SYSTEM_TEMP)
        self.assertEqual(rel, Path("myapp/log.txt"))


# ===========================================================================
#  6. exists()
# ===========================================================================

class TestExists(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()
        self.pm.set_proj_root(__file__, levels_up=2)

    def test_exists_true_for_real_path(self):
        tests_dir = Path(__file__).resolve().parent.parent
        self.pm.register("tests_dir", str(tests_dir), PathMode.ABSOLUTE)
        self.assertTrue(self.pm.exists("tests_dir"))

    def test_exists_false_for_nonexistent(self):
        self.pm.register("ghost", "this/path/does/not/exist/xyz_9999", PathMode.PROJ_ABSOLUTE)
        self.assertFalse(self.pm.exists("ghost"))

    def test_exists_false_for_unknown_tag(self):
        self.assertFalse(self.pm.exists("completely_missing_tag"))


# ===========================================================================
#  7. Waterfall — basic resolution
# ===========================================================================

class TestWaterfallBasic(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()
        self.pm.set_proj_root(__file__, levels_up=2)

    def test_waterfall_returns_first_existing(self):
        self.pm.register("w1", "", PathMode.SYSTEM_TEMP)
        wf = Waterfall(PathMode.PROJ_ABSOLUTE, PathMode.SYSTEM_TEMP)
        p = self.pm.get("w1", wf)
        self.assertTrue(p.exists())

    def test_waterfall_raises_when_nothing_exists(self):
        self.pm.register("w2", "this/does/not/exist/xyz_99", PathMode.PROJ_ABSOLUTE)
        wf = Waterfall(PathMode.PROJ_ABSOLUTE, PathMode.CWD)
        with self.assertRaises(FileNotFoundError):
            self.pm.get("w2", wf)

    def test_waterfall_error_contains_trace(self):
        self.pm.register("w3", "no/such/path_zzz", PathMode.PROJ_ABSOLUTE)
        wf = Waterfall(PathMode.PROJ_ABSOLUTE)
        try:
            self.pm.get("w3", wf)
        except FileNotFoundError as exc:
            self.assertIn("WaterfallTrace", str(exc))

    def test_get_with_trace_no_raise_on_failure(self):
        self.pm.register("w4", "definitely/not/here_zzz", PathMode.PROJ_ABSOLUTE)
        path, trace = self.pm.get_with_trace("w4", Waterfall.DEV_STANDARD)
        self.assertIsNone(path)
        self.assertIsInstance(trace, WaterfallTrace)
        self.assertFalse(trace.succeeded)

    def test_get_with_trace_success(self):
        self.pm.register("w5", "", PathMode.SYSTEM_TEMP)
        path, trace = self.pm.get_with_trace(
            "w5",
            Waterfall(PathMode.PROJ_ABSOLUTE, PathMode.SYSTEM_TEMP),
        )
        self.assertIsNotNone(path)
        self.assertTrue(trace.succeeded)

    def test_waterfall_overrides_registered_anchor(self):
        """Waterfall ignores registered anchor; uses waterfall steps instead."""
        self.pm.register("override_test", "", PathMode.USER_DATA)
        wf = Waterfall(PathMode.PROJ_ABSOLUTE, PathMode.SYSTEM_TEMP)
        p = self.pm.get("override_test", wf)
        self.assertTrue(p.exists())


# ===========================================================================
#  8. Waterfall — ResolveIntent
# ===========================================================================

class TestWaterfallIntent(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()
        self.pm.set_proj_root(__file__, levels_up=2)

    def test_write_intent_accepts_writable_parent(self):
        self.pm.register("wout", "nonexistent_output.xlsx", PathMode.SYSTEM_TEMP)
        wf = Waterfall(PathMode.SYSTEM_TEMP)
        p = self.pm.get("wout", wf, intent=ResolveIntent.WRITE)
        self.assertIsNotNone(p)
        self.assertTrue(p.parent.exists())

    def test_read_intent_rejects_nonexistent(self):
        self.pm.register("rin", "nosuchfile_zzz.csv", PathMode.SYSTEM_TEMP)
        wf = Waterfall(PathMode.SYSTEM_TEMP)
        with self.assertRaises(FileNotFoundError):
            self.pm.get("rin", wf, intent=ResolveIntent.READ)

    def test_write_intent_falls_through_to_temp(self):
        self.pm.register("etl_out", "outputs/result.csv", PathMode.PROJ_ABSOLUTE)
        path, trace = self.pm.get_with_trace(
            "etl_out",
            Waterfall(PathMode.PROJ_ABSOLUTE, PathMode.SYSTEM_TEMP),
            intent=ResolveIntent.WRITE,
        )
        self.assertIsNotNone(path)
        self.assertTrue(trace.succeeded)


# ===========================================================================
#  9. Waterfall — pre-built presets
# ===========================================================================

class TestWaterfallPresets(unittest.TestCase):

    def test_all_presets_are_waterfall_instances(self):
        presets = [
            Waterfall.DEV_STANDARD, Waterfall.DEV_WITH_USER_CONFIG,
            Waterfall.PROD_READ, Waterfall.PROD_WRITE,
            Waterfall.EXE_PREFER_BUNDLED, Waterfall.EXE_WRITE_SAFE,
            Waterfall.ETL_INPUT, Waterfall.ETL_OUTPUT,
            Waterfall.CI_ARTIFACT, Waterfall.UNIVERSAL,
        ]
        for wf in presets:
            with self.subTest(wf=wf):
                self.assertIsInstance(wf, Waterfall)
                self.assertGreater(len(wf.steps), 0)

    def test_presets_repr(self):
        self.assertIn("→", repr(Waterfall.UNIVERSAL))

    def test_equality(self):
        self.assertEqual(
            Waterfall(PathMode.PROJ_ABSOLUTE, PathMode.CWD),
            Waterfall(PathMode.PROJ_ABSOLUTE, PathMode.CWD),
        )

    def test_inequality(self):
        self.assertNotEqual(Waterfall.DEV_STANDARD, Waterfall.ETL_INPUT)


# ===========================================================================
#  10. WaterfallTrace
# ===========================================================================

class TestWaterfallTrace(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()
        self.pm.set_proj_root(__file__, levels_up=2)

    def test_trace_has_attempts(self):
        self.pm.register("tr", "some/path", PathMode.PROJ_ABSOLUTE)
        _, trace = self.pm.get_with_trace("tr", Waterfall.DEV_STANDARD)
        self.assertIsInstance(trace.attempts, list)
        self.assertGreater(len(trace.attempts), 0)

    def test_attempt_str(self):
        self.pm.register("tr2", "nope/path", PathMode.PROJ_ABSOLUTE)
        _, trace = self.pm.get_with_trace("tr2", Waterfall(PathMode.PROJ_ABSOLUTE))
        attempt = trace.attempts[0]
        self.assertIsInstance(attempt, Attempt)
        self.assertIn("PROJ_ABSOLUTE", str(attempt))

    def test_trace_str(self):
        self.pm.register("tr3", "nope", PathMode.CWD)
        _, trace = self.pm.get_with_trace("tr3", Waterfall(PathMode.CWD))
        self.assertIn("WaterfallTrace", str(trace))

    def test_successful_attempt_marked_ok(self):
        self.pm.register("tr4", "", PathMode.SYSTEM_TEMP)
        _, trace = self.pm.get_with_trace("tr4", Waterfall(PathMode.SYSTEM_TEMP))
        winning = next((a for a in trace.attempts if a.ok), None)
        self.assertIsNotNone(winning)


# ===========================================================================
#  11. Conflict resolution
# ===========================================================================

class TestConflictResolution(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _register_file(self, tag: str, filename: str) -> Path:
        target = self.tmpdir / filename
        self.pm.register(tag, str(target), PathMode.ABSOLUTE)
        return target

    def test_no_conflict_returns_original(self):
        target = self._register_file("nc", "results.xlsx")
        self.assertEqual(self.pm.resolve_conflict("nc"), target)

    def test_increment_suffix_on_conflict(self):
        target = self._register_file("ic", "report.xlsx")
        target.write_text("existing")
        safe = self.pm.resolve_conflict("ic", strategy=IncrementSuffixStrategy())
        self.assertIn("_001", safe.name)

    def test_increment_suffix_skips_existing(self):
        target = self._register_file("ic2", "data.csv")
        target.write_text("v1")
        (self.tmpdir / "data_001.csv").write_text("v1b")
        self.assertIn("_002", self.pm.resolve_conflict("ic2", strategy=IncrementSuffixStrategy()).name)

    def test_timestamp_suffix_on_conflict(self):
        target = self._register_file("ts", "output.csv")
        target.write_text("exists")
        safe = self.pm.resolve_conflict("ts", strategy=TimestampSuffixStrategy())
        self.assertRegex(safe.stem, r"output_\d{8}_\d{6}")

    def test_overwrite_strategy(self):
        target = self._register_file("ow", "log.txt")
        target.write_text("old")
        self.assertEqual(self.pm.resolve_conflict("ow", strategy=OverwriteStrategy()), target)

    def test_skip_strategy(self):
        target = self._register_file("sk", "skip.txt")
        target.write_text("keep")
        self.assertEqual(self.pm.resolve_conflict("sk", strategy=SkipIfExistsStrategy()), target)

    def test_default_strategy_is_increment(self):
        target = self._register_file("ds", "default.xlsx")
        target.write_text("exists")
        self.assertIn("_001", self.pm.resolve_conflict("ds").name)


# ===========================================================================
#  12. info() / list_tags()
# ===========================================================================

class TestIntrospection(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()
        self.pm.set_proj_root(__file__, levels_up=2)

    def test_info_contains_pyinstaller_flag(self):
        self.assertIn("pyinstaller", self.pm.info())

    def test_info_contains_registered_tags(self):
        self.pm.register("introspect_tag", "data/x", PathMode.PROJ_ABSOLUTE, description="my desc")
        text = self.pm.info()
        self.assertIn("introspect_tag", text)
        self.assertIn("my desc", text)

    def test_info_shows_anchor_name(self):
        self.pm.register("anchor_check", "logs", PathMode.USER_DATA)
        self.assertIn("USER_DATA", self.pm.info())

    def test_list_tags_returns_all(self):
        self.pm.register("t_a", "a/b", PathMode.PROJ_ABSOLUTE)
        self.pm.register("t_b", "c/d", PathMode.PROJ_ABSOLUTE, description="desc_b")
        tags = self.pm.list_tags()
        self.assertIn("t_a", tags)
        self.assertEqual(tags["t_b"], "desc_b")


# ===========================================================================
#  13. EnvironmentResolver static methods
# ===========================================================================

class TestEnvironmentResolver(unittest.TestCase):

    def test_is_pyinstaller_false_in_dev(self):
        self.assertFalse(EnvironmentResolver.is_pyinstaller())

    def test_exe_inner_raises_in_dev(self):
        with self.assertRaises(RuntimeError):
            EnvironmentResolver.exe_inner_root()

    def test_exe_side_root_is_absolute(self):
        self.assertTrue(EnvironmentResolver.exe_side_root().is_absolute())

    def test_system_temp_is_absolute(self):
        self.assertTrue(EnvironmentResolver.system_temp_root().is_absolute())

    def test_cwd_is_absolute(self):
        self.assertTrue(EnvironmentResolver.cwd().is_absolute())

    def test_script_dir_is_absolute(self):
        self.assertTrue(EnvironmentResolver.script_dir().is_absolute())

    def test_user_home_is_absolute(self):
        self.assertTrue(EnvironmentResolver.user_home().is_absolute())

    def test_user_config_is_absolute(self):
        self.assertTrue(EnvironmentResolver.user_config("test_isd").is_absolute())

    def test_user_data_is_absolute(self):
        self.assertTrue(EnvironmentResolver.user_data("test_isd").is_absolute())

    def test_user_cache_is_absolute(self):
        self.assertTrue(EnvironmentResolver.user_cache("test_isd").is_absolute())

    def test_virtual_env_missing(self):
        original = os.environ.pop("VIRTUAL_ENV", None)
        try:
            with self.assertRaises(RuntimeError):
                EnvironmentResolver.virtual_env()
        finally:
            if original is not None:
                os.environ["VIRTUAL_ENV"] = original

    def test_virtual_env_present(self):
        os.environ["VIRTUAL_ENV"] = str(Path.home())
        try:
            self.assertTrue(EnvironmentResolver.virtual_env().is_absolute())
        finally:
            del os.environ["VIRTUAL_ENV"]


# ===========================================================================
#  14. PathRegistry (internal unit tests)
# ===========================================================================

class TestPathRegistry(unittest.TestCase):

    def test_add_and_get(self):
        reg = PathRegistry()
        entry = PathEntry("foo", Path("data"), PathMode.PROJ_RELATIVE, "test")
        reg.add(entry)
        self.assertEqual(reg.get("foo"), entry)

    def test_add_overwrites_silently(self):
        reg = PathRegistry()
        reg.add(PathEntry("x", Path("old"), PathMode.ABSOLUTE))
        reg.add(PathEntry("x", Path("new"), PathMode.ABSOLUTE))
        self.assertEqual(reg.get("x").stored_path, Path("new"))

    def test_has(self):
        reg = PathRegistry()
        reg.add(PathEntry("bar", Path("x"), PathMode.ABSOLUTE))
        self.assertTrue(reg.has("bar"))
        self.assertFalse(reg.has("baz"))

    def test_remove(self):
        reg = PathRegistry()
        reg.add(PathEntry("to_rm", Path("y"), PathMode.ABSOLUTE))
        reg.remove("to_rm")
        self.assertFalse(reg.has("to_rm"))

    def test_remove_missing_raises(self):
        reg = PathRegistry()
        with self.assertRaises(KeyError):
            reg.remove("nothere")

    def test_get_missing_raises(self):
        reg = PathRegistry()
        with self.assertRaises(KeyError):
            reg.get("nothere")

    def test_all_entries_is_copy(self):
        reg = PathRegistry()
        reg.add(PathEntry("e1", Path("a"), PathMode.ABSOLUTE))
        reg.add(PathEntry("e2", Path("b"), PathMode.CWD))
        entries = reg.all_entries()
        entries.pop("e1")
        self.assertTrue(reg.has("e1"))


# ===========================================================================
#  15. Waterfall custom check=
# ===========================================================================

class TestWaterfallCustomCheck(unittest.TestCase):

    def setUp(self):
        self.pm = _fresh_manager()
        self.pm.set_proj_root(__file__, levels_up=2)

    def test_custom_check_always_true(self):
        self.pm.register("cc", "nonexistent/path_xyz", PathMode.PROJ_ABSOLUTE)
        p = self.pm.get("cc", Waterfall(PathMode.PROJ_ABSOLUTE, check=lambda p: True))
        self.assertIsNotNone(p)

    def test_custom_check_always_false(self):
        self.pm.register("cf", "some/path", PathMode.PROJ_ABSOLUTE)
        with self.assertRaises(FileNotFoundError):
            self.pm.get("cf", Waterfall(PathMode.PROJ_ABSOLUTE, PathMode.CWD, check=lambda p: False))


# ===========================================================================
#  16. [SCENARIO] PyInstaller bundled app
# ===========================================================================

class TestPyInstallerScenario(unittest.TestCase):
    """
    Mock sys.frozen + sys._MEIPASS to simulate a packaged environment.

    Layout:
        tmp/_MEIPASS/
            models/clf.pkl          ← bundled ML model
            data/reference.csv      ← bundled reference data
        tmp/exe_side/
            myapp.exe               ← the .exe lives here

    Expected:
        register("model", "models/clf.pkl", PathMode.EXE_INNER)
          → get("model") resolves to _MEIPASS/models/clf.pkl

        register("model", "models/clf.pkl", PathMode.PROJ_ABSOLUTE)  (dev default)
          → get("model", Waterfall.EXE_PREFER_BUNDLED)
             EXE_INNER step hits _MEIPASS first → wins
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.meipass = self.tmp / "_MEIPASS"
        self.meipass.mkdir()
        (self.meipass / "models").mkdir()
        (self.meipass / "models" / "clf.pkl").write_bytes(b"fake_model")
        (self.meipass / "data").mkdir()
        (self.meipass / "data" / "reference.csv").write_bytes(b"col1,col2\n1,2")
        self.exe_side = self.tmp / "exe_side"
        self.exe_side.mkdir()

        self._orig_frozen     = getattr(sys, "frozen",     None)
        self._orig_meipass    = getattr(sys, "_MEIPASS",   None)
        self._orig_executable = sys.executable
        sys.frozen    = True                               # type: ignore[attr-defined]
        sys._MEIPASS  = str(self.meipass)                  # type: ignore[attr-defined]
        sys.executable = str(self.exe_side / "myapp.exe")

        self.pm = _fresh_manager()
        self.pm.set_proj_root(self.tmp / "src")

    def tearDown(self):
        if self._orig_frozen is None:
            try: del sys.frozen    # type: ignore[attr-defined]
            except AttributeError: pass
        else:
            sys.frozen = self._orig_frozen  # type: ignore[attr-defined]
        if self._orig_meipass is None:
            try: del sys._MEIPASS  # type: ignore[attr-defined]
            except AttributeError: pass
        else:
            sys._MEIPASS = self._orig_meipass  # type: ignore[attr-defined]
        sys.executable = self._orig_executable
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_is_pyinstaller_returns_true(self):
        self.assertTrue(EnvironmentResolver.is_pyinstaller())

    def test_exe_inner_root_is_meipass(self):
        self.assertEqual(EnvironmentResolver.exe_inner_root(), self.meipass.resolve())

    def test_exe_inner_anchor_resolves_bundled_file(self):
        self.pm.register("model", "models/clf.pkl", PathMode.EXE_INNER)
        p = self.pm.get("model")
        self.assertTrue(p.exists())
        self.assertEqual(p, (self.meipass / "models/clf.pkl").resolve())

    def test_exe_inner_anchor_resolves_bundled_csv(self):
        self.pm.register("ref_data", "data/reference.csv", PathMode.EXE_INNER)
        self.assertTrue(self.pm.get("ref_data").exists())

    def test_waterfall_exe_prefer_bundled_finds_meipass_first(self):
        """Even if registered as PROJ_ABSOLUTE, waterfall finds _MEIPASS."""
        self.pm.register("model", "models/clf.pkl", PathMode.PROJ_ABSOLUTE)
        p = self.pm.get("model", Waterfall.EXE_PREFER_BUNDLED)
        self.assertTrue(p.exists())
        self.assertIn(str(self.meipass), str(p))

    def test_waterfall_trace_shows_exe_inner_won(self):
        self.pm.register("model", "models/clf.pkl", PathMode.PROJ_ABSOLUTE)
        path, trace = self.pm.get_with_trace("model", Waterfall.EXE_PREFER_BUNDLED)
        self.assertIsNotNone(path)
        winning = next((a for a in trace.attempts if a.ok), None)
        self.assertIsNotNone(winning)
        self.assertEqual(winning.mode, PathMode.EXE_INNER)

    def test_write_log_beside_exe(self):
        self.pm.register("log", "logs/app.log", PathMode.EXE_ABSOLUTE)
        p = self.pm.get("log")
        self.assertEqual(p, (self.exe_side / "logs/app.log").resolve())
        # Parent (exe_side/) exists → WRITE intent passes
        path, trace = self.pm.get_with_trace(
            "log",
            Waterfall(PathMode.EXE_ABSOLUTE, PathMode.SYSTEM_TEMP),
            intent=ResolveIntent.WRITE,
        )
        self.assertIsNotNone(path)

    def test_universal_waterfall_degrades_to_temp(self):
        self.pm.register("artefact", "ci/output.zip", PathMode.PROJ_ABSOLUTE)
        path, trace = self.pm.get_with_trace(
            "artefact", Waterfall.UNIVERSAL, intent=ResolveIntent.WRITE,
        )
        self.assertIsNotNone(path)
        self.assertTrue(trace.succeeded)


# ===========================================================================
#  17. [SCENARIO] Tkinter desktop app
# ===========================================================================

class TestTkinterAppScenario(unittest.TestCase):
    """
    A tkinter GUI tool called DataStudio.
    Registered at startup:
        settings   → USER_CONFIG  (persists across updates)
        history    → USER_DATA    (recent-files db)
        thumb_cache→ USER_CACHE   (safe to delete)
        scratch    → SYSTEM_TEMP  (per-session scratch)
        templates  → EXE_ABSOLUTE (read-only bundled layouts)
    """

    def setUp(self):
        self.pm = _fresh_manager()
        self.pm.set_app_name("DataStudio")
        self.pm.register("settings",    "settings.json",       PathMode.USER_CONFIG)
        self.pm.register("history",     "history.db",          PathMode.USER_DATA)
        self.pm.register("thumb_cache", "thumbs",              PathMode.USER_CACHE)
        self.pm.register("scratch",     "DataStudio_session",  PathMode.SYSTEM_TEMP)
        self.pm.register("templates",   "templates",           PathMode.EXE_ABSOLUTE)

    def test_settings_is_absolute(self):
        self.assertTrue(self.pm.get("settings").is_absolute())

    def test_settings_is_under_user_config(self):
        p = self.pm.get("settings")
        cfg_dir = EnvironmentResolver.user_config("DataStudio")
        self.assertEqual(p, (cfg_dir / "settings.json").resolve())

    def test_history_is_under_user_data(self):
        p = self.pm.get("history")
        self.assertEqual(p, (EnvironmentResolver.user_data("DataStudio") / "history.db").resolve())

    def test_thumb_cache_is_under_user_cache(self):
        p = self.pm.get("thumb_cache")
        self.assertEqual(p, (EnvironmentResolver.user_cache("DataStudio") / "thumbs").resolve())

    def test_scratch_is_in_temp(self):
        p = self.pm.get("scratch")
        self.assertTrue(str(p).startswith(str(EnvironmentResolver.system_temp_root())))

    def test_templates_beside_exe(self):
        p = self.pm.get("templates")
        self.assertEqual(p, (EnvironmentResolver.exe_side_root() / "templates").resolve())

    def test_settings_write_fallback(self):
        """On first launch config dir may not exist; SYSTEM_TEMP is the fallback."""
        path, trace = self.pm.get_with_trace(
            "settings",
            Waterfall(PathMode.USER_CONFIG, PathMode.SYSTEM_TEMP),
            intent=ResolveIntent.WRITE,
        )
        self.assertIsNotNone(path)
        self.assertTrue(trace.succeeded)

    def test_history_write_uses_prod_write(self):
        path, trace = self.pm.get_with_trace(
            "history", Waterfall.PROD_WRITE, intent=ResolveIntent.WRITE,
        )
        self.assertIsNotNone(path)
        self.assertTrue(trace.succeeded)

    def test_info_shows_all_tags(self):
        text = self.pm.info()
        for tag in ("settings", "history", "thumb_cache", "scratch", "templates"):
            self.assertIn(tag, text)

    def test_settings_as_relative(self):
        rel = self.pm.as_relative("settings", PathMode.USER_CONFIG)
        self.assertEqual(rel, Path("settings.json"))


# ===========================================================================
#  18. [SCENARIO] ETL pipeline
# ===========================================================================

class TestETLPipelineScenario(unittest.TestCase):
    """
    An ETL job with:
        etl_in   → PROJ_ABSOLUTE  (inputs exist in project)
        etl_out  → PROJ_ABSOLUTE  (outputs dir may or may not exist yet)
        report   → PROJ_ABSOLUTE  (will get timestamped on conflict)
    """

    def setUp(self):
        self.pm = _fresh_manager()
        self.tmpdir = Path(tempfile.mkdtemp())
        self.proj_root = self.tmpdir / "project"
        (self.proj_root / "data" / "inputs").mkdir(parents=True)
        (self.proj_root / "data" / "inputs" / "source.csv").write_text("id,value\n1,100")

        self.pm.set_proj_root(str(self.proj_root))
        self.pm.set_app_name("ETLTool")
        self.pm.register("etl_in",  "data/inputs",       PathMode.PROJ_ABSOLUTE)
        self.pm.register("etl_out", "data/outputs",      PathMode.PROJ_ABSOLUTE)
        self.pm.register("report",  "report.xlsx",       PathMode.PROJ_ABSOLUTE)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_etl_input_dir_exists(self):
        self.assertTrue(self.pm.exists("etl_in"))

    def test_etl_input_waterfall_prefers_proj(self):
        p = self.pm.get("etl_in", Waterfall.ETL_INPUT)
        self.assertEqual(p, (self.proj_root / "data" / "inputs").resolve())

    def test_etl_output_write_intent(self):
        """outputs/ not created yet; proj_root parent exists → WRITE passes."""
        path, trace = self.pm.get_with_trace(
            "etl_out",
            Waterfall.ETL_OUTPUT,
            intent=ResolveIntent.WRITE,
        )
        self.assertIsNotNone(path)
        self.assertTrue(trace.succeeded)

    def test_conflict_strategy_on_report(self):
        (self.proj_root / "report.xlsx").write_text("old")
        self.pm.set_default_conflict_strategy(TimestampSuffixStrategy())
        safe = self.pm.resolve_conflict("report")
        self.assertRegex(safe.stem, r"report_\d{8}_\d{6}")

    def test_etl_output_falls_back_to_temp_when_proj_unreachable(self):
        """A deeply nested non-existent output; last resort is SYSTEM_TEMP."""
        self.pm.register("deep_out", "a/b/c/d/e/out.parquet", PathMode.PROJ_ABSOLUTE)
        path, trace = self.pm.get_with_trace(
            "deep_out", Waterfall.ETL_OUTPUT, intent=ResolveIntent.WRITE,
        )
        self.assertIsNotNone(path)
        self.assertTrue(trace.succeeded)


# ===========================================================================
#  Entry point
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
