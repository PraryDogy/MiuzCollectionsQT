from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu

from cfg import JsonData
from system.lang import Lng


# QMenu импортирован вместо base widgets UMenu, чтобы не было рекурсивного
# импорта и только для аннотации


class OpenInView(QAction):
	def __init__(self, rel_paths: list[str], parent_: QMenu):
		if len(rel_paths) > 1:
			end_text =  f" ({len(rel_paths)})"
		else:
			end_text = ""
		super().__init__(parent=parent_, text=f"{Lng.open}{end_text}")


class ScanerRestart(QAction):
	def __init__(self, parent: QMenu):
		super().__init__(parent=parent, text=Lng.scan_folder)


class WinInfoAction(QAction):
	def __init__(self, parent: QMenu):
		super().__init__(text=Lng.info, parent=parent)


class CopyPath(QAction):
	def __init__(self, parent: QMenu, total: int):
		if total > 1:
			text = f"{Lng.copy_filepaths}"
		else:
			text = f"{Lng.copy_filepath}"
		super().__init__(parent=parent, text=text)


class CopyName(QAction):
	def __init__(self, parent: QMenu, total: int):
		if total > 1:
			text = f"{Lng.copy_names}"
		else:
			text = f"{Lng.copy_name}"
		super().__init__(parent=parent, text=text)


class RevealInFinder(QAction):
	def __init__(self, parent: QMenu, total: int):
		text = f"{Lng.reveal_in_finder}"
		super().__init__(parent=parent, text=text)


class SetFav(QAction):
	def __init__(self, parent: QMenu, fav_value: int):
		if not fav_value:
			t = Lng.add_to_favorites
		else:
			t = Lng.remove_from_favorites
		super().__init__(parent=parent, text=t)


class Save(QAction):
	def __init__(self, parent: QMenu, total: int):
		if total > 1:
			text = f"{Lng.save_to_downloads}"
		else:
			text = f"{Lng.save_to_downloads}"
		super().__init__(parent=parent, text=text)


class RemoveFiles(QAction):
	def __init__(self, parent: QMenu, total: int):
		if total > 1:
			text_ = f"{Lng.delete}"
		else:
			text_ = f"{Lng.delete}"
		super().__init__(text_, parent)


class CopyFiles(QAction):
	def __init__(self, parent: QMenu, rel_paths: list[str]):
		if len(rel_paths) == 1:
			text = f"{Lng.copy_file}"
		else:
			text = F"{Lng.copy_files}"
		super().__init__(text=text, parent=parent)


class PasteFiles(QAction):
	def __init__(self, parent: QMenu):
		super().__init__(text=Lng.paste, parent=parent)


class UpdateThumbAction(QAction):
	def __init__(self, parent: QMenu, rel_paths: list[str]):
		if len(rel_paths) == 1:
			text = Lng.update_thumb
		else:
			text = Lng.update_thumbs
		super().__init__(text=text, parent=parent)


class ShowInFolder(QAction):
	def __init__(self, parent: QMenu):
		super().__init__(
			text=Lng.show_in_folder,
			parent=parent
		)


class CollageAction(QAction):
	def __init__(self, parent: QMenu):
		super().__init__(
			text=Lng.collage,
			parent=parent
		)