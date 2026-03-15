import os, re
import argparse
import subprocess
import chardet
import functools
import os.path as op
from PIL import Image
from pathlib2 import Path
from shutil import copyfile
GITHUB_REPO_PREFIX = "https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/"
COMPRESS_THRESHOLD = 5e5 

def process_for_zhihu(input_file, current_args):
    current_args.input = Path(input_file)
    current_args.file_parent = str(current_args.input.parent)
    current_args.used_images = []
    image_folder_path = op.join(current_args.current_script_data_path, current_args.input.stem)
    if not op.exists(image_folder_path):
        os.makedirs(image_folder_path)
    current_args.image_folder_path = image_folder_path
    if current_args.encoding is None:
        with open(str(current_args.input), 'rb') as f:
            s = f.read()
            chatest = chardet.detect(s)
            encoding = chatest['encoding']
    else:
        encoding = current_args.encoding

    print(f"--- Processing: {current_args.input.name} (Encoding: {encoding}) ---")

    with open(str(current_args.input), "r", encoding=encoding) as f:
        lines = f.read()
        lines = image_ops(lines, current_args)
        lines = formula_ops(lines)
        lines = table_ops(lines)
        
        output_path = op.join(current_args.current_script_data_path, current_args.input.stem + "_for_zhihu.md")
        with open(output_path, "w+", encoding=encoding) as fw:
            fw.write(lines)
    
    cleanup_image_folder(current_args)


def formula_ops(_lines):
    _lines = re.sub('((.*?)\$\$)(\s*)?([\s\S]*?)(\$\$)\n', '\n<img src="https://www.zhihu.com/equation?tex=\\4" alt="\\4" class="ee_img tr_noresize" eeimg="1">\n', _lines)
    _lines = re.sub('(\$)(?!\$)(.*?)(\$)', ' <img src="https://www.zhihu.com/equation?tex=\\2" alt="\\2" class="ee_img tr_noresize" eeimg="1"> ', _lines)
    return _lines

def rename_image_ref(m, current_args, original=True):
    ori_path = m.group(2) if original else m.group(1)
    try:
        if op.exists(ori_path):
            full_img_path = ori_path
            img_stem = Path(full_img_path).stem
            img_suffix = Path(full_img_path).suffix
            img_name_new = img_stem + img_suffix
            
            # ���ͬ����ͻ
            if op.exists(op.join(current_args.image_folder_path, img_name_new)):
                i = 1
                while op.exists(op.join(current_args.image_folder_path, img_name_new)):
                    img_name_new = f"{img_stem}_{i}{img_suffix}"
                    i += 1
            
            copyfile(full_img_path, op.join(current_args.image_folder_path, img_name_new))
            full_img_path = op.join(current_args.image_folder_path, img_name_new)
        else:
            full_img_path = op.join(current_args.file_parent, ori_path)
            if not op.exists(full_img_path):
                return m.group(0)
    except OSError:
        return m.group(0)

    if op.getsize(full_img_path) > COMPRESS_THRESHOLD and current_args.compress:
        full_img_path = reduce_single_image_size(full_img_path)
    
    image_ref_name = Path(full_img_path).name
    current_args.used_images.append(image_ref_name)
    
    if original:
        return "![" + m.group(1) + "](" + GITHUB_REPO_PREFIX + current_args.input.stem + "/" + image_ref_name + ")"
    else:
        return '<img src="' + GITHUB_REPO_PREFIX + current_args.input.stem + "/" + image_ref_name + '"'

def cleanup_image_folder(current_args):
    actual_image_paths = [op.join(current_args.image_folder_path, i) for i in os.listdir(current_args.image_folder_path) if op.isfile(op.join(current_args.image_folder_path, i))]
    for image_path in actual_image_paths:
        if Path(image_path).name not in current_args.used_images:
            os.remove(str(image_path))

def image_ops(_lines, current_args):
    _lines = re.sub(r"\!\[(.*?)\]\((.*?)\)", functools.partial(rename_image_ref, current_args=current_args, original=True), _lines)
    _lines = re.sub(r'<img src="(.*?)"', functools.partial(rename_image_ref, current_args=current_args, original=False), _lines)
    return _lines

def table_ops(_lines):
    return re.sub("\|\n", r"|\n\n", _lines)

def reduce_single_image_size(image_path):
    output_path = Path(image_path).parent / (Path(image_path).stem + ".jpg")
    if op.exists(image_path):
        img = Image.open(image_path)
        if (img.size[0] > img.size[1] and img.size[0] > 1920):
            img = img.resize((1920, int(1920 * img.size[1] / img.size[0])), Image.ANTIALIAS)
        elif (img.size[1] > img.size[0] and img.size[1] > 1080):
            img = img.resize((int(1080 * img.size[0] / img.size[1]), 1080), Image.ANTIALIAS)
        img.convert('RGB').save(output_path, optimize=True, quality=85)
    return output_path

def git_ops(message="update files"):
    print("--- Pushing to GitHub ---")
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", message])
    subprocess.run(["git", "push", "-u", "origin", "master"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--compress', action='store_true', help='Compress images')
    parser.add_argument('-i', '--input', type=str, help='Path to file OR directory')
    parser.add_argument('-e', '--encoding', type=str, help='Encoding')
    args = parser.parse_args()

    if args.input is None:
        raise FileNotFoundError("Please provide an input path!")

    input_path = Path(args.input)
    args.current_script_data_path = str(Path(__file__).absolute().parent / 'Data')
    target_files = []
    if input_path.is_dir():
        print(f"Directory detected. Searching for .md files in {input_path}")
        target_files = list(input_path.glob("*.md"))
    elif input_path.is_file():
        target_files = [input_path]
    else:
        raise FileNotFoundError(f"Path not found: {args.input}")

    if not target_files:
        print("No Markdown files found to process.")
    else:
        # ��������ļ�
        for file in target_files:
            process_for_zhihu(file, args)
        
        # ȫ��������ɺ�һ�����ύ Git
        git_ops(message=f"Batch update: {len(target_files)} files")
        print("\nAll done!")