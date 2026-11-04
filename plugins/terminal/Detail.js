.pragma library

function number(value, digits) { return value === null || value === undefined || !isFinite(value) ? "—" : Number(value).toFixed(digits || 0); }
function bytes(value) { return value === null || value === undefined ? "—" : value >= 1073741824 ? number(value/1073741824,1)+" GiB" : number(value/1048576,0)+" MiB"; }
function uptime(value) { return value === null || value === undefined ? "—" : Math.floor(value/86400)+"D "+Math.floor(value/3600)%24+"H "+Math.floor(value/60)%60+"M"; }
function duration(value) { return value ? Math.floor(value/3600)+"H "+Math.floor(value/60)%60+"M" : "—"; }
function isoWeek(date) {
    const day = new Date(Date.UTC(date.getFullYear(),date.getMonth(),date.getDate()));
    day.setUTCDate(day.getUTCDate()+4-(day.getUTCDay() || 7));
    return Math.ceil((((day-new Date(Date.UTC(day.getUTCFullYear(),0,1)))/86400000)+1)/7);
}
function month(year, month) {
    const first=new Date(year,month-1,1,12), offset=(first.getDay()+6)%7, rows=[];
    for(let i=0;i<42;i++) {
        const date=new Date(year,month-1,1-offset+i,12);
        rows.push({year:date.getFullYear(),month:date.getMonth()+1,day:date.getDate(),week:isoWeek(date)});
    }
    return rows;
}
