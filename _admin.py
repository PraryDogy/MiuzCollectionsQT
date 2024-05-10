import subprocess
import os


print("Choose py ver: 3.10, 3.11")
ver: str = input()

if ver not in ("3.10", "3.11"):
    raise Exception("3.10 or 3.11")

# Команда для создания виртуального окружения
if not os.path.exists("env"):
    venv_command = f"python{ver} -m venv env"
    subprocess.run(venv_command, shell=True, check=True)

# Команда для активации виртуального окружения
activate_command = ". env/bin/activate"
subprocess.run(activate_command, shell=True, check=True)

# Команда для обновления pip
pip_upgrade_command = "pip install --upgrade pip"
subprocess.run(pip_upgrade_command, shell=True, check=True)

# Команда для установки обновлений для pip, setuptools и wheel
pip_setuptools_wheel_command = "pip install --upgrade pip setuptools wheel"
subprocess.run(pip_setuptools_wheel_command, shell=True, check=True)



