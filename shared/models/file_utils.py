def save_file(file_path: str, content: str) -> None:
    """
    Save content to a file.

    Args:
        file_path (str): The path to the file.
        content (str): The content to write to the file.
    """
    with open(file_path, 'w') as f:
        f.write(content)