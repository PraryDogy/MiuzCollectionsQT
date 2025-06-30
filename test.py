from system.main_folder import MainFolder, MainFolderModel
import json
import jsonschema


shema = MainFolderModel.model_json_schema()

with open(MainFolder.json_file, "r", encoding="utf-8") as file:
    data = json.load(file)

for i in data:
    try:
        jsonschema.validate(instance=i, schema=shema)
    except Exception as e:
        print("error validate")