import QtQuick
Canvas {
    property var samples: []
    property color ink: Runtime.c("jade")
    property real ceiling: 100
    onSamplesChanged: requestPaint()
    onInkChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const c = getContext("2d"); c.reset(); c.strokeStyle = ink; c.lineWidth = 1; c.beginPath();
        let connected = false;
        for (let i = 0; i < samples.length; i++) {
            if (samples[i] === null) { connected = false; continue; }
            const x = i * width / Math.max(1, samples.length - 1), y = height - 1 - Math.min(1, Math.max(0, samples[i] / ceiling)) * (height - 2);
            if (connected) c.lineTo(x, y); else c.moveTo(x, y); connected = true;
        }
        c.stroke();
    }
}
