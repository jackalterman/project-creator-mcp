import os
import argparse

def create_typer_project(project_name, target_dir):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    # requirements.txt
    with open(os.path.join(project_path, "requirements.txt"), "w") as f:
        f.write("typer[all]\nrich\n")

    # main.py
    main_py_content = """import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def hello(name: str):
    \"\"\"
    Say hello to NAME.
    \"\"\"
    console.print(f"[bold green]Hello {name}![/bold green]")

@app.command()
def goodbye(name: str, formal: bool = False):
    \"\"\"
    Say goodbye to NAME.
    \"\"\"
    if formal:
        console.print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        console.print(f"Bye {name}!")

if __name__ == "__main__":
    app()
"""
    with open(os.path.join(project_path, "main.py"), "w") as f:
        f.write(main_py_content)

    print(f"Typer CLI project '{project_name}' created at {project_path}")
    print("Run 'python main.py --help' to see usage.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Typer CLI project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    create_typer_project(args.project_name, args.target_dir)
