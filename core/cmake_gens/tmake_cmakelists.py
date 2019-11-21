#!/usr/bin/python2
# -*- coding:UTF-8 -*-
"""
tmake cmakelist
"""
import os
import re

# 存储左括号和右括号

import core
import shutil

OPEN_BRACKETS = '('
CLOSE_BRACKETS = ')'
# 映射左右括号便于出栈判断
BRACKETS_MAP = {')': '('}

# CMakeLists.txt文件名
CMAKELISTS = "CMakeLists.txt"
CMAKELISTS_BACKUP = "CMakeLists_backup.txt"

#pattern_tempelate
#INSTALL_PATTERN_TEMPLATE = r'INSTALL \(*'
INSTALL_PATTERN_TEMPLATE = r'INSTALL\(*'
DESTINATION_PATTERN_TEMPLATE = r'DESTINATION*(.*)'

INSTALL_PATTERN_TEMPLATE = [r'SET\(CMAKE_INSTALL_PREFIX',
                            r'SET \(CMAKE_INSTALL_PREFIX',
                            r'SET\(CMAKE_INSTALL_INCLUDEDIR',
                            r'SET \(CMAKE_INSTALL_INCLUDEDIR',
                            r'SET\(CMAKE_INSTALL_LIBDIR',
                            r'SET \(CMAKE_INSTALL_LIBDIR',
                            r'SET\(EXECUTABLE_OUTPUT_PATH',
                            r'SET \(EXECUTABLE_OUTPUT_PATH',
                            r'SET\(LIBRARY_OUTPUT_PATH',
                            r'SET \(LIBRARY_OUTPUT_PATH',
                            ]

SET_CMAKE_INSTALL_PREFIX = "SET(CMAKE_INSTALL_PREFIX ""{}"")\n"
SET_CMAKE_INSTALL_INCLUDEDIR = "SET(CMAKE_INSTALL_INCLUDEDIR ""{}"")\n"
SET_CMAKE_INSTALL_LIBDIR = "SET(CMAKE_INSTALL_LIBDIR ""{}"")\n"
SET_EXECUTABLE_OUTPUT_PATH = "SET(EXECUTABLE_OUTPUT_PATH ""{}"")\n"
SET_LIBRARY_OUTPUT_PATH = "SET(LIBRARY_OUTPUT_PATH ""{}"")\n"
SET_CMAKE_CURRENT_BINARY_DIR = "SET(CMAKE_CURRENT_BINARY_DIR ""{}"")\n"
#库后缀名
LIB_SUBFFIX = ['.a', '.lib', '.so', '.dylib', '.dll', '.pdb', '.exe']
LINK_STYLE_MAP = {'.a':'STATIC', '.lib':'STATIC', '.so':'SHARED', '.dylib':'SHARED', '.dll':'SHARED', '.pdb':'SHARED', '.exe':'WIN32'}
HEADER_SUBFFIX = ['.h', '.hpp', '.c', '.cpp', '.mm', '.m']

NO_CHANGE_CMAKELISTS = False


def __read_file(file):
    lines = None
    with open(file, "r") as f:
        lines = f.readlines()
        f.close()
    return lines

#pattern = r'install*(*DESTINATION (.*)'
def __search_text(pattern, line_text):
    searchObj = re.search(pattern, line_text, re.M|re.I)
    if searchObj:
        return searchObj.group()
    else:
        return None

#pattern = r'DESTINATION (.*)'   # DESTINATION
def __find_all_sub_text(pattern, line_text):
    text_list = []
    bfind = False
    it = re.finditer(pattern, line_text)
    for match in it:
        bfind = True
        result = match.group(1)
        #result = result.replace(" ", "")
        if result:
            result = result.replace(")", "")
            text_list.append(result)
    return bfind, text_list

#pattern = r'install*(*DESTINATION*'
def __replace_text(pattern, line_text, wanted_text):
    #new_text = re.sub(r"{}".format(pattern), wanted_text, line_text, re.I)
    pattern = pattern.replace(" ", "", 1)
    new_text = line_text.replace(pattern, wanted_text)
    return new_text

