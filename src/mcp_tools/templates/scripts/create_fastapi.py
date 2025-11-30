import os
import sys
import argparse

def create_fastapi_project(project_name, target_dir):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    # requirements.txt
    with open(os.path.join(project_path, "requirements.txt"), "w") as f:
        f.write("fastapi\nuvicorn\n")

    # main.py
    main_py_content = """from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    with open(os.path.join(project_path, "main.py"), "w") as f:
        f.write(main_py_content)

    print(f"FastAPI project '{project_name}' created at {project_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a FastAPI project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    create_fastapi_project(args.project_name, args.target_dir)
