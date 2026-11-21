import project_builder

NEW_TOOLS = [
    "search_files",
    "str_replace_in_file", "apply_edits", "move_path",
    "list_trash", "restore_from_trash",
    "create_checkpoint", "list_checkpoints", "restore_checkpoint",
    "run_checks",
]


def test_entrypoint_exposes_all_new_tools():
    missing = [name for name in NEW_TOOLS if not hasattr(project_builder, name)]
    assert not missing, f"project_builder.py does not import: {missing}"