def __check(row):
    # 对于每一行数据，进行如下判定若括号为左括号，加入栈，若括号为右括号，判断是否跟栈尾括号对应，
    # 若对应，弹出栈尾元素，若所有括号均正确闭合，则最后栈为空。
    stack = []
    label = True
    for char in row:
        if char in OPEN_BRACKETS:
            stack.append(char)
        elif char in CLOSE_BRACKETS:
            if len(stack) < 1:
                label = False
                break
            elif BRACKETS_MAP[char] == stack[-1]:
                stack.pop()
            else:
                label = False
                break
        else:
            continue
    if stack != []:
        label = False
    return label

def __find_and_replace(pattern, text, wanted_text):
    result = ""
    bfind, text_list = __find_all_sub_text(pattern, text)
    if len(text_list) > 0:
        result = text
        for item in text_list:
            # 多次替换可能存在问题
            result = __replace_text(r'{}'.format(item), result, wanted_text)
    return bfind,result

# def __modify_cmaklists(lines, new_text):
#     if lines is None:
#         return False,[]
#
#     is_modify = False
#     total_line = len(lines)
#     for i in range(0, total_line):
#         #寻找关键字INSTALL (
#         result = __search_text(INSTALL_PATTERN_TEMPLATE, lines[i])
#         if result:
#             line = ""
#             while i < total_line:
#                 line += lines[i]
#                 bfind,result = __find_and_replace(DESTINATION_PATTERN_TEMPLATE, lines[i], new_text)
#                 if result:
#                     lines[i] = result
#                     is_modify = True
#                 elif bfind:
#                     i += 1
#                     line += lines[i]
#                     while i < total_line:
#                         line += lines[i]
#                         is_comlete = __check(line)
#                         if is_comlete:
#                             break
#                         result = __search_text(r'(.*)', lines[i])
#                         if result:
#                             result = __replace_text(result, lines[i], new_text)
#                             lines[i] = result
#                             is_modify = True
#                             break;
#                         i += 1
#                 is_comlete = __check(line)
#                 if is_comlete:
#                     break
#                 i += 1
#             if not is_comlete:
#                 raise core.TmakeException("CMakelists.txt is not correct: {}".format(line))
#     return is_modify,lines

def __modify_cmaklists(lines, export_path, executable_output_path, library_output_path):
    if lines is None:
        return False,[]

    is_modify = True
    new_lines = []
    total_line = len(lines)
    new_lines.append(SET_CMAKE_INSTALL_PREFIX.format(export_path))
    new_lines.append(SET_EXECUTABLE_OUTPUT_PATH.format(executable_output_path))
    new_lines.append(SET_LIBRARY_OUTPUT_PATH.format(library_output_path))
    #new_lines.append(SET_CMAKE_INSTALL_INCLUDEDIR.format(library_output_path))
    #new_lines.append(SET_CMAKE_CURRENT_BINARY_DIR.format(library_output_path))
    new_lines.append(SET_CMAKE_INSTALL_LIBDIR.format(library_output_path))

    for i in range(0, total_line):
        #寻找关键字INSTALL (
        result = ''
        for pattern in INSTALL_PATTERN_TEMPLATE:
            result = __search_text(pattern, lines[i])
            if result:
                result = "#{}".format(lines[i])
                break
        if result:
            new_lines.append(result)
            is_modify = True
        else:
            new_lines.append(lines[i])

    return is_modify,new_lines

def __backup_cmakelists(file):
    result = False
    if os.path.isfile(file) and CMAKELISTS.lower() in file.lower():
        new_file = file.replace(CMAKELISTS, CMAKELISTS_BACKUP)
        os.rename(file, new_file)
        result = True
    return result

def __rewrite_cmakelists(file, lines):
    result = False
    if CMAKELISTS.lower() in file.lower() and lines:
        with open(file, 'w') as f:
            f.writelines(lines)
            f.close()
            result = True
    return result

def delete_libs(src_dir):
    # 删除无关的文件
    src_dir = src_dir.replace("\\", "/")
    if not os.path.exists(src_dir):
        return
    for f in os.listdir(src_dir):
        sourceF = os.path.join(src_dir, f)
        sourceF = sourceF.replace("\\", "/")
        if os.path.isfile(sourceF):
            suffix = os.path.splitext(sourceF)[1]
            if suffix and suffix.lower() in LIB_SUBFFIX:
                os.remove(sourceF)
            if suffix is None and os.access(sourceF, os.X_OK):
                os.remove(sourceF)
        if os.path.isdir(sourceF):
            delete_libs(sourceF)

