import QtQuick
Text {
    textFormat: Text.PlainText
    color: Runtime.c("paper-2")
    font.family: Runtime.mono
    font.pixelSize: Runtime.px(11)
    elide: Text.ElideRight
    verticalAlignment: Text.AlignVCenter
}
