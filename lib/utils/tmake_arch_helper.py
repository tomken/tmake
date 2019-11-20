#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
lib arch command
"""
import os
import traceback
from collections import OrderedDict
import lib


class ArchHelper(object):
    NO_MATCH_KEY = "no match"

    def __init__(self, work_path):
        """
        构造函数
        """
        self.arch_list_file_name = "ARCH.list"
        self.arch_keyword = "arch"
        self.not_found_list = []
        self.all_arch_list = {}
        self.work_path = work_path

    def read_all_from_file(self, full_path):
        fd = open(full_path, 'rb')
        result = fd.read()
        fd.close()
        return result

    def get_arch_dict(self):
        """
        通过ARCH.list解析自定义arch,command
        :return:dict
        """
        result_dict = {}
        print("get arch dict... {}".format(self.work_path))
        # 校验文件
        source_file_path = os.path.join(self.work_path, self.arch_list_file_name)
        if not os.path.exists(source_file_path):
            print("{} not found in {}, skip!".format(self.arch_list_file_name, self.work_path))
            return result_dict

        # 解析字典内容
        arch_dict = {}
        try:
            exec self.read_all_from_file(source_file_path)
        except Exception, e:
            traceback.print_exc()
            raise lib.TmakeException("parse [{}] error, {}".format(self.arch_list_file_name, repr(e)))
        print("arch_dict = {} ...".format(arch_dict))

        # 校验格式
        if self.arch_keyword not in arch_dict:
            raise lib.TmakeException(
                "{} not found in {}".format(self.arch_keyword, self.arch_list_file_name))

        result_dict = self.__parse_arch(arch_dict)
        return result_dict

    def get_arch_commad(self, arch):
        """
        :return:command
        """
        find = False
        result_dict = self.get_arch_dict()
        command = ""
        for (k, v) in result_dict.items():
            if (k == arch):
                command = v
                find = True
                break
        return find, command

    def get_arch_list(self):
        """
        :return:archs
        """
        result_dict = self.get_arch_dict()
        arch_list = []
        for (k, v) in result_dict.items():
            arch_list.append(k)
        return arch_list

    def __parse_arch(self, arch_dict):
        result_dict = OrderedDict()
        if self.arch_keyword in arch_dict and arch_dict[self.arch_keyword]:
            arch_list = arch_dict[self.arch_keyword]
            all_arch_name = []
            all_arch_command = []
            for item in arch_list:
                all_arch_name.append(item["name"])
                all_arch_command.append(item["command"])
            for arch_info in arch_list:
                if "name" not in arch_info:
                    continue
                arch_name = arch_info["name"]
                print("start parse {} ...".format(arch_name))
                arch_command = arch_info["command"]
                print("{} parse command {} ...".format(arch_name, arch_command))
                if arch_command == ArchHelper.NO_MATCH_KEY:
                    self.not_found_list.append(arch_command)
                result_dict[arch_name] = arch_command
        return result_dict


def main():
    """tmake arch extend entry"""
    return ArchHelper()
