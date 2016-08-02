# -*- coding:utf8 -*-

import imp
import os


class JsonRPC(object):
    def __init__(self, json_data):
        self.json_data = json_data
        self.response = Response()

    def call_method(self):
        autoload = AutoLoad(self.json_data["method"])
        try:
            for func in (autoload.is_valid_module, autoload.is_valid_method):
                if not func():
                    return False
            return autoload.call_method()
        except LoadError as e:
            self.response.error = e.args[0]

    def validate_mandatory(self):
        mandatory = ("jsonrpc", "id", "method", "params")

        for i in mandatory:
            if i not in self.json_data:
                self.response.error = "{0} is mandatory".format(i)
                return False
        return True

    def validate_null(self):
        not_null = ("jsonrpc", "id", "method")

        for i in not_null:
            if not self.json_data[i]:
                self.response.error = "{0} cannot be null".format(i)
                return False
        return True

    def validate_jsonrpc(self):
        if self.json_data["jsonrpc"] == "2.0":
            return True
        else:
            self.response.error = "jsonrpc is not 2.0"
            return False

    def validate_method(self):
        if self.json_data['method'].count('.') == 1 and self.json_data['method'].split('.')[0] and \
                self.json_data['method'].split('.')[1]:
            return True
        else:
            self.response.error = "the format of method is wrong"

    def validate_id(self):
        if isinstance(self.json_data['id'], int):
            return True
        else:
            self.response.error = "id is not number"

    def validate_auth(self):
        no_login_method = ("user.login", "api.info")

        if self.json_data["method"] in no_login_method:
            pass
        elif self.json_data.get("auth", None):
            if not self.auth():
                return False
        else:
            self.response.error = "auth needed"
            return False
        return True

    def validate(self):
        for func in (self.validate_mandatory, self.validate_null, self.validate_jsonrpc, self.validate_method,
                     self.validate_id, self.validate_auth):
            if not func():
                return False
        return True

    def auth(self):
        auth_string = ("string1", "string2")
        if self.json_data["auth"] in auth_string:
            return True
        self.response.error = "auth failed"
        return False

    def execute(self):
        if not self.validate():
            return False

        self.response.id = self.json_data["id"]
        method = self.call_method()
        if method:
            try:
                self.response.result = method(**self.json_data["params"])
            except Exception as e:
                self.response.error = e.args[0]


class AutoLoad(object):
    def __init__(self, module_method, path="modules"):
        file_dir = os.path.dirname(__file__)
        abs_path = os.path.abspath(file_dir)
        self.path = [os.path.join(abs_path, path)]
        self.module = module_method.split(".")[0].lower()
        self.method = module_method.split(".")[1].lower()
        self.load_module = None

    def is_valid_module(self):
        try:
            fp, path, desc = imp.find_module(self.module, self.path)
        except ImportError:
            raise LoadError("module '{0}' not found".format(self.module, self.path))
        fp.close()
        return True

    def is_valid_method(self):
        fp, path, desc = imp.find_module(self.module, self.path)
        self.load_module = imp.load_module(self.module, fp, path, desc)
        if not getattr(self.load_module, self.method, None):
            raise LoadError("method '{0}' not found".format(self.method))
        elif not callable(getattr(self.load_module, self.method)):
            raise LoadError("'{0}' not callable".format(self.method))
        else:
            pass
        fp.close()
        return True

    def call_method(self):
        return getattr(self.load_module, self.method)


class Response(object):
    def __init__(self):
        self.id = None
        self.result = None
        self.error = None
        self.json_rpc = "2.0"

    def to_dict(self):
        _dict = dict()
        for x, y in self.__dict__.iteritems():
            if callable(y) or not y:
                pass
            else:
                _dict[x] = y
        if not _dict.get('id', None):
            _dict['id'] = -1
        return _dict


class LoadError(Exception):
    pass
