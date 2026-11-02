import QtQuick
import "kit/generated/Tokens.js" as Tokens

Item {
    id: view
    property var controller:null
    property string outputName:""
    readonly property var payload:controller?controller.payload:({})
    readonly property var resolved:payload.resolved || ({})
    readonly property real elapsed:controller?controller.elapsed:0
    readonly property real phase:controller?controller.phase:-1
    readonly property bool reduced:controller?controller.reduced:false
    readonly property real wave:controller?controller.wave:0
    readonly property real wipe:controller?controller.wipe:0
    readonly property bool detailed:!!controller && outputName===controller.owner.primary
    readonly property string language:resolved.language || "en"
    readonly property real ratio:height/768
    readonly property real columnWidth:Math.min(1126*ratio,width-52*ratio)
    readonly property string host:payload.host || "—"
    readonly property var rows:payload.rows || [{key:"compositor",value:"—",ok:false},{key:"shell",value:"—",ok:false},{key:"link",value:"—",ok:false},{key:"operator",value:"—",ok:false}]
    readonly property string mono:Tokens.data.type.mono
    readonly property string serif:Tokens.data.type.cjk_serif
    function tr(key) { return payload.copy && payload.copy[key] || ({welcome:"Welcome back, Endministrator",subtitle:"ENDFIELD INDUSTRIES · TALOS-II"})[key] || key; }
    function c(role) {
        if(role==="yellow")role="fill";
        const mist=Tokens.data.palettes.mist[role] || "#ffff00";
        if(resolved.palette!=="paper" || wave<=0)return mist;
        const target=resolved.colors && resolved.colors[role]?resolved.colors[role].value:mist;
        const a=color(mist),b=color(target);return Qt.rgba(a.r+(b.r-a.r)*wave,a.g+(b.g-a.g)*wave,a.b+(b.b-a.b)*wave,1);
    }
    function color(hex) { return Qt.rgba(parseInt(hex.slice(1,3),16)/255,parseInt(hex.slice(3,5),16)/255,parseInt(hex.slice(5,7),16)/255,1); }
    function decode(text,start,duration) {
        if(reduced)return text;
        const progress=Math.max(0,Math.min(1,(elapsed-start)/duration)),chars=Array.from(text),n=Math.floor(chars.length*progress);
        return chars.map((ch,i)=>i<n || ch===" "?ch:"0123456789ABCDEF"[(i*7+Math.floor(elapsed/45))%16]).join("");
    }
    function p(value) { return value*ratio; }
    // Wipe the whole composition; the scan line is its moving boundary.
    Item {
        id:scene;opacity:1-(controller?controller.fade:0)
        layer.enabled: false
        clip:true
        y:view.wipe*view.height
        height:view.height*(1-view.wipe)
        width:view.width
        Item {
            width:view.width;height:view.height;y:-scene.y
            Rectangle { anchors.fill:parent;color:view.c("ink-0");visible:view.wave<=0 }
            Repeater {
                model:144
                Rectangle {
                    required property int index
                    visible:view.wave>0 && view.wave<1
                    readonly property real noise:Math.sin(index*127.1+311.7)*43758.5453
                    readonly property real threshold:.55*Math.floor(index/16)/8+.35*(noise-Math.floor(noise))
                    readonly property real progress:Math.max(0,Math.min(1,(view.wave-threshold)/.1))
                    x:Math.floor(index%16*view.width/16);y:Math.floor(Math.floor(index/16)*view.height/9)
                    width:Math.ceil(view.width/16)+1;height:Math.ceil(view.height/9)+1
                    color:progress>0 && progress<1?Qt.tint(view.c("ink-0"),Qt.rgba(1,1,0,.12)):view.c("ink-0")
                    opacity:1-progress;border.width:progress>0 && progress<1?1:0;border.color:view.c("yellow")
                }
            }
            Rectangle {
                id:scrim
                readonly property color ground:view.c("ink-0")
                anchors.fill:parent;opacity:view.wave
                gradient:Gradient { orientation:Gradient.Horizontal;GradientStop { position:0;color:Qt.rgba(scrim.ground.r,scrim.ground.g,scrim.ground.b,.82) } GradientStop { position:.46;color:Qt.rgba(scrim.ground.r,scrim.ground.g,scrim.ground.b,.62) } GradientStop { position:.78;color:Qt.rgba(scrim.ground.r,scrim.ground.g,scrim.ground.b,.08) } GradientStop { position:1;color:"transparent" } }
            }
            Repeater {
                model:4
                Item {
                    required property int index
                    x:index%2?view.width-view.p(37):view.p(26);y:index<2?view.p(26):view.height-view.p(37)
                    width:view.p(11);height:width
                    readonly property real progress:view.reduced?1:Math.max(0,Math.min(1,(view.elapsed-index*30)/160))
                    scale:1+.6*(1-progress);opacity:progress
                    Rectangle { anchors.verticalCenter:parent.verticalCenter;width:parent.width;height:1;color:view.c("mist-5") }
                    Rectangle { anchors.horizontalCenter:parent.horizontalCenter;height:parent.height;width:1;color:view.c("mist-5") }
                }
            }
            Text {
                x:view.p(46);y:view.height-view.p(39);text: { const t=Math.max(0,view.elapsed);return "00:00:"+String(Math.floor(t/1000)).padStart(2,"0")+"."+String(Math.floor(t%1000/10)).padStart(2,"0"); }
                font.family:view.mono;font.pixelSize:view.p(9);font.letterSpacing:view.p(1.4);color:view.c("mist-5")
            }
            Text { anchors.right:parent.right;anchors.rightMargin:view.p(46);y:view.height-view.p(39);text:view.decode("EF-WL / "+view.host,0,240);font.family:view.mono;font.pixelSize:view.p(9);font.letterSpacing:view.p(1.4);color:view.c("mist-5") }
            Item {
                id:column;width:view.columnWidth;x:(view.width-width)/2;y:view.p(190)
                Rectangle { width:view.p(6);height:width;y:view.p(1);color:view.c("yellow");opacity:view.reduced || Math.floor(view.elapsed/320)%2===0?1:.2 }
                Text { x:view.p(14);text:view.decode("SYSTEM BOOT",0,240);font.family:view.mono;font.pixelSize:view.p(9);font.letterSpacing:view.p(1.4);color:view.c("paper-2") }
                Text { anchors.right:parent.right;text:"FIELD TERMINAL   V0.1";font.family:view.mono;font.pixelSize:view.p(9);font.letterSpacing:view.p(1.4);color:view.c("mist-5") }
                // Measure each face with the font actually drawn. Measuring
                // 武陵 as mono unnecessarily loaded a second bold CJK face.
                TextMetrics { id:fullTitle;font.family:view.mono;font.pixelSize:view.p(52);font.weight:Font.DemiBold;font.letterSpacing:view.p(1.04);text:view.host+" —  FIELD TERMINAL" }
                TextMetrics { id:fullMark;font.family:view.serif;font.pixelSize:view.p(52);font.weight:Font.Black;text:"武陵" }
                readonly property real titleSize:Math.max(view.p(36),Math.min(view.p(52),view.p(52)*width/Math.max(1,fullTitle.advanceWidth+fullMark.advanceWidth)))
                TextMetrics { id:suffix;font.family:view.mono;font.pixelSize:column.titleSize;font.weight:Font.DemiBold;font.letterSpacing:column.titleSize*.02;text:" —  FIELD TERMINAL" }
                TextMetrics { id:markWidth;font.family:view.serif;font.pixelSize:column.titleSize;font.weight:Font.Black;text:"武陵" }
                TextMetrics { id:hostFit;font.family:view.mono;font.pixelSize:column.titleSize;font.weight:Font.DemiBold;font.letterSpacing:column.titleSize*.02;text:view.host;elide:Text.ElideMiddle;elideWidth:Math.max(0,column.width-suffix.advanceWidth-markWidth.advanceWidth-view.p(8)) }
                readonly property string prefix:hostFit.elidedText+" — "
                readonly property var title:Array.from(prefix+"武陵 FIELD TERMINAL")
                readonly property int typed:view.reduced?title.length:view.phase<0?0:Math.min(title.length,1+Math.floor(view.phase/28))
                readonly property int prefixLength:Array.from(prefix).length
                Row {
                    id:titleRow;y:view.p(35);spacing:0
                    Text { text:column.title.slice(0,Math.min(column.typed,column.prefixLength)).join("");font.family:view.mono;font.pixelSize:column.titleSize;font.weight:Font.DemiBold;font.letterSpacing:column.titleSize*.02;color:view.c("paper-1") }
                    Text { text:column.title.slice(column.prefixLength,Math.min(column.typed,column.prefixLength+2)).join("");font.family:view.serif;font.pixelSize:column.titleSize;font.weight:Font.Black;color:view.c("paper-1") }
                    Text { text:column.typed>column.prefixLength+2?column.title.slice(column.prefixLength+2,column.typed).join(""):"";font.family:view.mono;font.pixelSize:column.titleSize;font.weight:Font.DemiBold;font.letterSpacing:column.titleSize*.02;color:view.c("paper-1") }
                    Rectangle { visible:view.phase>=0 && !view.reduced && column.typed<column.title.length;width:view.p(4);height:column.titleSize;color:view.c("yellow") }
                }
                Text { visible:view.detailed && (view.reduced || view.phase>=600);y:view.p(110);text:view.decode("ENDFIELD INDUSTRIES · TALOS-II",(controller?controller.armedAt:0)+600,160);font.family:view.mono;font.pixelSize:view.p(13);font.weight:Font.Medium;font.letterSpacing:view.p(4.16);color:view.c("paper-2") }
                Text { visible:view.detailed && view.language!=="en" && (view.reduced || view.phase>=600);anchors.right:parent.right;y:view.p(110);text:view.tr("subtitle");font.family:view.mono;font.pixelSize:view.p(9);font.letterSpacing:view.p(1.4);color:view.c("paper-2") }
                Rectangle { y:view.p(140);width:parent.width*(view.reduced?1:Math.max(0,Math.min(1,(view.phase-680)/140)));height:1;color:view.c("line");visible:view.detailed }
                Column {
                    id:log;y:view.p(184);spacing:0;visible:view.detailed
                    Repeater {
                        model:view.rows
                        Row {
                            required property var modelData
                            required property int index
                            height:view.p(19);visible:view.reduced || view.phase>=720+index*110
                            Text { text:"[ ";font.family:view.mono;font.pixelSize:view.p(11);color:view.c("mist-4") }
                            Text { text:!modelData.ok?"--":modelData.key==="operator" && !view.reduced && view.phase<1300?"..":"OK";font.family:view.mono;font.pixelSize:view.p(11);color:modelData.ok?view.c("jade"):view.c("mist-4") }
                            Text { text:" ] "+(modelData.key+" ").padEnd(19,".")+" "+modelData.value;font.family:view.mono;font.pixelSize:view.p(11);font.letterSpacing:view.p(.66);color:view.c("mist-4") }
                            Text { visible:modelData.key==="compositor";text: { const screen=(view.payload.screens || []).find(s=>s.name===view.outputName);return screen?"     "+screen.name+" "+screen.width+"×"+screen.height+"@"+Math.round(screen.refresh):""; } font.family:view.mono;font.pixelSize:view.p(11);color:view.c("paper-1") }
                        }
                    }
                }
                Row {
                    id:progress;y:view.p(184+view.rows.length*19+26);spacing:view.p(3)
                    Repeater { model:20;Rectangle { required property int index;width:view.p(18);height:view.p(6);color:index<Math.floor((view.reduced?1:Math.max(0,Math.min(1,view.phase/1900)))*20)?view.c("yellow"):view.c("ink-4") } }
                }
                Text { visible:view.detailed && (view.reduced || view.phase>=1450);y:progress.y+view.p(18);text:view.decode(view.tr("welcome"),(controller?controller.armedAt:0)+1450,210);font.family:view.mono;font.pixelSize:view.p(9);font.letterSpacing:view.p(1.4);color:view.c("mist-5") }
                Text { y:progress.y+view.p(18);anchors.right:parent.right;text:Math.round((view.reduced?1:Math.max(0,Math.min(1,view.phase/1900)))*100)+"%";font.family:view.mono;font.pixelSize:view.p(9);font.letterSpacing:view.p(1.4);color:view.c("accent-ink") }
            }
        }
    }
    Rectangle { visible:view.wipe>0 && view.wipe<1;y:view.wipe*view.height;width:view.width;height:Math.max(1,view.p(2));color:view.c("yellow") }
}
