#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
tmake global info
"""
import json
import os
import traceback

from collections import OrderedDict

import core
from core.info import tmake_builtin
from core.info.tmake_path_info import PathInfo
from core.utils import tmake_utils


class RecordInfo(object):
    def __init__(self):
        self.deps_info = []
        self.deps_info_key = "deps_info"
        self.publish_info = []
        self.publish_info_key = "publish_info"
        self.record_file_name = "project_record.json"
        self.path_utils = PathInfo(tmake_builtin.TMAKE_CPU_ARCH, core.data.current_project.folder)
        self.record_file_path = os.path.join(self.path_utils.build_path, self.record_file_name)
        try:
            if os.path.exists(self.record_file_path):
                json_str = tmake_utils.read_all_from_file(self.record_file_path)
                json_dict = json.loads(json_str)
                if self.deps_info_key in json_dict and json_dict[self.deps_info_key]:
                    self.deps_info = json_dict[self.deps_info_key]
                if self.publish_info_key in json_dict and json_dict[self.publish_info_key]:
                    self.publish_info = json_dict[self.publish_info_key]
        except Exception, e:
            traceback.print_exc()

    def record_publish_info(self, publish_list):
        """
        记录依赖关系
        :param publish_list:
        :return:
        """
        del self.publish_info[:]
        self.publish_info += publish_list
        self.__record_to_file()

    def record_deps(self, deps_dict):
        """
        记录依赖关系
        :param deps_dict:
        :return:
        """
        del self.deps_info[:]
        for name, vers in deps_dict.iteritems():
            is_conflict = len(vers) > 1
            for version in vers:
                self.deps_info.append({"name": name, "version": version, "is_conflict": is_conflict})
        self.__record_to_file()

    def __record_to_file(self):
        record_dict = OrderedDict()
        record_dict[self.deps_info_key] = self.deps_info
        record_dict[self.publish_info_key] = self.publish_info
        json_str = json.dumps(record_dict, indent=4)
        tmake_utils.write_entire_file(self.record_file_path, json_str)
