import QtQuick
Label {
    property string name: ""
    text: Runtime.icon(name)
    font.family: Runtime.iconFont
    font.pixelSize: Runtime.px(18)
    horizontalAlignment: Text.AlignHCenter
    elide: Text.ElideNone
    Accessible.ignored: true
}
