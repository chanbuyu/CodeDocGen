from pathlib import Path
import io
import sys

def generate_tree(directory, prefix="", is_last=True, output_buffer=None):
    # Get the directory path
    path = Path(directory)
    
    # Skip .git directory
    if path.name == '.git':
        return
    
    # Get the directory name or full path
    output = prefix + "├── " if not is_last else prefix + "└── "
    output += path.name
    
    # Print to console and write to buffer
    print(output)
    if output_buffer is not None:
        output_buffer.write(output + "\n")
    
    # If it's a directory, process its contents
    if path.is_dir():
        # Get all items in directory
        items = list(path.iterdir())
        items.sort()  # Sort items alphabetically
        
        # Process each item
        for i, item in enumerate(items):
            # Determine if this is the last item
            is_last_item = (i == len(items) - 1)
            
            # Create new prefix for children
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            # Recursively process item
            generate_tree(item, new_prefix, is_last_item, output_buffer)

def print_tree(root_path, output_file=None):
    # Set console output encoding to UTF-8
    if sys.platform.startswith('win'):
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Create string buffer if output file is specified
    output_buffer = io.StringIO() if output_file else None
    
    # Print and write the root
    print(".")
    if output_buffer:
        output_buffer.write(".\n")
    
    path = Path(root_path)
    
    # Get all items in root directory
    items = list(path.iterdir())
    items.sort()  # Sort items alphabetically
    
    # Process each item
    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        generate_tree(item, "", is_last, output_buffer)
    
    # If output file is specified, append to it
    if output_file:
        with open(output_file, 'a', encoding='utf-8') as f:  # Added UTF-8 encoding
            f.write("\n## 项目目录结构\n\n```\n")
            f.write(output_buffer.getvalue())
            f.write("```\n")
        
        output_buffer.close()

if __name__ == "__main__":
    # Replace with your directory path
    root_directory = "."
    documentation_file = "code_documentation.md"
    print_tree(root_directory, documentation_file) 