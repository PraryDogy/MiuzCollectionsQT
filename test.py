from system.json_validator import JsonValidator
from system.main_folder import MainFolder, MainFolderListModel, MainFolderItemModel

src = MainFolder.json_file
model = MainFolderListModel
obj = MainFolder

validator = JsonValidator(src, obj, model)
json_data = validator.load_json_data(src)
for k, v in json_data.items():
    for i in v:
        validator = JsonValidator