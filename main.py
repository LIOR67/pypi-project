import requests
import tarfile
import os
import ast
import toml # Needs to install before running


# Get package from PyPI
def get_package(package):
    url = f"https://pypi.org/pypi/{package}/json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    print("Package not found.")
    return None


# returns latest version string
def pack_version(data):
    return data["info"]["version"]


# Download .tar.gz or .whl file
def download_file(data):
    chosen_file = None
    for file in data["urls"]:
        if file["filename"].endswith("tar.gz"):
            chosen_file = file
            break
    if not chosen_file:
        for file in data["urls"]:
            if file["filename"].endswith(".whl"):
                chosen_file = file
                break
    if not chosen_file:
        print("No downloadable file found.")
        return None

    url = chosen_file["url"]
    filename = url.split("/")[-1]
    print(f"Downloading: {filename}")
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)
    print(f"Saved as: {filename}")
    return filename


# Extract tar.gz file
def extract_tar_file(filename, extract_to="extracted_package"):
    if not filename.endswith("tar.gz"):
        print("Not a .tar.gz file.")
        return None

    os.makedirs(extract_to, exist_ok=True)
    with tarfile.open(filename, "r:gz") as tar:
        tar.extractall(path=extract_to)
    print(f"Extracted to: {extract_to}")
    return extract_to


# Find setup.py, pyproject.toml, or requirements.txt
def find_dependency_file(folder):
    for root, _, files in os.walk(folder):
        for target in ["setup.py", "pyproject.toml", "requirements.txt"]:
            if target in files:
                return os.path.join(root, target)
    return None


# Extract install_requires from setup.py
def extract_dependencies_from_setup(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        setup_code = f.read()
    tree = ast.parse(setup_code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == "setup":
            for keyword in node.keywords:
                if keyword.arg == "install_requires" and isinstance(keyword.value, ast.List):
                    return [ast.literal_eval(item) for item in keyword.value.elts]
    return []


# Extract dependencies from pyproject.toml
def extract_dependencies_from_pyproject(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        toml_data = toml.load(f)
    if "project" in toml_data and "dependencies" in toml_data["project"]:
        return toml_data["project"]["dependencies"]
    return []


# Extract dependencies from requirements.txt
def extract_dependencies_from_requirements(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


# Main interactive menu
while True:
    print("\nPYPI Package Scraper")
    print("1. Analyze package")
    print("2. Exit")
    choice = input("Enter choice: ")

    if choice == "1":
        package = input("Enter package name: ").strip()
        data = get_package(package)
        if not data:
            continue

        version = pack_version(data)
        print(f"Latest version: {version}")

        filename = download_file(data)
        if not filename:
            continue

        extracted_path = extract_tar_file(filename)
        if not extracted_path:
            continue

        dep_file = find_dependency_file(extracted_path)
        if not dep_file:
            print("No dependency file found.")
            continue

        print(f"Found dependency file: {dep_file}")

        if dep_file.endswith("setup.py"):
            deps = extract_dependencies_from_setup(dep_file)
            print("Dependencies (setup.py):", deps)

        elif dep_file.endswith("pyproject.toml"):
            deps = extract_dependencies_from_pyproject(dep_file)
            print("Dependencies (pyproject.toml):", deps)

        elif dep_file.endswith("requirements.txt"):
            deps = extract_dependencies_from_requirements(dep_file)
            print("Dependencies (requirements.txt):", deps)

        else:
            print("Unsupported file format.")

    elif choice == "2":
        print("Exiting.")
        break

    else:
        print("Invalid choice.")
