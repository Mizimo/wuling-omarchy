import QtQuick
Canvas {
    property color ink: Runtime.c("on-accent")
    onInkChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const context = getContext("2d"); context.reset(); context.fillStyle = ink;
        for (let x = -height; x < width + height; x += 8) {
            context.beginPath(); context.moveTo(x, height); context.lineTo(x + height, 0);
            context.lineTo(x + height + 3, 0); context.lineTo(x + 3, height); context.closePath(); context.fill();
        }
    }
}
