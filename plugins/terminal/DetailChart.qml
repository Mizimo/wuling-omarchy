import QtQuick
import "kit" as Kit

Canvas {
    id:chart
    property var samples:[]
    property bool timed:false
    property color ink:Kit.Runtime.c("accent-ink")
    onSamplesChanged:requestPaint()
    onInkChanged:requestPaint()
    onWidthChanged:requestPaint()
    onHeightChanged:requestPaint()
    onPaint: {
        const c=getContext("2d");c.reset();c.strokeStyle=Kit.Runtime.c("line");c.lineWidth=1;
        for(let j=0;j<3;j++) { c.beginPath();c.moveTo(0,j*(height-1)/2);c.lineTo(width,j*(height-1)/2);c.stroke(); }
        const end=Date.now()/1000,start=end-86400;
        let points=[];
        function segment() {
            if(!points.length)return;
            c.beginPath();c.moveTo(points[0][0],height);
            for(const p of points)c.lineTo(p[0],p[1]);
            c.lineTo(points[points.length-1][0],height);c.closePath();c.fillStyle=Qt.rgba(ink.r,ink.g,ink.b,.07);c.fill();
            c.beginPath();c.moveTo(points[0][0],points[0][1]);for(const p of points)c.lineTo(p[0],p[1]);c.strokeStyle=ink;c.stroke();points=[];
        }
        for(let i=0;i<samples.length;i++) {
            const value=timed?samples[i].percent:samples[i];
            if(value===null) { segment();continue; }
            const x=timed?(samples[i].time-start)/86400*width:(60-samples.length+i)*width/59;
            points.push([Math.max(0,Math.min(width,x)),height-1-Math.max(0,Math.min(100,value))*(height-2)/100]);
        }
        segment();
    }
}
