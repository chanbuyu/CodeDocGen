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

def analyze_code_files(root_dir, output_file):
    """分析代码文件并生成说明文档"""
    
    print("开始扫描Python文件...")
    py_files = list(Path(root_dir).rglob('*.py'))
    print(f"找到 {len(py_files)} 个Python文件")
    
    print("创建输出文件...")
    # 先写入文档头部
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('# 代码文件功能说明文档\n\n')
    
    for path in tqdm(py_files, desc="分析进度"):
        relative_path = path.relative_to(root_dir)
        print(f"\n开始处理文件: {relative_path}")
        
        try:
            print("  正在读取文件内容...")
            with open(path, 'r', encoding='utf-8') as code_file:
                content = code_file.read()
            
            print("  开始AI分析...")
            ai_analysis = get_ai_analysis(content, relative_path)
            
            print("  写入分析结果...")
            # 以追加模式打开文件写入当前分析结果
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f'## {relative_path}\n\n')
                f.write(f'文件路径: `{relative_path}`\n\n')
                f.write('### AI分析说明\n\n')
                # 移除 think 标签及其内容
                cleaned_analysis = ai_analysis
                if '<think>' in ai_analysis and '</think>' in ai_analysis:
                    start_idx = ai_analysis.find('<think>')
                    end_idx = ai_analysis.find('</think>') + len('</think>')
                    cleaned_analysis = ai_analysis[:start_idx] + ai_analysis[end_idx:]
                f.write(f'{cleaned_analysis}\n\n')
                f.write('---\n\n')
                f.flush()  # 确保内容立即写入磁盘
            
            print("  分析结果已保存")
            print("  等待2秒后继续下一个文件...")
            time.sleep(2)
            
        except Exception as e:
            print(f"  处理文件时出错: {str(e)}")
            # 错误信息也以追加模式写入
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f'## {relative_path} (处理出错)\n\n')
                f.write(f'处理文件时出错: {str(e)}\n\n---\n\n')
                f.flush()
            continue

if __name__ == '__main__':
    # 获取项目根目录：优先使用命令行参数，否则使用当前目录
    project_root = sys.argv[1] if len(sys.argv) > 1 else '.'  # 默认使用当前目录
    output_path = 'code_documentation.md'
    
    print(f'正在分析项目目录: {os.path.abspath(project_root)}')
    analyze_code_files(project_root, output_path)
    print(f'文档已生成: {output_path}') 