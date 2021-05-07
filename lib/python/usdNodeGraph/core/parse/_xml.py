import tempfile
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom


def fixedWritexml(self, writer, indent="", addindent="", newl=""):
    """
    :param indent:
    :param addindent:
    :param newl:
    :return:
    """

    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = list(attrs.keys())
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        if len(self.childNodes) == 1 \
          and self.childNodes[0].nodeType == minidom.Node.TEXT_NODE:
            writer.write(">")
            self.childNodes[0].writexml(writer, "", "", "")
            writer.write("</%s>%s" % (self.tagName, newl))
            return
        writer.write(">%s" % (newl, ))
        for node in self.childNodes:
            if node.nodeType is not minidom.Node.TEXT_NODE:
                node.writexml(writer, indent+addindent, addindent, newl)
        writer.write("%s</%s>%s" % (indent, self.tagName, newl))
    else:
        writer.write("/>%s" % (newl, ))


minidom.Element.writexml = fixedWritexml


def convertToString(element):
    string = ET.tostring(element)
    document = minidom.parseString(string)
    tmpFile = tempfile.mktemp(suffix='.xml')
    with open(tmpFile, 'w') as f:
        document.writexml(f, addindent='\t', newl='\n', encoding='utf-8')
    with open(tmpFile, 'r') as f:
        txt = f.read()
    return txt


