import os
import sys
import argparse

def create_flask_project(project_name, target_dir):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, "templates"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "static"), exist_ok=True)

    # requirements.txt
    with open(os.path.join(project_path, "requirements.txt"), "w") as f:
        f.write("flask\n")

    # app.py
    app_py_content = """from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
"""
    with open(os.path.join(project_path, "app.py"), "w") as f:
        f.write(app_py_content)

    # templates/index.html
    index_html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask App</title>
</head>
<body>
    <h1>Hello from Flask!</h1>
</body>
</html>
"""
    with open(os.path.join(project_path, "templates", "index.html"), "w") as f:
        f.write(index_html_content)

    print(f"Flask project '{project_name}' created at {project_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Flask project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    create_flask_project(args.project_name, args.target_dir)
