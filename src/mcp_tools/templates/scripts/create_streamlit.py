import os
import argparse

def create_streamlit_project(project_name, target_dir):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, ".streamlit"), exist_ok=True)

    # requirements.txt
    with open(os.path.join(project_path, "requirements.txt"), "w") as f:
        f.write("streamlit\npandas\nnumpy\n")

    # app.py
    app_py_content = """import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title=f"Hello {project_name}",
    page_icon=":wave:",
)

st.title("Welcome to Streamlit! :wave:")

st.markdown(
    \"\"\"
    Streamlit is an open-source app framework built specifically for
    Machine Learning and Data Science projects.
    \"\"\"
)

if st.button('Click me'):
    st.write('You clicked the button!')

st.header("Sample Data")
chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['a', 'b', 'c']
)

st.line_chart(chart_data)
"""
    with open(os.path.join(project_path, "app.py"), "w", encoding='utf-8') as f:
        f.write(app_py_content.replace("{project_name}", project_name))

    # .streamlit/config.toml
    config_toml_content = """[theme]
primaryColor = "#F63366"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
"""
    with open(os.path.join(project_path, ".streamlit", "config.toml"), "w") as f:
        f.write(config_toml_content)

    print(f"Streamlit project '{project_name}' created at {project_path}")
    print("Run 'streamlit run app.py' to start the server.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Streamlit project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    create_streamlit_project(args.project_name, args.target_dir)
