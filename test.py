from system.json_validator import JsonValidator
from system.main_folder import MainFolder, MainFolderListModel

src = MainFolder.json_file
model = MainFolderListModel
obj = MainFolder

validator = JsonValidator(src, obj, model)
res = validator.get_validated_data()
print(res)