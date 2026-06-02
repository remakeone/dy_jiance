def extract_lines_to_new_file(input_file_path: str, output_file_path: str, start_line: int, end_line: int) -> bool:
    """
    从输入文件中提取指定行范围，并保存到新文件

    Args:
        input_file_path: 输入文件路径
        output_file_path: 输出文件路径
        start_line: 起始行号（从1开始，包含）
        end_line: 结束行号（包含）

    Returns:
        bool: 操作是否成功
    """
    try:
        # 验证行号范围
        if start_line < 1:
            print("错误: 起始行号必须大于等于1")
            return False

        if end_line < start_line:
            print("错误: 结束行号不能小于起始行号")
            return False

        # 读取文件并截取指定行
        extracted_lines = []
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

            # 检查行号是否超出文件范围
            if start_line > len(lines):
                print(f"错误: 起始行号({start_line})超出文件行数({len(lines)})")
                return False

            if end_line > len(lines):
                print(f"警告: 结束行号({end_line})超出文件行数({len(lines)})，将截取到文件末尾")
                end_line = len(lines)

            # 提取指定行（注意行号从1开始，索引从0开始）
            extracted_lines = lines[start_line - 1:end_line]

        # 写入新文件
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.writelines(extracted_lines)

        print(f"成功截取行 {start_line}-{end_line} 到文件: {output_file_path}")
        print(f"共截取 {len(extracted_lines)} 行")
        return True

    except FileNotFoundError:
        print(f"错误: 找不到输入文件 {input_file_path}")
        return False
    except Exception as e:
        print(f"处理文件时出错: {e}")
        return False


def extract_lines_with_preview(input_file_path: str, output_file_path: str, start_line: int, end_line: int,
                               preview_lines: int = 5) -> bool:
    """
    从输入文件中提取指定行范围，并保存到新文件，同时提供预览

    Args:
        input_file_path: 输入文件路径
        output_file_path: 输出文件路径
        start_line: 起始行号（从1开始，包含）
        end_line: 结束行号（包含）
        preview_lines: 预览行数

    Returns:
        bool: 操作是否成功
    """
    try:
        # 先执行截取操作
        success = extract_lines_to_new_file(input_file_path, output_file_path, start_line, end_line)

        if success:
            # 显示预览
            print(f"\n前{preview_lines}行预览:")
            print("-" * 50)

            with open(output_file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if i > preview_lines:
                        break
                    print(f"{i:3d}: {line.rstrip()}")

            # 显示文件信息
            with open(output_file_path, 'r', encoding='utf-8') as f:
                total_lines = sum(1 for _ in f)

            print("-" * 50)
            print(f"文件总行数: {total_lines}")

        return success

    except Exception as e:
        print(f"预览时出错: {e}")
        return False


def get_file_info(file_path: str) -> dict:
    """
    获取文件基本信息

    Args:
        file_path: 文件路径

    Returns:
        dict: 包含文件信息的字典
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        return {
            'total_lines': len(lines),
            'first_few_lines': lines[:5] if len(lines) > 0 else [],
            'last_few_lines': lines[-5:] if len(lines) > 0 else []
        }
    except Exception as e:
        print(f"获取文件信息时出错: {e}")
        return {}


def interactive_extract():
    """
    交互式文件截取工具
    """
    input_file = input("请输入源文件路径: ").strip()

    # 获取文件信息
    file_info = get_file_info(input_file)
    if not file_info:
        return

    print(f"\n文件 '{input_file}' 信息:")
    print(f"总行数: {file_info['total_lines']}")

    if file_info['first_few_lines']:
        print("\n前5行预览:")
        for i, line in enumerate(file_info['first_few_lines'], 1):
            print(f"{i:3d}: {line.rstrip()}")

    if file_info['last_few_lines']:
        print("\n后5行预览:")
        for i, line in enumerate(file_info['last_few_lines'], file_info['total_lines'] - 4):
            print(f"{i:3d}: {line.rstrip()}")

    # 获取截取范围
    try:
        start_line = int(input(f"\n请输入起始行号 (1-{file_info['total_lines']}): "))
        end_line = int(input(f"请输入结束行号 ({start_line}-{file_info['total_lines']}): "))

        # 生成输出文件名
        import os
        base_name = os.path.splitext(input_file)[0]
        ext = os.path.splitext(input_file)[1]
        output_file = f"{base_name}_lines_{start_line}_{end_line}{ext}"

        # 执行截取
        extract_lines_with_preview(input_file, output_file, start_line, end_line)

    except ValueError:
        print("错误: 请输入有效的数字")
    except Exception as e:
        print(f"处理时出错: {e}")


# 使用示例
if __name__ == "__main__":
    # 方法1: 直接调用函数
    input_file = r"C:\Users\remake\Documents\Tencent Files\2567040897\FileRecv\log_new.2025-11-23_20-42-02_911228.log"  # 替换为你的日志文件路径
    output_file = "extracted_log.log"  # 输出文件路径
    start_line = 218289  # 起始行号
    end_line = 312991  # 结束行号

    # 基本用法
    extract_lines_to_new_file(input_file, output_file, start_line, end_line)

    # 带预览的用法
    # extract_lines_with_preview(input_file, output_file, start_line, end_line)

    # 方法2: 交互式使用
    # interactive_extract()