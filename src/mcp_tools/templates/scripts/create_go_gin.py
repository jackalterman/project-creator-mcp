import os
import sys
import argparse
import subprocess

def create_go_gin_project(project_name, target_dir):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    # main.go
    main_go_content = """package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()
	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "Hello World",
		})
	})
	r.Run() // listen and serve on 0.0.0.0:8080
}
"""
    with open(os.path.join(project_path, "main.go"), "w") as f:
        f.write(main_go_content)

    # Initialize go mod
    try:
        subprocess.run(["go", "mod", "init", project_name], cwd=project_path, check=True)
        # We don't run go get here to avoid network dependency during scaffold if possible, 
        # but for go.mod to be valid with imports, we might need it. 
        # However, user can run 'go mod tidy' later.
        print("Go module initialized.")
    except Exception as e:
        print(f"Warning: Failed to initialize go module: {e}")

    print(f"Go Gin project '{project_name}' created at {project_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Go Gin project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    create_go_gin_project(args.project_name, args.target_dir)
