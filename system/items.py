from typing import Literal


class CopyItem:
    def __init__(self, src_dir: str, dst_dir: str, src_urls: list[str], is_search: bool, is_cut: bool):
        super().__init__()
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self.src_urls = src_urls
        self.is_search = is_search
        self.is_cut = is_cut

        self.current_size: int = 0
        self.total_size: int = 0
        self.current_count: int = 0
        self.total_count: int = 0
        self.dst_urls: list[str] = []
        self.msg: Literal["", "error", "need_replace", "replace_one", "replace_all", "finished"]