def move_header_files(src_dir, dst_dir):
    if NO_CHANGE_CMAKELISTS:
        return
    src_dir = src_dir.replace("\\", "/")
    dst_dir = dst_dir.replace("\\", "/")
    if not os.path.exists(src_dir):
        core.i("move_header_files: no src_dir={}".format(src_dir))
        return

    libname = dst_dir[dst_dir.rfind("/")+1:]
    bfind = False
    for f in os.listdir(src_dir):
        sourceF = os.path.join(src_dir, f)
        sourceF = sourceF.replace("\\", "/")
        if os.path.isdir(sourceF):
            if f == libname:
                bfind = True
                src_dir = sourceF
                break

    if not bfind:
        src_dir = os.path.join(src_dir, "include")
        if not os.path.exists(src_dir):
            core.i("move_header_files no include directory: {}".format(src_dir))
            return
        target_path = os.path.join(dst_dir, "include")
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        shutil.copytree(src_dir, target_path)
    else:
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)
        for f in os.listdir(src_dir):
            sourceF = os.path.join(src_dir, f)
            sourceF = sourceF.replace("\\", "/")
            if os.path.isdir(sourceF):
                target_path = os.path.join(dst_dir, "include")
                shutil.copytree(sourceF, target_path)
            else:
                target_path = os.path.join(dst_dir, "include")
                target_file = os.path.join(target_path, f)
                if os.path.exists(target_file):
                    os.remove(target_file)
                shutil.copy(sourceF, target_path)

def recover_cmakelists(path):
    if NO_CHANGE_CMAKELISTS:
        return
    path = path.replace("\\", "/")
    if not os.path.exists(path):
        return
    result = False
    for f in os.listdir(path):
        sourceF = os.path.join(path, f)
        sourceF = sourceF.replace("\\", "/")
        if os.path.isfile(sourceF) and CMAKELISTS_BACKUP.lower() in sourceF.lower():
            base_path = sourceF[0:sourceF.rfind("/")]
            file = os.path.join(base_path, CMAKELISTS)
            if os.path.isfile(file):
                os.remove(file)
            os.rename(sourceF, file)
            result = True
        if os.path.isdir(sourceF):
            recover_cmakelists(sourceF)
    return result

def change_cmakelists_output(src_dir, export_path, executable_output_path, library_output_path):

    if NO_CHANGE_CMAKELISTS:
        return
    src_dir = src_dir.replace("\\", "/")
    export_path = export_path.replace("\\", "/")
    executable_output_path = executable_output_path.replace("\\", "/")
    library_output_path = library_output_path.replace("\\", "/")
    for f in os.listdir(src_dir):
        sourceF = os.path.join(src_dir, f)
        sourceF = sourceF.replace("\\", "/")
        if os.path.isfile(sourceF) and CMAKELISTS.lower() in sourceF.lower():
            lines = __read_file(sourceF)
            is_modify, lines = __modify_cmaklists(lines, export_path, executable_output_path, library_output_path)
            if is_modify and lines:
                ret = __backup_cmakelists(sourceF)
                if not ret:
                    core.TmakeException("Backup CMakelists.txt failed: {}".format(sourceF))
                else:
                    ret = __rewrite_cmakelists(sourceF, lines)
                    if not ret:
                        core.TmakeException("Rewrite CMakelists.txt failed: {}".format(sourceF))
        if os.path.isdir(sourceF):
            change_cmakelists_output(sourceF, export_path, executable_output_path, library_output_path)

def get_libs_info(libs_dir):
    libs_info = []
    if NO_CHANGE_CMAKELISTS:
        return libs_info
    if not os.path.exists(libs_dir):
        return libs_info
    libs_dir = libs_dir.replace("\\", "/")

    for f in os.listdir(libs_dir):
        sourceF = os.path.join(libs_dir, f)
        sourceF = sourceF.replace("\\", "/")
        if os.path.isfile(sourceF):
            suffix = os.path.splitext(sourceF)[1]
            lib_name = sourceF[sourceF.rfind("/")+1:]
            if suffix and suffix.lower() in LIB_SUBFFIX and suffix.lower() != '.pdb' and suffix.lower() != '.exe':
                link_style = LINK_STYLE_MAP[suffix]
                lib_name = lib_name.replace(suffix, "")
                lib_name = lib_name.replace("lib", "",1)
                lib_info = "{}:{}".format(lib_name, link_style)
                libs_info.append(lib_info)
        if os.path.isdir(sourceF):
            get_libs_info(sourceF)
    return libs_info

