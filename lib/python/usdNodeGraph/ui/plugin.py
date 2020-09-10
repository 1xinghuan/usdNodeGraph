#
# Copyright 2018 Pixar
#
# Licensed under the Apache License, Version 2.0 (the "Apache License")
# with the following modification; you may not use this file except in
# compliance with the Apache License and the following modification to it:
# Section 6. Trademarks. is deleted and replaced with:
#
# 6. Trademarks. This License does not grant permission to use the trade
#    names, trademarks, service marks, or product names of the Licensor
#    and its affiliates, except as required to comply with Section 4(c) of
#    the License and to reproduce the content of the NOTICE file.
#
# You may obtain a copy of the Apache License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Apache License with the above modification is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the Apache License for the specific
# language governing permissions and limitations under the Apache License.
#

import sys
from pxr import Tf, Plug


class PluginContainer(object):
    def registerPlugins(self):
        pass


PluginContainerTfType = Tf.Type.Define(PluginContainer)


def loadPlugins():
    containerTypes = Plug.Registry.GetAllDerivedTypes(PluginContainerTfType)

    # Find all plugins and plugin container types through libplug.
    plugins = dict()
    for containerType in containerTypes:
        plugin = Plug.Registry().GetPluginForType(containerType)
        pluginContainerTypes = plugins.setdefault(plugin, [])
        pluginContainerTypes.append(containerType)

    # Load each plugin in alphabetical order by name. For each plugin, load all
    # of its containers in alphabetical order by type name.
    allContainers = []
    for plugin in sorted(plugins.keys(), key=lambda plugin: plugin.name):
        plugin.Load()
        pluginContainerTypes = sorted(
            plugins[plugin], key=lambda containerType: containerType.typeName)
        for containerType in pluginContainerTypes:
            if containerType.pythonClass is None:
                print(("WARNING: Missing plugin container '{}' from plugin "
                    "'{}'. Make sure the container is a defined Tf.Type and "
                    "the container's import path matches the path in "
                    "plugInfo.json.").format(
                        containerType.typeName, plugin.name))
                continue
            container = containerType.pythonClass()
            allContainers.append(container)

    # No plugins to load, so don't create a registry.
    if len(allContainers) == 0:
        return None

    for container in allContainers:
        container.registerPlugins()

