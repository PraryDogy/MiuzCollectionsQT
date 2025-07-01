import json
from typing import List
from pydantic import BaseModel, RootModel



class MainFolderItemModel(BaseModel):
    name: str
    paths: List[str]
    stop_list: List[str]
    curr_path: str


class MainFolderListModel(BaseModel):
    main_folder_list: List[MainFolderItemModel]


def load_and_validate(filepath: str) -> List[MainFolderListModel]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json_data: dict = json.load(f)
            return MainFolderListModel(**json_data)
    except Exception as e:
        print(e)
        return None

src = "/Users/Loshkarev/Documents/_Projects/MiuzCollectionsQT/main_folder.json"
folders = load_and_validate(src)