import os
from pathlib import Path
import time
import requests  # Add this import
import json     # Add this import
from tqdm import tqdm  # 添加进度条支持
import sys

# Replace OpenAI client setup with DMX API configuration
url = "https://www.dmxapi.com/v1/chat/completions"
headers = {
    "Accept": "application/json",
    "Authorization": "sk-8eGPnYVR6PxQqRSQpMu5tOOkpjMGZpYQMaAZ2ETtMQuceJwm",
    "User-Agent": "DMXAPI/1.0.0 (https://www.dmxapi.com)",
    "Content-Type": "application/json",
}

def get_ai_analysis(code_content, filename):
    """使用DMX API分析代码功能"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"    准备分析文件: {filename}")
            
            payload = {
                "model": "deepseek-r1",
                "stream": True,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"""简短解释下这份代码，要求必须说明它调用了哪些库 '{filename}' 。

                    代码内容如下：
                    {code_content}
                    """}
                ],
            }
            
            print(f"    正在调用API...")
            response = requests.post(url, headers=headers, json=payload, stream=True)
            
            print(f"    正在接收流式响应...")
            full_response = ""
            buffer = ""
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    buffer += chunk.decode("utf-8")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if line.strip() == "":
                            continue
                        if line.startswith("data: "):
                            data_line = line[len("data: "):].strip()
                            if data_line == "[DONE]":
                                break
                            else:
                                try:
                                    data = json.loads(data_line)
                                    delta = data["choices"][0]["delta"]
                                    content = delta.get("content", "")
                                    full_response += content
                                    print(content, end="", flush=True)
                                except json.JSONDecodeError:
                                    buffer = line + "\n" + buffer
                                    break
            
            print("\n    响应接收完成")
            return full_response
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"    尝试 {attempt + 1} 失败: {str(e)}，等待5秒后重试...")
                time.sleep(5)
                continue
            return f"AI分析失败 (已重试{max_retries}次): {str(e)}"

def analyze_code_files(file_paths, output_file, retry_failed_only=False):
    """分析指定的代码文件并生成说明文档"""
    
    print(f"准备分析 {len(file_paths)} 个文件...")
    
    # 创建或读取失败文件列表
    failed_files_path = 'failed_files.txt'
    failed_files = set()
    
    if retry_failed_only:
        # 如果是重试模式，则只处理之前失败的文件
        if os.path.exists(failed_files_path):
            with open(failed_files_path, 'r', encoding='utf-8') as f:
                failed_files = set(line.strip() for line in f.readlines())
            file_paths = [p for p in file_paths if str(p) in failed_files]
            print(f"重试模式：将处理 {len(file_paths)} 个之前失败的文件")
    
    if not retry_failed_only:
        if not os.path.exists(output_file):
            print("创建新的输出文件...")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('# 代码文件功能说明文档\n\n')
        else:
            print("输出文件已存在，将在文件末尾追加新的分析结果...")
    
    # 用于记录本次运行失败的文件
    current_failed_files = set()
    
    for path in tqdm(file_paths, desc="分析进度"):
        path = Path(path)
        print(f"\n开始处理文件: {path}")
        
        try:
            print("  正在读取文件内容...")
            with open(path, 'r', encoding='utf-8') as code_file:
                content = code_file.read()
            
            print("  开始AI分析...")
            ai_analysis = get_ai_analysis(content, path)
            
            print("  写入分析结果...")
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f'## {path}\n\n')
                f.write(f'文件路径: `{path}`\n\n')
                f.write('### AI分析说明\n\n')
                # 移除 think 标签及其内容
                cleaned_analysis = ai_analysis
                if '<think>' in ai_analysis and '</think>' in ai_analysis:
                    start_idx = ai_analysis.find('<think>')
                    end_idx = ai_analysis.find('</think>') + len('</think>')
                    cleaned_analysis = ai_analysis[:start_idx] + ai_analysis[end_idx:]
                f.write(f'{cleaned_analysis}\n\n')
                f.write('---\n\n')
                f.flush()
            
            print("  分析结果已保存")
            print("  等待2秒后继续下一个文件...")
            time.sleep(2)
            
        except Exception as e:
            print(f"  处理文件时出错: {str(e)}")
            current_failed_files.add(str(path))
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f'## {path} (处理出错)\n\n')
                f.write(f'处理文件时出错: {str(e)}\n\n---\n\n')
                f.flush()
            continue
    
    # 保存失败的文件列表
    with open(failed_files_path, 'w', encoding='utf-8') as f:
        for failed_file in current_failed_files:
            f.write(f'{failed_file}\n')
    
    if current_failed_files:
        print(f"\n本次运行中有 {len(current_failed_files)} 个文件处理失败")
        print(f"失败文件列表已保存到: {failed_files_path}")

if __name__ == '__main__':
    # 可以直接在这里指定要分析的文件列表
    files_to_analyze = [
        # 在这里添加要分析的文件路径，例如：
        # "path/to/your/file1.py",
        # "path/to/your/file2.py",
        "generate_tree.py",
    ]
    
    # 如果命令行提供了参数，则使用命令行参数
    if len(sys.argv) > 1:
        file_paths = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    else:
        file_paths = files_to_analyze
        
    if not file_paths:
        print("请提供要分析的文件路径")
        print("方法1: 直接在代码中的 files_to_analyze 列表中添加文件路径")
        print("方法2: 通过命令行参数指定: python code_analyzer_manual.py <file_path1> [file_path2 ...]")
        sys.exit(1)
    
    output_path = 'code_documentation.md'
    retry_mode = '--retry' in sys.argv
    
    print(f'准备分析以下文件:')
    for path in file_paths:
        print(f'  - {os.path.abspath(path)}')
    
    analyze_code_files(file_paths, output_path, retry_failed_only=retry_mode)
    print(f'文档已生成: {output_path}') 