
import os
import argparse

def create_textual_project(project_name, target_dir):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    # requirements.txt
    with open(os.path.join(project_path, "requirements.txt"), "w") as f:
        f.write("textual\n")

    # tcss (styles)
    tcss_content = """
Screen {
    layout: grid;
    grid-size: 2;
    grid-gutter: 2;
    padding: 2;
}

#sidebar {
    dock: left;
    width: 20%;
    height: 100%;
    background: $panel;
    border-right: vkey $accent;
}

#body {
    width: 100%;
    height: 100%;
    content-align: center middle;
}

Header {
    dock: top;
}

Footer {
    dock: bottom;
}
"""
    with open(os.path.join(project_path, "styles.tcss"), "w") as f:
        f.write(tcss_content)

    # app.py
    app_py_content = """from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static, Button

class TextualApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Sidebar", id="sidebar"),
            Container(
                Static("Welcome to your modern TUI app!", id="welcome"),
                Button("Click Me!", variant="primary", id="btn_click"),
                id="body"
            )
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_click":
            self.notify("Button clicked!")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

if __name__ == "__main__":
    app = TextualApp()
    app.run()
"""
    with open(os.path.join(project_path, "app.py"), "w") as f:
        f.write(app_py_content)

    print(f"Textual TUI project '{project_name}' created at {project_path}")
    print("Run 'python app.py' to start the TUI.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Textual TUI project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    create_textual_project(args.project_name, args.target_dir)
