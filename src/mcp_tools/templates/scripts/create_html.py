import os
import sys
import argparse

def create_html_project(project_name, target_dir, single_file=False):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    if single_file:
        content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Modern Project</title>
    <style>
        /* Modern CSS Reset */
        *, *::before, *::after {
            box_sizing: border_box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
            padding: 2rem;
            background-color: #f9fafb;
            color: #111827;
        }
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: #1f2937;
        }
        p {
            margin-bottom: 1rem;
            color: #4b5563;
        }
    </style>
</head>
<body>
    <main>
        <h1>Hello World</h1>
        <p>Welcome to your modern HTML project.</p>
    </main>
    <script type="module">
        console.log("Hello from Modern JavaScript!");
    </script>
</body>
</html>
"""
        with open(os.path.join(project_path, "index.html"), "w") as f:
            f.write(content)
    else:
        # index.html
        index_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Modern Project</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <main>
        <h1>Hello World</h1>
        <p>Welcome to your modern HTML project.</p>
    </main>
    <script type="module" src="script.js"></script>
</body>
</html>
"""
        with open(os.path.join(project_path, "index.html"), "w") as f:
            f.write(index_content)

        # style.css
        css_content = """/* Modern CSS Reset */
*, *::before, *::after {
    box_sizing: border_box;
    margin: 0;
    padding: 0;
}

body {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    padding: 2rem;
    background-color: #f9fafb;
    color: #111827;
}

h1 {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    color: #1f2937;
}

p {
    margin-bottom: 1rem;
    color: #4b5563;
}
"""
        with open(os.path.join(project_path, "style.css"), "w") as f:
            f.write(css_content)

        # script.js
        js_content = """console.log("Hello from Modern JavaScript!");
"""
        with open(os.path.join(project_path, "script.js"), "w") as f:
            f.write(js_content)

    print(f"HTML project '{project_name}' created at {project_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an HTML project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    parser.add_argument("--type", choices=["single", "separate"], default="separate", help="Project type")
    args = parser.parse_args()

    create_html_project(args.project_name, args.target_dir, single_file=(args.type == "single"))
