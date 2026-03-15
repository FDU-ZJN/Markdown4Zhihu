import os
import re
import argparse
import subprocess
import chardet
import functools
import os.path as op
from PIL import Image
from pathlib2 import Path
from shutil import copyfile

GITHUB_REPO_PREFIX = "https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/"
COMPRESS_THRESHOLD = 5e5

def formula_ops(lines):
    lines = re.sub('((.*?)\$\$)(\s*)?([\s\S]*?)(\$\$)\n', '\n<img src="https://www.zhihu.com/equation?tex=\\4" alt="\\4" class="ee_img tr_noresize" eeimg="1">\n', lines)
    lines = re.sub('(\$)(?!\$)(.*?)(\$)', ' <img src="https://www.zhihu.com/equation?tex=\\2" alt="\\2" class="ee_img tr_noresize" eeimg="1"> ', lines)
    return lines

def reduce_single_image_size(image_path):
    output_path = Path(image_path).parent / (Path(image_path).stem + ".jpg")
    if op.exists(image_path):
        img = Image.open(image_path)
        if (img.size[0] > img.size[1] and img.size[0] > 1920):
            img = img.resize((1920, int(1920 * img.size[1] / img.size[0])), Image.LANCZOS)
        elif (img.size[1] > img.size[0] and img.size[1] > 1080):
            img = img.resize((int(1080 * img.size[0] / img.size[1]), 1080), Image.LANCZOS)
        img.convert('RGB').save(output_path, optimize=True, quality=85)
    return output_path

def rename_image_ref(m, current_args, original=True):
    ori_path = m.group(2) if original else m.group(1)
    full_img_path = None

    if op.exists(ori_path):
        full_img_path = ori_path
    else:
        potential_path = op.join(current_args.file_parent, ori_path)
        if op.exists(potential_path):
            full_img_path = potential_path

    if full_img_path is None:
        return m.group(0)

    try:
        img_stem = Path(full_img_path).stem
        img_suffix = Path(full_img_path).suffix
        img_name_new = img_stem + img_suffix
        
        target_path = op.join(current_args.image_folder_path, img_name_new)
        if op.exists(target_path):
            i = 1
            while op.exists(op.join(current_args.image_folder_path, img_name_new)):
                img_name_new = f"{img_stem}_{i}{img_suffix}"
                i += 1
            target_path = op.join(current_args.image_folder_path, img_name_new)

        copyfile(full_img_path, target_path)
        
        if op.getsize(target_path) > COMPRESS_THRESHOLD and current_args.compress:
            target_path = reduce_single_image_size(target_path)
        
        image_ref_name = Path(target_path).name
        current_args.used_images.append(image_ref_name)

        if original:
            return "![" + m.group(1) + "](" + GITHUB_REPO_PREFIX + current_args.input.stem + "/" + image_ref_name + ")"
        else:
            return '<img src="' + GITHUB_REPO_PREFIX + current_args.input.stem + "/" + image_ref_name + '"'
    except:
        return m.group(0)

def cleanup_image_folder(current_args):
    if not op.exists(current_args.image_folder_path):
        return
    actual_images = [op.join(current_args.image_folder_path, i) for i in os.listdir(current_args.image_folder_path) if op.isfile(op.join(current_args.image_folder_path, i))]
    for path in actual_images:
        if Path(path).name not in current_args.used_images:
            os.remove(str(path))

def image_ops(lines, current_args):
    lines = re.sub(r"\!\[(.*?)\]\((.*?)\)", functools.partial(rename_image_ref, current_args=current_args, original=True), lines)
    lines = re.sub(r'<img src="(.*?)"', functools.partial(rename_image_ref, current_args=current_args, original=False), lines)
    return lines

def table_ops(lines):
    return re.sub("\|\n", r"|\n\n", lines)

def git_ops(message):
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", message])
    subprocess.run(["git", "push", "-u", "origin", "master"])

def process_single_file(file_path, current_args):
    current_args.input = Path(file_path)
    current_args.file_parent = str(current_args.input.parent)
    current_args.used_images = []
    
    image_folder = op.join(current_args.current_script_data_path, current_args.input.stem)
    if not op.exists(image_folder):
        os.makedirs(image_folder)
    current_args.image_folder_path = image_folder

    if current_args.encoding is None:
        with open(str(current_args.input), 'rb') as f:
            encoding = chardet.detect(f.read())['encoding']
    else:
        encoding = current_args.encoding

    with open(str(current_args.input), "r", encoding=encoding) as f:
        content = f.read()
        content = image_ops(content, current_args)
        content = formula_ops(content)
        content = table_ops(content)
        
        output_name = current_args.input.stem + "_for_zhihu.md"
        output_path = op.join(current_args.current_script_data_path, output_name)
        with open(output_path, "w+", encoding=encoding) as fw:
            fw.write(content)
    
    cleanup_image_folder(current_args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--compress', action='store_true')
    parser.add_argument('-i', '--input', type=str)
    parser.add_argument('-e', '--encoding', type=str)
    args = parser.parse_args()

    if args.input is None:
        exit()

    input_path = Path(args.input)
    args.current_script_data_path = str(Path(__file__).absolute().parent / 'Data')
    
    if not op.exists(args.current_script_data_path):
        os.makedirs(args.current_script_data_path)

    files_to_process = []
    if input_path.is_dir():
        files_to_process = list(input_path.glob("*.md"))
    elif input_path.is_file():
        files_to_process = [input_path]

    for f in files_to_process:
        process_single_file(f, args)
    
    if files_to_process:
        git_ops(f"Batch update: {len(files_to_process)} files")