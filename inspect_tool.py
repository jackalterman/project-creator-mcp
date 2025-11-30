from src.mcp_tools.file_system_tools import create_file

print(f"Type: {type(create_file)}")
print(f"Dir: {dir(create_file)}")
try:
    print(f"Wrapped: {create_file.fn}")
except AttributeError:
    print("No .fn attribute")
try:
    print(f"Wrapped: {create_file.__wrapped__}")
except AttributeError:
    print("No .__wrapped__ attribute")
