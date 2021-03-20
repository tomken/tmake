#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
tmake cmake info py file
"""
import copy
import os
import stat
import traceback
import time
from collections import OrderedDict
from distutils.version import LooseVersion

import core
from .tmake_deps_parser import RemoteModuleParser
from core.utils import tmake_utils


class DepModule(object):
    """
    Dep module
    """
    LOCAL_KEY = "local"

    def __init__(self, name=None, version=None, custom_link_name=None):
        self.name = name
        self.link_name = name
        self.is_local = DepModule.LOCAL_KEY == version
        self.is_shared = self.name.endswith(core.SHARED_SUFFIX)
        self.is_binary = self.name.endswith(core.BINARY_SUFFIX)
        self.include_dir = []
        self.root_path = ""
        self.lib_dir = []
        self.dep_name_version_list = []  # item: [dep_name, dep_version]
        self.dep_module_list = []  # DepModule
        self.version = version
        # 添加对+类型的支持，版本号以+结尾的设置is_match_version为True
        self.is_match_version = False
        if version and version.endswith("+"):
            self.version = version[:-1]
            self.is_match_version = True
        self.declare_info = self.name + ":" + self.version
        # 下面属性主要是获取原始路径
        self.origin_lib_dir = ""
        self.origin_sym_lib_dir = ""
        self.origin_include_dir = ""
        # 自定义的依赖信息，none为未设置，空串为置空链接内容
        self.custom_link_name = custom_link_name

    def __check_name_version(self):
        if self != core.data.deps_mgr.get_module(self.name, self.version):
            raise core.TmakeException("error dep info {} {}".format(self.name, self.version))

    def get_deps_lib(self, un_relink_deps=None):
        self.__check_name_version()
        if self.is_binary:
            return []
        link_name = self.custom_link_name if self.custom_link_name is not None else self.link_name
        # link_name 可能为空，也可能为a,b
        if link_name == "":
            dep_list = []
        elif "," in link_name:
            dep_list = link_name.split(",")
        else:
            dep_list = [link_name]
        if un_relink_deps:
            if self.name in un_relink_deps:
                return dep_list
            if "{}:self".format(self.name) in un_relink_deps:
                return []
        for lib in self.dep_module_list:
            # 如果自己是动态库，并且依赖项是静态库就跳过，一些项目有问题，暂时屏蔽掉
            if self.is_shared and not lib.is_shared:
                continue
            dep_list.extend(lib.get_deps_lib())
        return dep_list

    def get_deps_lib_dir(self):
        self.__check_name_version()
        dep_list = []
        if self.is_binary:
            return dep_list
        dep_list.extend(self.lib_dir)
        for lib in self.dep_module_list:
            # 如果自己是动态库，并且依赖项是静态库就跳过，一些项目有问题，暂时屏蔽掉
            if self.is_shared and not lib.is_shared:
                pass
            dep_list.extend(lib.get_deps_lib_dir())
        return dep_list

    def get_deps_include(self):
        self.__check_name_version()
        dep_list = []
        if self.is_binary:
            return dep_list
        dep_list.extend(self.include_dir)
        for lib in self.dep_module_list:
            dep_list.extend(lib.get_deps_include())
        return dep_list

    def get_deps(self):
        dep_list = []
        for lib in self.dep_module_list:
            dep_list.extend(lib.get_deps())
        return self.dep_module_list + dep_list

    def get_deps_desc(self, deep):
        info = ""
        for i in range(0, deep):
            # 修改缩进符"\t" -> 空格符 * 2
            info += " " * 2
        info += "+{}:{}\n".format(self.name, self.version)
        for lib in self.dep_module_list:
            info += lib.get_deps_desc(deep + 1)
        return info

    def get_dep_info(self):
        dep_info = dict()
        dep_info["name"] = self.name
        dep_info["version"] = self.version
        dep_info["lib_dir"] = self.origin_lib_dir
        dep_info["include_dir"] = self.origin_include_dir
        dep_info["sym_lib_dir"] = self.origin_sym_lib_dir

        children_deps = {}
        dep_info["children"] = children_deps
        for item in self.dep_module_list:
            children_deps[item.name] = item.get_dep_info()
        return dep_info

    def __str__(self):
        deps_info = ""
        for item in self.dep_module_list:
            deps_info += item.name + "; "
        return "id={}, name={}, link_name={}, version={}, deps={}, include={}, path={}".format(id(self),
                                                                                               self.name,
                                                                                               self.link_name,
                                                                                               self.version,
                                                                                               deps_info,
                                                                                               self.include_dir,
                                                                                               self.root_path)


class DepsManager(object):
    """dep library manager"""

    def __init__(self):
        self.__deps_dict = {}  # __deps_set['abc']['version']=module
        self.__is_cyclic = False
        self.__conflict = {}
        self.__arch = "uninit"
        self.__root_deps_dict = {}  # 只有向文件中记录依赖关系用到，可执行程序的依赖列表
        self.__deps_download_queue = {}
        self.__current_lock_file = None
        self.callback_fun = None  # (callback_fun, callback_params, is_tree, exclude_rule)

    def remove_module(self, module):
        """
        移除某个module
        :param module:
        :return:
        """
        if module.name in self.__deps_dict:
            if module.version in self.__deps_dict[module.name]:
                del self.__deps_dict[module.name][module.version]

    def clear(self):
        """
        清空deps_manager
        :return:
        """
        self.__deps_dict = {}
        self.__is_cyclic = False

    def update_arch(self, arch):
        """
        更新arch
        :return:
        """
        self.__arch = arch

    def has_module(self, name, version):
        """has module"""
        if name in self.__deps_dict:
            if version in self.__deps_dict[name]:
                return True
        return False

    def get_module_by_name(self, name, force=True):
        """
        通过名字获得依赖信息
        如果冲突的解决方案里有，取里面的
        如果__deps_dict里有多个不同版本号的，取第一个
        :param name:
        :return:
        """
        arr = name.split(":")
        if len(arr) > 1:
            name = arr[0]
        result = None
        if name in self.__deps_dict:
            for key in self.__deps_dict[name]:
                result = self.__deps_dict[name][key]
                break
        if force and not result:
            raise core.TmakeException("Can't find dep info by name: {}".format(name))
        return result

    def get_module_deps_lib(self, name, un_relink_deps=None):
        """
        获取所有深层依赖的library
        :param name:
        :param un_relink_deps:
        :return:
        """
        module = self.get_module_by_name(name)
        if not module:
            return []
        temp = module.get_deps_lib(un_relink_deps)
        while None in temp:
            temp.remove(None)
        return temp

    def get_module_deps_lib_dir(self, name):
        """
        获取所有深层依赖的library查找路径
        :param name:
        :return:
        """
        module = self.get_module_by_name(name)
        if not module:
            return []
        temp = module.get_deps_lib_dir()
        while None in temp:
            temp.remove(None)
        return temp

    def get_module_deps_include(self, name):
        """
        获取所有深层依赖的library的include文件夹
        :param name:
        :return:
        """
        module = self.get_module_by_name(name)
        if not module:
            return []
        temp = module.get_deps_include()
        while None in temp:
            temp.remove(None)
        return temp

    def update_dep_module_lib_dir(self, name, lib_dir, include_dir):
        """
        更新lib的文件夹，一般是子项目编译完调用
        :param name:
        :param lib_dir:
        :param include_dir:
        :return:
        """
        module = self.get_module_by_name(name)
        module.lib_dir.extend(set(lib_dir))
        module.include_dir.extend(set(include_dir))

    def get_module(self, name, version):
        """
        通过name、version获取depModule
        :param name:
        :param version:
        :return:
        """
        if name in self.__deps_dict:
            if version in self.__deps_dict[name]:
                return self.__deps_dict[name][version]
        return None

    def set_module(self, module):
        """
        添加一个depmodule到__deps_dict
        :param module:
        :return:
        """
        if module.name in self.__deps_dict:
            if module.version not in self.__deps_dict[module.name]:
                self.__deps_dict[module.name][module.version] = module
        else:
            self.__deps_dict[module.name] = {}
            self.__deps_dict[module.name][module.version] = module

    def add_download_queue(self, module):
        """
        添加到下载队列
        :param module:
        :return:
        """
        if module.name in self.__deps_download_queue:
            self.__deps_download_queue[module.name][module.version] = module
        else:
            self.__deps_download_queue[module.name] = {}
            self.__deps_download_queue[module.name][module.version] = module

    def add_conflict_solution(self, cond_dict):
        """
        添加一个依赖的解决方案
        :param cond_dict:
        :return:
        """
        if cond_dict is None:
            return
        deps = []
        for modname, modver in dict(cond_dict).iteritems():
            deps.append("{}:{}".format(modname, modver))

        deps = tmake_utils.reset_deps(deps)

        for dep in deps:
            info = dep.split(":")
            self.__conflict[info[0]] = info[1]

    def __dep_analyse(self, dep):
        """
        分析被依赖的单个模块
        :param dep:
        :return:
        """
        dep_name, dep_version, custom_link_name = core.parse_dep(dep)
        # 在冲突里就用冲突里配置的
        if dep_name in self.__conflict:
            conflict_solution_version = self.__conflict[dep_name]
            if dep_version.endswith("+") \
                    and LooseVersion(conflict_solution_version) < LooseVersion(dep_version[:-1]):
                raise core.TmakeException("tmake_customerVersion is {{'{}':'{}'}}, "
                                           "but found must bigger one:{}".format(dep_name,
                                                                                 conflict_solution_version,
                                                                                 dep_version))
            dep_version = conflict_solution_version

        dep_mod = self.get_module(dep_name, dep_version)
        if not dep_mod:
            dep_mod = DepModule(dep_name, dep_version, custom_link_name)
            if not dep_mod.is_local:
                self.add_download_queue(dep_mod)
                self.set_module(dep_mod)
        return dep_mod

    def get_previous_version(self, version):
        if version:
            """
            自动降版本号的逻辑
            :param version: 当前版本
            :return:
            """
            ss = version.split('.')
            min_version = int(ss[-1]) - 1
            if min_version < 0:
                return ''
            ss[-1] = str(min_version)
            new_value = ""
            for oidx, o in enumerate(ss):
                if oidx != 0:
                    new_value += "."
                new_value += o
            return new_value
        else:
            return ''

    def __download_dep(self, module, arch):
        """
        下载某依赖
        :param module:
        :return:
        """
        from core.info.tmake_deps_download import DepDownload
        version = module.version
        try_previous_version = True
        while True:
            dep_download = DepDownload(core.TMAKE_LIBRARIES_PATH,
                                       module.name,
                                       version,
                                       core.data.target,
                                       arch)
            # 如果是ios的下载fusion指令集的，然后设置软连接
            if arch in [core.TARGET_CPU_OS, core.TARGET_CPU_SIMULATOR]:
                fusion_download = DepDownload(core.TMAKE_LIBRARIES_PATH,
                                              module.name,
                                              version,
                                              core.data.target,
                                              core.TARGET_CPU_FUSION)
                parser = self.__download_dep_module(fusion_download, module)
                # 设置软连接
                if parser:
                    tmake_utils.set_symlink(fusion_download.get_path(), dep_download.get_path())
            else:
                parser = self.__download_dep_module(dep_download, module)

            if not parser:
                if try_previous_version:
                    # 查看对应库的上一个版本是否存在，如果存在，则可能与依赖的库处于并发构建状态
                    version = self.get_previous_version(version)
                    if version:
                        try_previous_version = False
                    else:
                        # 前一个版本号不存在，直接抛出异常
                        raise core.TmakeException("download dep failed! [{}] [{}] {} ".format(core.data.target,
                                                                                           arch,
                                                                                           module))
                else:
                    raise core.TmakeException("download dep failed! [{}] [{}] {} ".format(core.data.target,
                                                                                       arch,
                                                                                       module))
            else:
                if not try_previous_version and module.version != version:
                    # 上一个版本的库存在，延时5min后再次下载
                    core.log.e("{}不存在，{}存在，可能处于并发构建，延时5min后自动再次尝试下载{}".format(module.version, version, module.name))
                    time.sleep(300)
                    version = module.version
                else:
                    # 下载成功，直接break
                    break
        module.include_dir = [parser.include_dir]
        module.root_path = parser.get_root_path()
        module.lib_dir = [parser.lib_dir]
        module.link_name = parser.link_name
        module.origin_lib_dir = parser.lib_dir
        module.origin_sym_lib_dir = parser.sym_lib_dir
        module.origin_include_dir = parser.include_dir
        return parser.depslibs

    def lock_deps(self):
        if self.__current_lock_file:
            core.log.v(" lock {}".format(self.__current_lock_file))
            self.__current_lock_file.acquire()

    def unlock_deps(self):
        if self.__current_lock_file:
            core.log.v(" unlock {}".format(self.__current_lock_file))
            self.__current_lock_file.release()
            self.__current_lock_file = None

    def __download_dep_module(self, downloader, module):
        ret, path = downloader.download_xml()
        if not ret:
            return None
        parser = RemoteModuleParser(module.name, module.version)
        parser.set_xmlpath(path)
        parser.parse()
        if not parser.has_download():
            lock_file = downloader.get_unique_key()
            core.log.v(" waiting lock {} ...".format(lock_file))
            if not os.path.exists(core.TMAKE_LOCK_PATH):
                os.mkdir(core.TMAKE_LOCK_PATH)
            # 轮询间隔是timeout的十分之一
            from core.third_part.lockfile import LockFile
            self.__current_lock_file = LockFile(os.path.join(core.TMAKE_LOCK_PATH, lock_file), timeout=400)
            try:
                self.lock_deps()
            except Exception, e:
                # 如果超时清掉锁文件再次申请锁
                core.log.e(repr(e))
                tmake_utils.clean(self.__current_lock_file.unique_name)
                lock_path = os.path.join(core.TMAKE_LOCK_PATH, "{}.lock".format(lock_file))
                try:
                    try:
                        os.chmod(lock_path, stat.S_IRWXU)
                    except Exception, e1:
                        pass
                    os.remove(lock_path)
                except Exception, e:
                    traceback.print_exc()
                    core.log.e("remove lock file [{}] failed! {}".format(lock_path, e.message))
                self.lock_deps()
                # 无论如何都把锁释放掉
            try:
                if not parser.has_download():
                    ret = downloader.download_package(parser.package_name, parser.package_type)
                else:
                    ret = True
            except Exception, e:
                traceback.print_exc()
                raise e
            finally:
                self.unlock_deps()
            if not ret:
                return None
        parser.check()
        return parser

    def parse(self, project, is_root):
        """
        解析一个项目的依赖关系
        :param project:
        :param is_root:
        :return:
        """
        # 把module里的描述添加到依赖集合里，类型为local
        for module_type_dict in [project.libraries, project.apps, project.binaries]:
            if not module_type_dict:
                continue
            for lib_name in module_type_dict:
                library = module_type_dict[lib_name]
                # 如果在冲突解决方案里，同时又不是local类型的就直接跳过了
                if lib_name in self.__conflict and self.__conflict[lib_name] != DepModule.LOCAL_KEY:
                    continue
                mod = DepModule(lib_name, DepModule.LOCAL_KEY)
                # 如果是local类型且不是project的给deps.log设置参数
                if "project" != core.data.arguments.tmake_cmd():
                    from core.info.tmake_path_info import PathInfo
                    path_info = PathInfo(self.__arch, project.folder)
                    mod.root_path = path_info.get_build_path()
                    library_name = lib_name.replace(core.SHARED_SUFFIX, "").replace(core.BINARY_SUFFIX, "")
                    mod.include_dir = [path_info.get_local_export_include_path(library_name)]
                self.set_module(mod)
                deps = []
                if 'deps' in library:
                    deps = library['deps']
                    deps= tmake_utils.reset_deps(deps)
                if deps and isinstance(deps, list):
                    if is_root:
                        self.__root_deps_dict[lib_name] = deps
                    for dep in deps:
                        depmod = self.__dep_analyse(dep)
                        mod.dep_name_version_list.append([depmod.name, depmod.version])

        # 处理 __root_deps_dict， 去重
        sub_key_list = []
        for key, value in self.__root_deps_dict.items():
            for inner_key, inner_value in self.__root_deps_dict.items():
                if inner_key == key:
                    continue
                for item in inner_value:
                    if key == item or "{}:".format(key) in item:
                        sub_key_list.append(key)
        for item in sub_key_list:
            if item in self.__root_deps_dict:
                del self.__root_deps_dict[item]

        while len(self.__deps_download_queue) > 0:
            ddq = self.__deps_download_queue
            self.__deps_download_queue = {}
            for dummy, versions in ddq.iteritems():
                for inner, mod in versions.iteritems():
                    deps = self.__download_dep(mod, self.__arch)
                    if deps and isinstance(deps, list):
                        for dep in deps:
                            dep_mod = self.__dep_analyse(dep)
                            mod.dep_name_version_list.append([dep_mod.name, dep_mod.version])
        pass

    def has_cyclic(self):
        """
        检查是否有循环依赖
        :return:
        """
        return self.__is_cyclic

    def __str__(self):
        info = "build finally use those deps:\n"
        for name in self.__deps_dict:
            for version in self.__deps_dict[name]:
                info += "[{}][{}]: {}\n".format(name, version, self.__deps_dict[name][version])
        return info

    def __check(self):
        """
        依赖树依赖检查
        :return:
        """
        self.__filter_match_module()
        for name, vers in self.__deps_dict.iteritems():
            if len(vers) > 1:
                self.__fix_origin_deps_module()
                self.record_deps_info()
                raise core.TmakeException("库版本冲突:[name:{}][version:{}]".format(name, vers.keys()))
            continue
            # 暂时去掉库不同类型版本冲突的检查
            fix_name = name
            for item in [core.SHARED_SUFFIX, core.BINARY_SUFFIX, core.FRAMEWORK_SUFFIX]:
                fix_name = fix_name.replace(item, "")

            # 如果xxxDice及xxxDice_shared同时依赖，版本不一样也报冲突
            type_version_set = None
            if fix_name in self.__deps_dict:
                type_version_set = set(self.__deps_dict[fix_name].keys() + vers.keys())
            if type_version_set and len(type_version_set) > 1:
                self.__fix_origin_deps_module()
                self.record_deps_info()
                raise core.TmakeException("库不同类型版本冲突:[name:{}/{}][version:{}]".format(fix_name,
                                                                                       name,
                                                                                       type_version_set))

        # 把名字转换为对象
        self.__fix_deps_module()

        # 成功记录依赖关系
        self.record_deps_info()

    def __filter_match_module(self):
        """
        对版本号中有+类型的支持 如1.0+
        :return:
        """
        for name in self.__deps_dict:
            version_list = []
            target_module_versions = self.__deps_dict[name]
            # 长度本身为 1 的无需处理
            if len(target_module_versions) == 1:
                continue
            has_match_version = False
            for version in target_module_versions:
                module = target_module_versions[version]
                version_list.append(module.version)
                if module.is_match_version:
                    core.log.i("{}:{}+ is match version.".format(module.name, module.version))
                    has_match_version = True
            if has_match_version:
                # 获取最大版本号，设置到self.__conflict中
                version_list.sort()
                max_version = self.__get_max_version(version_list)
                temp_module_versions = copy.copy(target_module_versions)
                for version in temp_module_versions:
                    if version != max_version:
                        del target_module_versions[version]
                        core.log.i("select versions with '+' : {}'s max version {}!{}".format(name,
                                                                                               max_version,
                                                                                               version_list))

    def __fix_deps_module(self):
        """
        替换 __deps_dict里的每个module的对象
        :return:
        """
        for name in self.__deps_dict:
            for ver in self.__deps_dict[name]:
                # 实际此时每个name只有一个version了
                dep_module = self.__deps_dict[name][ver]
                # 把字符串类型的依赖替换为depModule类型的依赖
                for dep in dep_module.dep_name_version_list:
                    module = self.get_module_by_name(dep[0])
                    if not module:
                        raise core.TmakeException("can't find module by name:%s" % dep[0])
                    dep_module.dep_module_list.append(module)

    def __fix_origin_deps_module(self):
        """
        替换 __deps_dict里的每个module的对象，用原始的版本号查找
        :return:
        """
        for name in self.__deps_dict:
            for ver in self.__deps_dict[name]:
                # 实际此时每个name只有一个version了
                dep_module = self.__deps_dict[name][ver]
                # 把字符串类型的依赖替换为depModule类型的依赖
                for dep in dep_module.dep_name_version_list:
                    module = self.get_module(dep[0], dep[1])
                    if not module:
                        # 配置了+的可能会导致找不到，这里再通过名字找下
                        module = self.get_module_by_name(dep[0])
                    if not module:
                        raise core.TmakeException("can't find module by name:{} version:{}".format(dep[0], dep[1]))
                    dep_module.dep_module_list.append(module)

    def __get_max_version(self, version_list):
        """
        通过LooseVersion来判断版本号大小
        :param version_list:
        :return:
        """
        max_version = "0.0"
        for version in version_list:
            if LooseVersion(version) > LooseVersion(max_version):
                max_version = version
        return max_version

    def record_deps_info(self):
        # 所有二进制程序，他们都是根
        all_direct_deps = set()
        for key in self.__root_deps_dict:
            all_direct_deps |= set(self.__root_deps_dict[key])
        # 所有被依赖的
        inner_deps = set()
        for name in self.__deps_dict:
            for ver in self.__deps_dict[name]:
                dep_module = self.__deps_dict[name][ver]
                if dep_module.name in all_direct_deps:
                    inner_deps.add(dep_module)
                inner_deps |= set(dep_module.get_deps())
        info = "DEPS INFO RECORD:\n\n"
        info += self.__str__()
        info += "\n\nTREE VIEW:\n"

        # 依赖树信息
        for key, value in self.__root_deps_dict.items():
            info += "\n\n deps info of {}(library|binary|app):\n\n".format(key)
            for item in value:
                module_info = self.get_module_by_name(item)
                info += module_info.get_deps_desc(1)
            # 生成浏览器可以查看的链接
            main_module = self.get_module_by_name(key)
            info += self.__general_deps_url(main_module)
        #core.log.i(info)
        core.tmake_print(info)

        # 记录依赖关系到deps.log
        from core.info.tmake_path_info import PathInfo
        path_info = PathInfo(self.__arch, core.data.project.folder)
        tmake_utils.write_entire_file(os.path.join(path_info.build_path, "deps.log"), info)

        # 记录依赖到json文件
        from core.info.tmake_record_info import RecordInfo
        RecordInfo().record_deps(self.__deps_dict)

    def __general_deps_url(self, module):
        """
        支持依赖树在网页上显示
        :param module:
        :return:
        """
        url_info = ""
        if module.is_local and not module.dep_module_list:
            return url_info
        arch = self.__arch
        if self.__arch in [core.TARGET_CPU_OS, core.TARGET_CPU_SIMULATOR]:
            arch = core.TARGET_CPU_FUSION
        general = True
        dep_info = []
        if module.is_local:
            for lib in module.dep_module_list:
                if lib.version == "local":
                    general = False
                else:
                    dep_info.append(lib.declare_info)
        else:
            dep_info.append(module.declare_info)
        if general:
            url_info += "\nshow in browser: {}repository/tree/show?deps={}&target={}&arch={}\n".format(
                core.data.repo.host_name,
                ",".join(dep_info),
                core.data.target,
                arch)
        return url_info

    def __callback(self):
        """
        依赖树回调
        :return:
        """
        if not self.callback_fun:
            return
        is_tree = self.callback_fun[2]
        exclude_rule = self.callback_fun[3]
        if is_tree:
            result = self.__root_deps_dict
        else:
            result = {}
            for item in self.__root_deps_dict.values():
                result.update(self.__plat_deps(item, exclude_rule))
        self.callback_fun[0](self.__arch, result, self.callback_fun[1])

    def library_deps(self, library_name):
        """
        获取库依赖
        :param library_name:
        :return:
        """
        dep_model = self.get_module_by_name(library_name)
        model_list = dep_model.get_deps()
        deps_dict = dict()
        for model in model_list:
            deps_dict[model.name] = dep_model.get_dep_info()
        sorted_dict = sorted(deps_dict.items(), key=lambda (key, value): key)
        result_dict = OrderedDict(sorted_dict)
        return result_dict

    def __plat_deps(self, deps_dict, exclude_rule=None):
        """
        平铺依赖关系
        :param deps_dict:
        :param exclude_rule:
        :return:
        """
        if not deps_dict:
            return []
        name = deps_dict["name"]
        result_dict = {name: deps_dict}

        # 根据规则过滤
        if exclude_rule:
            is_exclude = False
            for item in exclude_rule:
                if item in name:
                    is_exclude = True
                    break
            if is_exclude:
                return result_dict
        for item in deps_dict["children"].values():
            result_dict.update(self.__plat_deps(item, exclude_rule))
        return result_dict

    def parse_finish(self):
        # 依赖树检查
        self.__check()

        # 返回依赖关系
        for key, value in self.__root_deps_dict.items():
            dep_model = self.get_module_by_name(key)
            self.__root_deps_dict[key] = dep_model.get_dep_info()

        # 回调core.proj
        self.__callback()
