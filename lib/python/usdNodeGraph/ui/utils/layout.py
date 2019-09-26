from usdNodeGraph.module.sqt import QFormLayout

def clearLayout(layout):
    if layout is not None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                clearLayout(child.layout())


class FormLayout(QFormLayout):
    def addRow(self, label, widget):
        setattr(widget, 'parentLayout', self)
        return super(FormLayout, self).addRow(label, widget)

    def removeRowWidget(self, widget):
        labelWidget = self.labelForField(widget)
        widget.deleteLater()
        labelWidget.deleteLater()

