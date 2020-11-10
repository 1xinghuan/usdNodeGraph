
import re

COLLECTION_TYPE_NAME = 'Collection'


def exclude(l1, l2):
    l = [i for i in l1 if i not in l2]
    return l


def includeBoth(l1, l2):
    l = [i for i in l1 if i in l2]
    return l


def _getAllPrimPaths(prim, paths):
    paths.append(prim.GetPath().pathString)
    for childPrim in prim.GetChildren():
        _getAllPrimPaths(childPrim, paths)


def resolveOneCELString(string, all, stage=None):
    paths = []
    if '/' not in string and stage is not None:
        collectionPath = '/collection/{}'.format(string)
        prim = stage.GetPrimAtPath(collectionPath)
        if prim.IsValid() and prim.GetTypeName() == COLLECTION_TYPE_NAME:
            cels = [i for i in prim.GetAttribute('CEL').Get()]
            for cel in cels:
                paths.extend(resolveCELString(cel, all, stage))
    elif '*' not in string and '//' not in string:
        paths.append(string)
    else:
        if string.startswith('//'):
            string = string.replace('//', '.*/')
        else:
            string = string.replace('*', '.*')
            string = string.replace('//', '/.*')

        pattern = re.compile(string)
        for i in all:
            if re.match(pattern, i):
                paths.append(i)
    return paths


def resolveCELString(string, all=None, stage=None):
    if all is None and stage is not None:
        all = []
        _getAllPrimPaths(stage.GetPrimAtPath('/'), all)

    def _resolveTempList(templ):
        result = []
        currentOp = '+'
        for i in templ:
            if i in ['+', '-', '^']:
                currentOp = i
            else:
                if isinstance(i, list):
                    currentPaths = _resolveTempList(i)
                else:
                    currentPaths = resolveOneCELString(i, all, stage)

                if currentOp == '+':
                    result.extend(currentPaths)
                elif currentOp == '-':
                    result = exclude(result, currentPaths)
                elif currentOp == '^':
                    result = includeBoth(result, currentPaths)
        return result

    l = ['']
    currentIndex = 0

    for index, i in enumerate(string):
        if i == ' ':
            if l[currentIndex] != '':
                l.append('')
                currentIndex += 1
        elif i in ['-', '+', '^']:
            if l[currentIndex] != '':
                l.append('')
                currentIndex += 1
            l[currentIndex] += i

            l.append('')
            currentIndex += 1

        else:
            l[currentIndex] += i

    string = str(l)

    while "'(" in string:
        string = string.replace("'(", "['")
    while ")'" in string:
        string = string.replace(")'", "']")

    tempList = eval(string)
    resolvedPaths = _resolveTempList(tempList)

    return resolvedPaths


if __name__ == '__main__':
    s = '/root/world/cam_main'
    s = '/root/world/cam_main /root/world/cam_taco'
    s = '/root/world/cam_main + /root/world/cam_taco'
    s = '/root/world/cam_main - /root/world/cam_taco'
    s = '(/root/world/cam*-(/root/world/cam_main /root/world/cam_taco)) + (/root/world/lgt* - /root/world/lgt_rim)'
    s = '/root/world//*Mesh'
    s = '//Mesh'


    all = [
        '/root/world/asset/group1/Mesh',
        '/root/world/asset/group1/aMesh',
        '/root/world/asset/group1/bMesh',
        '/root/world/cam1',
        '/root/world/cam2',
        '/root/world/cam_main',
        '/root/world/cam_taco',
        '/root/world/lgt1',
        '/root/world/lgt_rim',
    ]

    print resolveCELString(s, all)

