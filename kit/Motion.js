.pragma library

// Cubic-bezier(.2,.8,.2,1), with x inverted before evaluating y.
function snap(progress) {
    const x=Math.max(0,Math.min(1,progress));
    let low=0,high=1,t=x;
    for(let i=0;i<12;i++) {
        const value=3*(1-t)*(1-t)*t*.2+3*(1-t)*t*t*.2+t*t*t;
        if(value<x)low=t;else high=t;
        t=(low+high)/2;
    }
    return x===0?0:x===1?1:3*(1-t)*(1-t)*t*.8+3*(1-t)*t*t+t*t*t;
}
