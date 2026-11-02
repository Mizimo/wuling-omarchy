import QtQuick
Canvas {
    property color ink: Runtime.c("on-accent")
    property color ground: Runtime.c("ink-2")
    readonly property real stripe: Runtime.px(4 * Math.SQRT2)
    onInkChanged: requestPaint()
    onGroundChanged: requestPaint()
    onStripeChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const context = getContext("2d"); context.reset();
        context.fillStyle = ground; context.fillRect(0, 0, width, height); context.fillStyle = ink;
        // CSS -45deg, four pixels measured perpendicular to each stripe.
        for (let x = -height; x < width + height; x += stripe * 2) {
            context.beginPath(); context.moveTo(x, height); context.lineTo(x + height, 0);
            context.lineTo(x + height + stripe, 0); context.lineTo(x + stripe, height); context.closePath(); context.fill();
        }
    }
}
