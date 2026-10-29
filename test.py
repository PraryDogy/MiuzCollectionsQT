import subprocess

script = '''
set appNames to {}
set searchFolders to {"/Applications", "/Applications/Utilities", "/System/Applications", "/System/Applications/Utilities", "/System/Library/CoreServices"}
tell application "Finder"
    repeat with folderPath in searchFolders
        set theFolder to POSIX file folderPath as alias
        set appNames to appNames & (name of every application file of folder theFolder)
    end repeat
end tell
set AppleScript's text item delimiters to linefeed
return appNames as text
'''

result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)

if result.returncode != 0:
    print("Ошибка:", result.stderr.strip())
else:
    apps = set()
    for line in result.stdout.splitlines():
        name = line.strip()
        if name.endswith(".app"):
            name = name[:-4]
        if name:
            apps.add(name)

    for app in sorted(apps, key=str.lower):
        print(app)