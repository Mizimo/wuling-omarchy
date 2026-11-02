import QtQuick
Label {
    property real pixels: 8
    font.pixelSize: Runtime.px(pixels)
    font.weight: Font.Medium
    font.letterSpacing: Runtime.px(pixels * .14)
    height: Runtime.px(pixels)
    color: Runtime.c("mist-5")
}
