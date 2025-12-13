import os
import argparse

def create_jupyter_project(project_name, target_dir):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, "notebooks"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "data"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "scripts"), exist_ok=True)

    # requirements.txt
    with open(os.path.join(project_path, "requirements.txt"), "w") as f:
        f.write("jupyterlab\npandas\nmatplotlib\nscikit-learn\nseaborn\n")

    # notebooks/analysis.ipynb
    # Creating a minimal valid notebook JSON
    notebook_content = """{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Data Analysis\\n",
    "\\n",
    "Welcome to your new Data Science project!"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\\n",
    "import matplotlib.pyplot as plt\\n",
    "import seaborn as sns\\n",
    "\\n",
    "%matplotlib inline"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}"""
    with open(os.path.join(project_path, "notebooks", "analysis.ipynb"), "w") as f:
        f.write(notebook_content)

    print(f"Jupyter Data Science project '{project_name}' created at {project_path}")
    print("Run 'jupyter lab' to start the environment.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Jupyter Data Science project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    create_jupyter_project(args.project_name, args.target_dir)
