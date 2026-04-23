from pathlib import Path

class InnoRankingDataGeneration:
    ROOT_DIR: Path = Path(__file__).resolve().parent.parent  # 預設 ROOT_DIR

    @classmethod
    def set_root_dir(cls, new_root: Path | str):
        cls.ROOT_DIR = Path(new_root).resolve()

    @classmethod
    def get_inputs_path(cls) -> Path:
        return cls.ROOT_DIR / "data" / "inputs"
    @classmethod
    def get_outputs_path(cls) -> Path:
        return cls.ROOT_DIR / "data" / "outputs"
    @classmethod
    def get_pris_data(cls, mode: str = None) -> Path:
        path = cls.ROOT_DIR / "data/inputs/pris_data"
        if mode is not None:
            path = path / mode
        return path
    @classmethod
    def get_builtin_data(cls) -> Path:
        return cls.ROOT_DIR / "data/inputs/builtin_reference_data"
    @classmethod
    def get_outer_source_data(cls) -> Path:
        return cls.ROOT_DIR / "data/inputs/outer_sources_data"
    @classmethod
    def get_self_gen(cls) -> Path:
        return cls.ROOT_DIR / "data/inputs/self_gen"




# from abc import ABC, abstractmethod
#
# # Corrected abstract core class definition
# class InnoRankingExcelExporterBase(ABC):
#     def __init__(self):
#         pass
#     @abstractmethod
#     def get_output_sheets_name(self):
#         # This should be implemented by subclasses
#         return []
#     @abstractmethod
#     def get_sheets_to_process(self):
#         # This should be implemented by subclasses
#         return []


# Example utility function to return sheet names
def get_major_field_list():
    return ["Electrical engineering", "Instruments", "Chemistry", "Mechanical engineering", "Other fields"]
def get_all_continents_list():
    return ['SA', 'NA', 'AF', 'AS', 'OC', 'EU']


# ---------------------------------------------------------------------------
# 新版寫法示範（僅供參考，不替換舊 class）
# 使用 SingletonPathManager + 標準 API
# ---------------------------------------------------------------------------

from isd_py_framework_sdk.path_manager import (
    SingletonPathManager, PathMode, Waterfall, ResolveIntent,
    IncrementSuffixStrategy,
)
def setup_inno_ranking_paths(proj_root_file: str) -> None:
    """在程式入口呼叫一次（如 main.py），之後所有模組直接 pm.get(tag) 即可。

    This function registers all tags with explicit anchors (no defaults).
    Use `pm = SingletonPathManager()` elsewhere to fetch paths.
    """
    pm = SingletonPathManager()
    pm.set_proj_root(proj_root_file, levels_up=2)
    pm.set_app_name("InnoRanking")

    # 必須顯式指定 anchor（不接受預設）
    pm.register("data_in", "data/inputs", PathMode.PROJ_ABSOLUTE,
                description="所有輸入資料的根目錄")

    pm.register("pris_data", "data/inputs/pris_data", PathMode.PROJ_ABSOLUTE,
                description="PRIS 原始資料（含子模組目錄）")

    pm.register("builtin_ref", "data/inputs/builtin_reference_data", PathMode.PROJ_ABSOLUTE,
                description="內建參考資料（隨程式碼版控）")

    pm.register("outer_src", "data/inputs/outer_sources_data", PathMode.PROJ_ABSOLUTE,
                description="外部來源資料（不版控）")

    pm.register("self_gen", "data/inputs/self_gen", PathMode.PROJ_ABSOLUTE,
                description="程式自行產生的中間結果")

    pm.register("data_out", "data/outputs", PathMode.PROJ_ABSOLUTE,
                description="所有輸出結果的根目錄")


class InnoRankingPathsAdapter:
    """Adapter exposing the old API while using the new PathManager.

    Usage:
        adapter = InnoRankingPathsAdapter()
        adapter.setup(__file__)
        inputs = adapter.get_inputs_path()
    """

    def __init__(self) -> None:
        self.pm = SingletonPathManager()

    def setup(self, proj_root_file: str) -> None:
        setup_inno_ranking_paths(proj_root_file)

    def get_inputs_path(self) -> Path:
        return self.pm.get("data_in")

    def get_outputs_path(self) -> Path:
        return self.pm.get("data_out")

    def get_pris_data(self, mode: str | None = None) -> Path:
        base = self.pm.get("pris_data")
        return base / mode if mode else base

    def get_builtin_data(self) -> Path:
        return self.pm.get("builtin_ref")

    def get_outer_source_data(self) -> Path:
        return self.pm.get("outer_src")

    def get_self_gen(self) -> Path:
        return self.pm.get("self_gen")


# ── 取路徑的方式（取代原本的 @classmethod）──────────────────
#
# 舊：InnoRankingDataGeneration.get_inputs_path()
# 新：pm.get("data_in")
#
# 舊：InnoRankingDataGeneration.get_pris_data("2024")
# 新：pm.get("pris_data") / "2024"
#
# 舊：InnoRankingDataGeneration.get_outputs_path()
# 新：pm.get("data_out")
#
# ── 衝突安全輸出（新版額外能力）───────────────────────────────
#
# report = pm.resolve_conflict("data_out") / "result.xlsx"
# report = pm.resolve_conflict("data_out", strategy=IncrementSuffixStrategy()) / "result.xlsx"
#
# ── PyInstaller 部署模式（新版額外能力）──────────────────────
#
# pm.get("builtin_ref", Waterfall.EXE_PREFER_BUNDLED)
#   → 先找 sys._MEIPASS 內部，找不到再找 exe 旁邊，再找 proj_root
#
# ── 除錯（新版額外能力）──────────────────────────────────────
#
# path, trace = pm.get_with_trace("builtin_ref", Waterfall.EXE_PREFER_BUNDLED)
# print(trace)
#   → 印出每個 waterfall 步驟的 ✓/✗ 以及最終結果
