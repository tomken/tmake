# coding:utf-8
import re, os
from functools import reduce


class PropertiesParser():
    def __init__(self):
        self.__update_log = {}
        self.__add_log = {}
        self.__config = {}
        self.__configfilename = None

    def __validitycheck(self, lines, configfilename):
        for line_number in range(len(lines)):
            if (not re.match(r'^#', lines[line_number])) and (not re.match(r'^(\r\n|\r|\n)', lines[line_number])) and (
                    not re.match(r'^[a-zA-Z0-9](\w|\.| |\t)*\=( |\t)*(\S|.)*$', lines[line_number])):
                raise SyntaxError("The configuration file (%s) have SyntaxError(%s) in line %s" % (
                    configfilename, lines[line_number], line_number + 1))

    def __analysisfile(self, configfilename):
        with open(configfilename, 'r') as Contents:
            lines = Contents.readlines()
        self.__validitycheck(lines, configfilename)
        return [re.match(r'^[a-zA-Z0-9](\w|\.| |\t)*\=( |\t)*(\S|.)*$', line).group() for line in lines if
                re.match(r'^[a-zA-Z0-9](\w|\.| |\t)*\=( |\t)*(\S|.)*$', line)]

    def __analysislines(self, vaild_lines):
        return [re.split(r'( |\t)*\=( |\t)*', i, maxsplit=1) for i in vaild_lines]

    def __genarate_config(self, key, value):
        if re.match(r'^(False|None|True){1,1}$', value):
            value = eval(value)
        elif re.match(r'^(\d)+\.(\d)+$|^(\d)+$', re.sub(r'(\s)*$', '', value)):
            value = eval(value)
        else:
            value = re.sub(r'(\s)*$', '', value)
        self.__config[key] = value

    def read(self, configfilename):
        if os.path.exists(configfilename):
            if os.path.isfile(configfilename):
                _ = [self.__genarate_config(item[0], item[-1]) for item in
                     self.__analysislines(self.__analysisfile(configfilename))]
                self.__configfilename = configfilename
            else:
                raise IOError('"%s" is not a file.' % configfilename)
        else:
            raise FileNotFoundError('No such file or directory:"%s"' % configfilename)

    def keys(self):
        return self.__config.keys()

    def get(self, key):
        try:
            return self.__config[key]
        except:
            raise KeyError("Maping key not found.('%s')" % key)

    def update(self, key, newvalue):
        if re.match(r"(\S|.)*", str(newvalue)) and re.match(r"^(\S|.)*", str(newvalue)).group() == str(newvalue):
            self.__update(key, newvalue)
        else:
            raise ValueError("Unsupported value.(Only support Non-blank characters)")

    def __update(self, key, newvalue):
        if key in self.__config.keys():
            if self.__config[key] != newvalue:
                self.__config[key] = re.sub(r'(\s)*$', '', newvalue)
                self.__update_log[key] = re.sub(r'(\s)*$', '', newvalue)
            else:
                pass
        else:
            raise KeyError("Maping key not found.('%s')" % key)

    def add(self, key, value):
        if re.match(r"(\S)*", str(value)) and re.match(r"^(\S)*", str(value)).group() == str(value):
            if re.match(r'^[a-zA-Z0-9](\w|\.)*$', str(key)):
                self.__add(key, value)
            else:
                raise KeyError(
                    "Unsupported Key.(The key must start with a number or letter and only support ['number','letter','_','.'])")
        else:
            raise ValueError("Unsupported value.(Only support Non-blank characters)")

    def __add(self, key, value):
        if key in self.__config.keys():
            self.__update(key, value)
        else:
            self.__config[key] = re.sub(r'(\s)*$', '', value)
            self.__add_log[key] = re.sub(r'(\s)*$', '', value)

    def save(self):
        with open(self.__configfilename, "r") as cfile:
            clines = cfile.readlines()
            for n in range(len(clines)):
                for nkey in self.__update_log.keys():
                    if re.match(r"^%s( |\t)*\=( ||\t)*(\S|.)*$" % nkey, clines[n]):
                        clines[n] = re.sub(r"^%s( |\t)*\=( ||\t)*(\S|.)*$" % nkey,
                                           "%s = %s" % (nkey, self.__update_log[nkey]), clines[n])
            if not re.match(r'.*(\r\n|\r|\n)$', clines[-1]):
                clines[-1] = clines[-1] + "\n"
            clines = clines + ["%s = %s\n" % (nkey, self.__add_log[nkey]) for nkey in self.__add_log.keys()]
        with open(self.__configfilename, "w") as wcfile:
            wcfile.write(reduce(lambda x, y: x + y, clines))
