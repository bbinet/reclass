#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#
import os, sys
import fnmatch
from reclass.storage import NodeStorageBase
from yamlfile import YamlFile
from directory import Directory
from reclass.datatypes import Entity
import reclass.errors

FILE_EXTENSION = '.yml'
STORAGE_NAME = 'yaml_fs'

def vvv(msg):
    #print >>sys.stderr, msg
    pass

class ExternalNodeStorage(NodeStorageBase):

    def __init__(self, nodes_uri, classes_uri, default_environment=None,
                 environments=None):
        super(ExternalNodeStorage, self).__init__(STORAGE_NAME)

        if default_environment and not (
                environments and default_environment in environments):
            raise reclass.errors.EnvironmentsConfigError(
                environments, default_environment)
        self._default_environment = default_environment
        self._environments = environments

        def _handle_node_duplicates(name, uri1, uri2):
            raise reclass.errors.DuplicateNodeNameError(self._get_storage_name(),
                                                        name, uri1, uri2)
        self._nodes_uri = nodes_uri
        self._nodes = self._enumerate_inventory(nodes_uri,
                                                duplicate_handler=_handle_node_duplicates)
        self._classes_uri = classes_uri
        try:
            self._classes = {}
            for env in environments:
                self._classes[env] = self._enumerate_inventory(
                    os.path.join(classes_uri, env))
        except TypeError:
            # there is no environments
            self._classes = self._enumerate_inventory(classes_uri)

    nodes_uri = property(lambda self: self._nodes_uri)
    classes_uri = property(lambda self: self._classes_uri)

    def _enumerate_inventory(self, basedir, duplicate_handler=None):
        ret = {}
        def register_fn(dirpath, filenames):
            filenames = fnmatch.filter(filenames, '*{0}'.format(FILE_EXTENSION))
            vvv('REGISTER {0} in path {1}'.format(filenames, dirpath))
            for f in filenames:
                name = os.path.splitext(f)[0]
                uri = os.path.join(dirpath, f)
                if name in ret and callable(duplicate_handler):
                    duplicate_handler(name, os.path.join(basedir, ret[name]), uri)
                ret[name] = os.path.relpath(uri, basedir)

        d = Directory(basedir)
        d.walk(register_fn)
        return ret

    def get_node(self, name):
        vvv('GET NODE {0}'.format(name))
        try:
            relpath = self._nodes[name]
            path = os.path.join(self.nodes_uri, relpath)
            name = os.path.splitext(relpath)[0]
        except KeyError, e:
            raise reclass.errors.NodeNotFound(self.name, name, self.nodes_uri)
        entity = YamlFile(path).get_entity(name, self._default_environment)
        return entity

    def get_class(self, name, nodename=None, env=None):
        vvv('GET CLASS {0}'.format(name))
        try:
            if env is None:
                path = os.path.join(self.classes_uri, self._classes[name])
            else:
                path = os.path.join(
                    self.classes_uri, env, self._classes[env][name])
        except KeyError, e:
            raise reclass.errors.ClassNotFound(self.name, name, self.classes_uri)
        entity = YamlFile(path).get_entity(name, default_environment=env)
        return entity

    def enumerate_nodes(self):
        return self._nodes.keys()
