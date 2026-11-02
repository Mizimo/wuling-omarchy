import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import "kit" as Kit
import "Model.js" as Model

Item {
    id: dispatch
    property var shell: null
    property bool opened: false
    property string outputName: ""
    property string mode: "apps"
    property string query: ""
    property int selected: 0
    property var data: ({})
    property string feedback: ""
    property bool pending: false
    property real appearance:0
    property real buildElapsed:0
    readonly property var modes: data.clip_enabled ? ["apps","clip","run","calc","ask"] : ["apps","run","calc","ask"]
    readonly property string search: query.replace(/^[=>?]/, "")
    readonly property var rows: Model.rows(data,mode,search)
    readonly property var result: mode==="calc"?Model.calculate(search):null
    readonly property var outputNames: Quickshell.screens.map(s=>s.name)
    readonly property string targetOutput: outputNames.indexOf(outputName)>=0?outputName:outputNames[0] || ""
    function refresh() { if(reader.running)pending=true;else reader.running=true; }
    function open(payload) {
        mode="apps";query="";selected=0;feedback="";
        outputName=Hyprland.focusedMonitor?Hyprland.focusedMonitor.name:"";
        opened=true;leaving.stop();appearance=0;buildElapsed=0;entering.restart();build.restart();refresh();
    }
    function close() { opened=false;entering.stop();build.stop();leaving.restart();reader.running=false;pending=false;query="";feedback=""; }
    NumberAnimation { id:entering;target:dispatch;property:"appearance";from:0;to:1;duration:Kit.Runtime.reduced?90:150 }
    NumberAnimation { id:leaving;target:dispatch;property:"appearance";to:0;duration:130;onFinished:if(!dispatch.opened)dispatch.data=({}) }
    NumberAnimation { id:build;target:dispatch;property:"buildElapsed";from:0;to:500;duration:500 }
    function dismiss() { close();if(shell)shell.hide("wuling.dispatch"); }
    function changeMode(next) { mode=next;selected=0;if(/^[=>?]/.test(query))query="";feedback=""; }
    function cycle(back) { const i=modes.indexOf(mode);changeMode(modes[(i+(back?modes.length-1:1))%modes.length]); }
    onQueryChanged: {
        const prefix=query[0];if(prefix==="=")mode="calc";else if(prefix===">")mode="run";else if(prefix==="?")mode="ask";
        selected=0;feedback="";
    }
    onRowsChanged: selected=Math.max(0,Math.min(selected,rows.length-1))
    function activate(index) {
        if(action.running)return;
        const value=mode==="calc"?result:rows[index]?String(rows[index].id):null;
        if(value===null || value===undefined)return;
        action.mode=mode;action.command=["wuling","dispatch","activate",mode,"--",value];action.running=true;
    }
    function key(event) {
        if(event.key===Qt.Key_Down)selected=Math.min(rows.length-1,selected+1);
        else if(event.key===Qt.Key_Up)selected=Math.max(0,selected-1);
        else if(event.key===Qt.Key_Tab || event.key===Qt.Key_Backtab)cycle(event.key===Qt.Key_Backtab || !!(event.modifiers&Qt.ShiftModifier));
        else if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter) { if(!event.isAutoRepeat)activate(selected); }
        else if(event.key===Qt.Key_Escape) { if(query)query="";else dismiss(); }
        else return;
        event.accepted=true;
    }
    Process {
        id:reader;command:["wuling","dispatch","snapshot"]
        stdout:StdioCollector {
            onStreamFinished: {
                if(!dispatch.opened)return;
                try { const value=JSON.parse(text);if(value.schema_version===1 && value.apps)dispatch.data=value;else dispatch.feedback=Kit.Runtime.tr("unavailable"); }
                catch(_) { dispatch.feedback=Kit.Runtime.tr("unavailable"); }
            }
        }
        onExited:if(dispatch.pending && dispatch.opened) { dispatch.pending=false;Qt.callLater(dispatch.refresh); }
    }
    Process {
        id:action;property string mode:""
        stdout:StdioCollector {
            onStreamFinished: {
                try { const value=JSON.parse(text);if(value.ok) { if(action.mode==="calc")dispatch.feedback=Kit.Runtime.tr("copied");else dispatch.dismiss(); }else dispatch.feedback=Kit.Runtime.tr(value.error && value.error.code==="agent_unavailable"?"agent-unavailable":"failed"); }
                catch(_) { dispatch.feedback=Kit.Runtime.tr("failed"); }
            }
        }
    }
    FileView {
        path:dispatch.opened?Kit.Runtime.home+"/.local/state/omarchy/clipboard-history.json":""
        watchChanges:dispatch.opened;printErrors:false
        onFileChanged: { reload();dispatch.refresh(); }
    }
    IpcHandler {
        target:"wuling.dispatch"
        function state():string { return JSON.stringify({opened:dispatch.opened,mode:dispatch.mode,rows:dispatch.rows.length,selected:dispatch.selected,busy:reader.running}); }
    }
    Variants {
        model:Quickshell.screens
        PanelWindow {
            id:surface
            required property var modelData
            readonly property bool showing:dispatch.opened && modelData.name===dispatch.targetOutput
            visible:(dispatch.opened || dispatch.appearance>0) && modelData.name===dispatch.targetOutput;screen:modelData;color:"transparent";exclusionMode:ExclusionMode.Ignore
            anchors { top:true;bottom:true;left:true;right:true }
            WlrLayershell.namespace:"wuling-dispatch"
            WlrLayershell.layer:WlrLayer.Overlay
            WlrLayershell.keyboardFocus:showing?WlrKeyboardFocus.Exclusive:WlrKeyboardFocus.None
            onShowingChanged:if(showing)Qt.callLater(function(){input.forceActiveFocus();})
            MouseArea { anchors.fill:parent;onClicked:dispatch.dismiss() }
            FocusScope {
                id:panel
                opacity:dispatch.appearance
                width:Kit.Runtime.px(680);height:Kit.Runtime.px(456)
                anchors.centerIn:parent;scale:Math.min(1,(surface.width-20)/width,(surface.height-20)/height)
                Keys.priority:Keys.BeforeItem;Keys.onPressed:event=>dispatch.key(event)
                MouseArea { anchors.fill:parent;onClicked:input.forceActiveFocus() }
                Canvas {
                    id:plate;anchors.fill:parent
                    property color ink:Kit.Runtime.c("ink-2");property color line:Kit.Runtime.c("line")
                    onInkChanged:requestPaint();onLineChanged:requestPaint();onWidthChanged:requestPaint();onHeightChanged:requestPaint()
                    onPaint: { const c=getContext("2d"),cut=Kit.Runtime.px(16);c.reset();c.beginPath();c.moveTo(.5,.5);c.lineTo(width-cut,.5);c.lineTo(width-.5,cut);c.lineTo(width-.5,height-.5);c.lineTo(.5,height-.5);c.closePath();c.globalAlpha=.98;c.fillStyle=ink;c.fill();c.globalAlpha=1;c.strokeStyle=line;c.lineWidth=1;c.stroke(); }
                }
                Item {
                    id:rail;width:Kit.Runtime.px(72);height:parent.height
                    Rectangle { anchors.right:parent.right;width:1;height:parent.height;color:Kit.Runtime.c("line") }
                    Kit.Micro { x:Kit.Runtime.px(14);y:Kit.Runtime.px(16);text:"01";color:Kit.Runtime.c("accent-ink") }
                    Kit.Label { y:Kit.Runtime.px(44);anchors.horizontalCenter:parent.horizontalCenter;text:Kit.Runtime.language==="en"?"DISPATCH":"調\n度";font.family:Kit.Runtime.language==="en"?Kit.Runtime.display:Kit.Runtime.serif;font.pixelSize:Kit.Runtime.px(Kit.Runtime.language==="en"?12:32);font.weight:Font.Black;horizontalAlignment:Text.AlignHCenter }
                    Rectangle { x:Kit.Runtime.px(12);y:Kit.Runtime.px(78);width:parent.width-Kit.Runtime.px(24);height:1;color:Kit.Runtime.c("accent-ink") }
                    Kit.Micro { anchors.centerIn:parent;rotation:90;text:"DISPATCH · "+dispatch.mode.toUpperCase() }
                    Rectangle { anchors.bottom:parent.bottom;anchors.bottomMargin:Kit.Runtime.px(14);anchors.horizontalCenter:parent.horizontalCenter;width:Kit.Runtime.px(32);height:width;color:Kit.Runtime.c("vermilion");Kit.Label { anchors.centerIn:parent;text:"令";font.family:Kit.Runtime.serif;font.pixelSize:Kit.Runtime.px(19);font.weight:Font.Black;color:"#F4F5EF" } }
                }
                Item {
                    x:rail.width;width:parent.width-x;height:parent.height
                    Rectangle { y:Kit.Runtime.px(52);width:parent.width;height:1;color:Kit.Runtime.c("line") }
                    TextInput {
                        id:input;x:Kit.Runtime.px(18);height:Kit.Runtime.px(52);width:Math.max(Kit.Runtime.px(60),tabs.x-x-Kit.Runtime.px(12))
                        text:dispatch.query;onTextEdited:dispatch.query=text
                        color:Kit.Runtime.c("paper-1");selectionColor:Kit.Runtime.c("fill");selectedTextColor:Kit.Runtime.c("on-accent")
                        font.family:Kit.Runtime.mono;font.pixelSize:Kit.Runtime.px(17);verticalAlignment:TextInput.AlignVCenter;clip:true;selectByMouse:true
                        cursorDelegate:Rectangle { width:1;color:Kit.Runtime.c("accent-ink");visible:input.activeFocus }
                        Component.onCompleted:if(surface.showing)forceActiveFocus()
                        Kit.Label { anchors.fill:parent;verticalAlignment:Text.AlignVCenter;visible:!input.text && !input.preeditText;text:Kit.Runtime.tr("search");font.pixelSize:Kit.Runtime.px(13);color:Kit.Runtime.c("mist-6") }
                    }
                    Row {
                        id:tabs;anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(18);y:Kit.Runtime.px(12);spacing:Kit.Runtime.px(2)
                        Repeater { model:dispatch.modes
                            Rectangle {
                                id:tab
                                required property string modelData
                                readonly property bool selected:dispatch.mode===modelData
                                height:Kit.Runtime.px(21);width:tabLabel.implicitWidth+Kit.Runtime.px(16)
                                color:selected?Kit.Runtime.c("paper-0"):"transparent"
                                Kit.Micro { id:tabLabel;anchors.centerIn:parent;text:Kit.Runtime.tr(tab.modelData);pixels:8.5;color:Kit.Runtime.c(tab.selected?"ink-2":"mist-5") }
                                MouseArea { anchors.fill:parent;onClicked: { dispatch.changeMode(tab.modelData);input.forceActiveFocus(); } }
                            }
                        }
                    }
                    Rectangle { y:Kit.Runtime.px(78);width:parent.width;height:1;color:Kit.Runtime.c("line-soft") }
                    Kit.Micro { x:Kit.Runtime.px(18);y:Kit.Runtime.px(52);height:Kit.Runtime.px(26);verticalAlignment:Text.AlignVCenter;text:dispatch.mode==="calc"?Kit.Runtime.tr("result"):Kit.Runtime.tr("match")+" "+dispatch.rows.length+" · "+Kit.Runtime.tr(dispatch.mode==="apps"?"frecency":"recent") }
                    Kit.Micro { anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(18);y:Kit.Runtime.px(52);height:Kit.Runtime.px(26);verticalAlignment:Text.AlignVCenter;text:dispatch.feedback || (reader.running?Kit.Runtime.tr("loading"):"");color:Kit.Runtime.c("accent-ink") }
                    ListView {
                        id:list;x:0;y:Kit.Runtime.px(79);width:parent.width;height:parent.height-y-Kit.Runtime.px(34);clip:true
                        visible:dispatch.mode!=="calc";model:dispatch.rows;currentIndex:dispatch.selected
                        onCurrentIndexChanged:positionViewAtIndex(currentIndex,ListView.Contain)
                        delegate:Rectangle {
                            id:row;required property var modelData;required property int index
                            readonly property bool selected:index===dispatch.selected
                            width:list.width;height:Kit.Runtime.px(34);color:selected?Kit.Runtime.c("paper-0"):"transparent"
                            opacity:Kit.Runtime.reduced?1:Math.max(0,Math.min(1,(dispatch.buildElapsed-150-Math.min(index,11)*20)/70))
                            Rectangle { width:Kit.Runtime.px(2);height:parent.height;color:row.selected?Kit.Runtime.c("fill"):"transparent" }
                            Kit.Micro { x:Kit.Runtime.px(18);anchors.verticalCenter:parent.verticalCenter;text:String(row.index+1).padStart(3,"0");color:Kit.Runtime.c(row.selected?"ink-5":"mist-6") }
                            Kit.Icon { x:Kit.Runtime.px(52);anchors.verticalCenter:parent.verticalCenter;font.pixelSize:Kit.Runtime.px(18);name:dispatch.mode==="apps"?"apps":dispatch.mode==="clip"?"content_paste":row.modelData.recent?"history":dispatch.mode==="ask"?"smart_toy":"terminal";color:Kit.Runtime.c(row.selected?"ink-2":"mist-4") }
                            Kit.Label { id:nameLabel;x:Kit.Runtime.px(84);anchors.verticalCenter:parent.verticalCenter;width:Math.min(implicitWidth,Math.max(0,chip.x-x-Kit.Runtime.px(10)));text:dispatch.mode==="apps" || dispatch.mode==="clip"?Model.highlight(row.modelData.name,dispatch.search,Kit.Runtime.c(row.selected?"ink-2":"accent-ink")):Model.escaped(row.modelData.name);textFormat:Text.StyledText;font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(13);font.weight:Font.Medium;color:Kit.Runtime.c(row.selected?"ink-2":"paper-1") }
                            Kit.Label { x:nameLabel.x+nameLabel.width+Kit.Runtime.px(12);anchors.verticalCenter:parent.verticalCenter;width:Math.max(0,chip.x-x-Kit.Runtime.px(12));text:row.modelData.detail || "";font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(11);color:Kit.Runtime.c(row.selected?"ink-5":"mist-5") }
                            Rectangle { id:chip;anchors.right:goLabel.left;anchors.rightMargin:Kit.Runtime.px(10);anchors.verticalCenter:parent.verticalCenter;width:chipText.implicitWidth+Kit.Runtime.px(10);height:Kit.Runtime.px(16);color:"transparent";border.width:1;border.color:Kit.Runtime.c(row.selected?"ink-5":"line");Kit.Micro { id:chipText;anchors.centerIn:parent;text:dispatch.mode==="apps"?(row.modelData.terminal?"TUI":"APP"):dispatch.mode.toUpperCase();pixels:7.5;color:Kit.Runtime.c(row.selected?"ink-4":"mist-5") } }
                            Kit.Micro { id:goLabel;anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(18);anchors.verticalCenter:parent.verticalCenter;width:row.selected?implicitWidth:0;visible:row.selected;text:"↵ "+Kit.Runtime.tr("go-"+dispatch.mode);pixels:8.5;color:Kit.Runtime.c("ink-2") }
                            MouseArea { anchors.fill:parent;hoverEnabled:true;onClicked: { if(dispatch.selected===row.index)dispatch.activate(row.index);else dispatch.selected=row.index;input.forceActiveFocus(); } }
                        }
                    }
                    Column {
                        visible:dispatch.mode==="calc";x:Kit.Runtime.px(18);y:Kit.Runtime.px(96);width:parent.width-x*2;spacing:Kit.Runtime.px(6)
                        Kit.Label { width:parent.width;text:dispatch.result===null?"—":dispatch.result;font.pixelSize:Kit.Runtime.px(30);font.weight:Font.DemiBold }
                        Kit.Label { width:parent.width;text:dispatch.search+" =";font.pixelSize:Kit.Runtime.px(11);color:Kit.Runtime.c("mist-5") }
                    }
                    Kit.Label { visible:dispatch.mode!=="calc" && !dispatch.rows.length && !reader.running;x:Kit.Runtime.px(18);y:Kit.Runtime.px(109);width:parent.width-x*2;text:Kit.Runtime.tr("empty");font.family:Kit.Runtime.sans;color:Kit.Runtime.c("mist-5") }
                    Rectangle { anchors.bottom:parent.bottom;anchors.bottomMargin:Kit.Runtime.px(34);width:parent.width;height:1;color:Kit.Runtime.c("line") }
                    Kit.Micro { x:Kit.Runtime.px(18);anchors.bottom:parent.bottom;height:Kit.Runtime.px(34);verticalAlignment:Text.AlignVCenter;text:"↑↓ "+Kit.Runtime.tr("select")+"   ↵ "+Kit.Runtime.tr("go-"+dispatch.mode)+"   TAB "+Kit.Runtime.tr("mode")+"   ESC "+Kit.Runtime.tr("close") }
                    Kit.Micro { anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(18);anchors.bottom:parent.bottom;height:Kit.Runtime.px(34);verticalAlignment:Text.AlignVCenter;text:"SUPER+D" }
                }
            }
        }
    }
}
