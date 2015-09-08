"""
The MIT License (MIT)

Copyright (c) 2015 Olof Kindgren <olof.kindgren@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import xml.etree.ElementTree as ET

class IpxactInt(int):
    def __new__(cls, *args, **kwargs):
        if not args:
            return super(IpxactInt, cls).__new__(cls)
        elif len(args[0]) > 2 and args[0][0:2] == '0x':
            return super(IpxactInt, cls).__new__(cls, args[0][2:], 16)
        elif "'" in args[0]:
            sep = args[0].find("'")
            if args[0][sep+1] == "h":
                base = 16
            else:
                raise Exception
            return super(IpxactInt, cls).__new__(cls, args[0][sep+2:], base)
        else:
            return super(IpxactInt, cls).__new__(cls, args[0])

class IpxactBool(object):
    def __new__(cls, *args, **kwargs):
        if not args:
            return False
        elif args[0] == 'true':
            return True
        elif args[0] == 'false':
            return False
        else:
            raise Exception

class IpxactItem(object):
    ATTRIBS = {}
    MEMBERS = {}
    CHILDREN = []
    CHILD = []
    def __init__(self, root=None, ns=None):
        self.ns = ns
        for key, value in self.ATTRIBS.items():
            setattr(self, key, value)
        for key, value in self.MEMBERS.items():
            setattr(self, key, value)
        for c in self.CHILDREN:
            setattr(self, c, [])
        for c in self.CHILD:
            setattr(self, c, None)

        if root is not None:
            self.parse_tree(root)

    def parse_tree(self, root):
        if self.ATTRIBS:
            for _name, _type in self.ATTRIBS.items():
                _tagname = '{' + self.ns['spirit'] + '}' + _name
                if _tagname in root.attrib:
                    setattr(self, _name, _type(root.attrib[_tagname]))
        for _name, _type in self.MEMBERS.items():
            tmp = root.find('./spirit:{}'.format(_name), self.ns)
            if tmp is not None and tmp.text is not None:
                setattr(self, _name, _type(tmp.text))
            else:
                setattr(self, _name, _type())

        for c in self.CHILDREN:
            for f in root.findall(".//spirit:{}".format(c), self.ns):
                child = getattr(self, c)
                class_name = c[0].upper() + c[1:]
                t = eval(class_name)(f, self.ns)
                child.append(t)
        for c in self.CHILD:
            f = root.find(".//spirit:{}".format(c), self.ns)
            class_name = c[0].upper() + c[1:]
            t = eval(class_name)(f, self.ns)
            setattr(self, c, t)

    def write(self, root):
        S = '{%s}' % self.ns['spirit']

        for a in self.ATTRIBS:
            root.attrib[a] = getattr(self, a)

        for m in self.MEMBERS:
            ET.SubElement(root, S+m).text = str(getattr(self, m))

        for c in self.CHILDREN:
            for child_obj in getattr(self, c):
                subel = ET.SubElement(root, S+c)
                child_obj.write(subel)
        for c in self.CHILD:
            subel = ET.SubElement(root, S+c)
            getattr(self, c).write(subel)

class EnumeratedValue(IpxactItem):
    MEMBERS = {'name' : str,
               'value' : IpxactInt}

class EnumeratedValues(IpxactItem):
    CHILDREN = ['enumeratedValue']
    
class Field(IpxactItem):
    MEMBERS = {'name'        : str,
               'description' : str,
               'bitOffset'   : IpxactInt,
               'bitWidth'    : IpxactInt,
               'volatile'    : IpxactBool,
               'access'      : str}
    CHILDREN = ['enumeratedValues']

class Register(IpxactItem):
    MEMBERS = {'name'          : str,
               'description'   : str,
               'access'        : str, #FIXME enum
               'addressOffset' : IpxactInt,
               'size'          : IpxactInt,
               'volatile'      : IpxactBool,
               'width'         : IpxactInt}
    CHILDREN = ['field']

class AddressBlock(IpxactItem):
    MEMBERS = {'name'        : str,
               'description' : str,
               'baseAddress' : IpxactInt,
               'range' : IpxactInt,
               'width' : IpxactInt}

    CHILDREN = ['register']

class MemoryMap(IpxactItem):
    MEMBERS = {'name' : str}

    CHILDREN = ['addressBlock']

class MemoryMaps(IpxactItem):
    CHILDREN = ['memoryMap']

class File(IpxactItem):
    MEMBERS = {'name'          : str,
               'fileType'      : str,
               'isIncludeFile' : IpxactBool}

class FileSet(IpxactItem):
    MEMBERS = {'name' : str}

    CHILDREN = ['file']

class FileSets(IpxactItem):
    CHILDREN = ['fileSet']

class Vector(IpxactItem):
    MEMBERS = {'left'  : IpxactInt,
               'right' : IpxactInt}

class PhysicalPort(IpxactItem):
    MEMBERS = {'name' : str}

    CHILD = ['vector']

class LogicalPort(IpxactItem):
    MEMBERS = {'name' : str}

    CHILD = ['vector']

class PortMap(IpxactItem):
    CHILD = ['logicalPort', 'physicalPort']

class PortMaps(IpxactItem):
    CHILDREN = ['portMap']

class BusType(IpxactItem):
    ATTRIBS = {'vendor'  : str,
               'library' : str,
               'name'    : str,
               'version' : str}

class AbstractionType(IpxactItem):
    ATTRIBS = {'vendor'  : str,
               'library' : str,
               'name'    : str,
               'version' : str}

class BusInterface(IpxactItem):
    MEMBERS = {'name'               : str,
               'mirroredMaster'     : str,
    }

    CHILD = ['abstractionType',
             'busType',
             'portMaps']

class BusInterfaces(IpxactItem):
    CHILDREN = ['busInterface']

class Component(IpxactItem):
    MEMBERS = {'vendor'  : str,
               'library' : str,
               'name'    : str,
               'version' : str,
               }
    CHILDREN = ['fileSets', 'memoryMaps']
    CHILD = ['busInterfaces']

class Ipxact:
    nsmap = [('1.4' , 'spirit', 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4'),
             ('1.5' , 'spirit', 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5')]

    ROOT_TAG = 'component'
    def __init__(self, root):
        
        #Warning: Horrible hack to find out which IP-Xact version that is used
        version = ""
        nsval = ""
        for key, value in root.attrib.items():
            if key == '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation':
                nstags = value.split()
                for i in self.nsmap:
                    if i[2] in nstags:
                        nsver = i[0]
                        nskey = i[1]
                        nsval = i[2]

        self.nsver = nsver
        self.nskey = nskey
        self.nsval = nsval
        if not (root.tag == '{'+nsval+'}'+self.ROOT_TAG):
            raise Exception
        self.ns = {nskey : nsval}

        self.component = Component(root, self.ns)
        for c in self.component.MEMBERS:
            child = getattr(self.component,c)
            setattr(self, c, child)
        for c in self.component.CHILDREN:
            child = getattr(self.component, c)
            setattr(self, c, child)
        for c in self.component.CHILD:
            child = getattr(self.component, c)
            setattr(self, c, child)

    def write(self, f):
        print(f)
        ET.register_namespace(self.nskey, self.nsval)
        print(dir(self))
        S = '{%s}' % self.nsval
        root = ET.Element(S+'component')
        self.component.write(root)

        et = ET.ElementTree(root)
        et.write(f, xml_declaration=True, encoding='unicode')#, default_namespace=SPIRIT_NS)
        
