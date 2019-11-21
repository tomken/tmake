#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
cmake action file
"""
import os

import core
from core.utils import tmake_utils

PLUGIN_VERSION = "1.0.0"

# 生成camke_list的tag
TMAKE_ACTION_CMAKE_LISTS = "CMAKE_LISTS"
# build的tag
TMAKE_ACTION_CMAKE_BUILD = "PRE_CMAKE_BUILD"
# 生成项目的tag
TMAKE_ACTION_CMAKE_PROJECT = "PRE_CMAKE_PROJECT"
# publish之前的操作
TMAKE_ACTION_PUBLISH_PROJECT = "PRE_PUBLISH_PROJECT"


class Action(object):
    """action base class"""

    def __init__(self):
        pass

    def filter_by_command(self, dummy):
        """
        action filter by command
        cmake is special command
        """
        return False

    def filter_by_build_type(self, command):
        """action type"""
        return ""

    def is_befor(self, command):
        """is befor command to run"""
        return False

    def is_after(self, command):
        """is after command to run"""
        return False

    def priority(self):
        """action priority"""
        return 0

    def run(self, command, ctx, acg):
        """run action"""
        pass

    def __str__(self):
        return "empty action"


def action_comp(action1, action2):
    """comp action"""
    if action1.priority() < action2.priority():
        return 1
    elif action1.priority() > action2.priority():
        return -1
    else:
        return 0


class ActionManager(object):
    """
    tmake action plugin manager
    """

    def __init__(self):
        # 所有插件
        self.actions = []
        # 类型和保存文件夹的映射关系
        self.plugin_type_mapping = {"cmd": "cmd", "action": "actions", "cmake": "cmake_gens"}
        # 类型和保存的文件名前缀
        self.plugin_name_mapping = {"cmd": "tmake_", "action": "tmake_action_", "cmake": "tmake_cmake_generator_"}
        # 加载插件
        self.__try_load_action()

    def run_befor_action(self, command, ctx, acg):
        """
        run befor action
        """
        for action in self.actions:
            if action.filter_by_command(command) and action.is_befor(command):
                action.run(command, ctx, acg)

    def run_after_action(self, command, ctx, acg):
        """
        run after action
        """
        for action in self.actions:
            if action.filter_by_command(command) and action.is_after(command):
                action.run(command, ctx, acg)

    def __try_load_action(self):
        # 通过参数p获取插件
        plugin_name = core.data.arguments.get_opt("p")
        if not plugin_name:
            return
        plugin_list = plugin_name.split(core.GLOBAL_SEPARATED)

        # 获取已经存在的插件列表
        folder = os.path.dirname(os.path.abspath(__file__))
        file_list = os.listdir(folder)
        for plugin in plugin_list:
            plugin_name = self.plugin_name_mapping["action"] + plugin
            # 不存在下载
            if plugin_name + ".py" not in file_list:
                if not self.try_download_plugin("action", plugin):
                    raise core.TmakeException(
                        "The plugin:" + plugin + " is not support! Please check your -p params!")
            # 加载插件
            try:
                module = "core.actions." + plugin_name
                exec ("import " + module)
                action = eval(module + ".new_action()")
                self.actions.append(action)
            except ImportError:
                raise core.TmakeException("Can't load action plugin {} \n".format(plugin))
            core.s("plugin [%s] loaded successfully!" % plugin)
        self.actions.sort(cmp=action_comp)

    def __get_plugin_info(self, plugin_type, name):
        """
        通过插件类型和名字来查询插件
        :param plugin_type:
        :param name:
        :return:
        """
        params = {'type': plugin_type, 'name': name}
        success, json_object, msg = comm_utils.request_json_object(core.data.repo.get_default_plugin_search_url(), params)
        if success and json_object and "path" in json_object[0]:
            return json_object[0]["path"]
        return None

    def try_download_plugin(self, plugin_type, name):
        """
        通过插件类型和名字来下载插件
        :param plugin_type:
        :param name:
        :return:
        """
        path = self.__get_plugin_info(plugin_type, name)
        if not path:
            return False
        url = comm_utils.urljoin(core.data.repo.get_default_plugin_download_url(), path)
        save_path = os.path.join(core.data.arguments.tmake_path(),
                                 "tmake",
                                 self.plugin_type_mapping[plugin_type],
                                 self.plugin_name_mapping[plugin_type] + name + ".py")
        return DownloadFile(url, save_path).download()
