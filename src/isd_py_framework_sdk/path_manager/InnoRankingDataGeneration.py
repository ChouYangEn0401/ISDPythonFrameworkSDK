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