def arrange_dir(src_dir, dst_dir):
    src_dir = src_dir.replace("\\", "/")
    dst_dir = dst_dir.replace("\\", "/")
    if not os.path.exists(src_dir):
        return
    for f in os.listdir(src_dir):
        sourceF = os.path.join(src_dir, f)
        sourceF = sourceF.replace("\\", "/")
        if os.path.islink(sourceF):
            os.remove(sourceF)
            continue
        if os.path.isfile(sourceF):
            suffix = os.path.splitext(sourceF)[1]
            lib_name = sourceF[sourceF.rfind("/")+1:]
            dst_file = os.path.join(dst_dir, lib_name)
            if suffix and suffix.lower() in LIB_SUBFFIX and not os.path.exists(dst_file):
               shutil.move(sourceF, dst_file)
            elif suffix is None and os.access(sourceF, os.X_OK) and not os.path.exists(dst_file):
                shutil.move(sourceF, dst_file)
            elif suffix and not suffix.lower() in HEADER_SUBFFIX and not suffix.lower() in LIB_SUBFFIX:
                os.remove(sourceF)
        if os.path.isdir(sourceF):
            arrange_dir(sourceF, dst_dir)

def copy_bin_to_export(src_dir, dst_dir):
    if NO_CHANGE_CMAKELISTS:
        return
    src_dir = src_dir.replace("\\", "/")
    dst_dir = dst_dir.replace("\\", "/")
    if not os.path.exists(src_dir):
        core.i("copy_bin_to_export error directory: {}".format(src_dir))
        return
    if os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)

def copy_libs_to_export(src_dir, dst_dir):
    if NO_CHANGE_CMAKELISTS:
        return
    src_dir = src_dir.replace("\\", "/")
    dst_dir = dst_dir.replace("\\", "/")
    if not os.path.exists(src_dir):
        return
    for f in os.listdir(src_dir):
        sourceF = os.path.join(src_dir, f)
        sourceF = sourceF.replace("\\", "/")
        if os.path.islink(sourceF):
            os.remove(sourceF)
            continue
        if os.path.isfile(sourceF):
            suffix = os.path.splitext(sourceF)[1]
            lib_name = sourceF[sourceF.rfind("/")+1:]
            dst_file = os.path.join(dst_dir, lib_name)
            if suffix and suffix.lower() in LIB_SUBFFIX and not os.path.exists(dst_file):
               if not os.path.exists(dst_dir):
                   os.makedirs(dst_dir)
               shutil.copy(sourceF, dst_file)
        if os.path.isdir(sourceF):
            copy_libs_to_export(sourceF, dst_dir)

def delete_src_file(src_dir):
    if NO_CHANGE_CMAKELISTS:
        return
    src_dir = src_dir.replace("\\", "/")
    if not os.path.exists(src_dir):
        return
    for f in os.listdir(src_dir):
        sourceF = os.path.join(src_dir, f)
        sourceF = sourceF.replace("\\", "/")
        if os.path.isfile(sourceF):
            suffix = os.path.splitext(sourceF)[1]
            if suffix and suffix.lower() in HEADER_SUBFFIX:
                os.remove(sourceF)
            elif suffix is None and not os.access(sourceF, os.X_OK):
                os.remove(sourceF)
        if os.path.isdir(sourceF):
            delete_src_file(sourceF)

def delete_empty_dir(dir):
    dir = dir.replace("\\", "/")
    if not os.path.exists(dir):
        return
    if os.path.isdir(dir):
        for p in os.listdir(dir):
            d  = os.path.join(dir, p)
            if (os.path.isdir(d) == True):
                delete_empty_dir(d)
    if not os.listdir(dir):
        os.rmdir(dir)

