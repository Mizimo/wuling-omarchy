import QtQuick
import "kit" as Kit

Item {
    id: frame
    property bool showing: false
    property bool terminalOpen: false
    property var rows: []
    property string number: "08"
    property string pageName: "comms"
    property string retainedPage: "comms"
    property var snapshot: ({})
    property string crumb: ""
    function key(event) { if(pageLoader.item)pageLoader.item.key(event); }
    property string error: ""
    property real progress: 0
    property int direction: 1
    readonly property alias controls: pageBody
    readonly property alias flickable: scroll
    readonly property bool loaded:pageLoader.item!==null
    signal command(string name,string value)
    signal back()
    signal clear()
    signal action(string key, int index)
    visible:showing || progress>0;enabled:showing;clip:true;opacity:progress
    transform:Translate { x:Kit.Runtime.reduced?0:frame.direction*Kit.Runtime.px(24)*(1-frame.progress) }
    onShowingChanged: {
        direction=showing?1:-1;
        motion.to=showing?1:0;motion.restart();
        if(showing) { retainedPage=pageName;scroll.contentY=0; }
    }
    onPageNameChanged:if(pageName) {
        retainedPage=pageName;scroll.contentY=0;
        if(showing) { progress=0;motion.to=1;motion.restart(); }
    }
    NumberAnimation { id:motion;target:frame;property:"progress";duration:Kit.Runtime.reduced?90:220;easing.type:Easing.OutCubic }
    Rectangle { anchors.fill:parent;color:Kit.Runtime.c("ink-2") }
    Kit.Label { anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(12);y:Kit.Runtime.px(50);text:Kit.Runtime.tr(frame.retainedPage+"-mark");font.family:Kit.Runtime.serif;font.pixelSize:Kit.Runtime.px(150);opacity:.045 }
    Item {
        id: pageBody;anchors.fill:parent
        Kit.Button { id:backButton;x:Kit.Runtime.px(14);y:Kit.Runtime.px(8);height:Kit.Runtime.px(24);text:Kit.Runtime.label("back");icon:"chevron_left";sound:"";onClicked:frame.back() }
        Row {
            anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(14);y:Kit.Runtime.px(16);spacing:Kit.Runtime.px(5)
            Kit.Micro { text:frame.number;color:Kit.Runtime.c("accent-ink");pixels:8 }
            Kit.Micro { text:frame.crumb || Kit.Runtime.label("comms-page");width:Math.min(implicitWidth,pageBody.width-Kit.Runtime.px(117));elide:Text.ElideLeft;pixels:8 }
        }
        Rectangle { y:Kit.Runtime.px(39);width:parent.width;height:1;color:Kit.Runtime.c("line") }
        Flickable {
            id:scroll;x:Kit.Runtime.px(14);y:Kit.Runtime.px(40);width:parent.width-Kit.Runtime.px(28)
            height:Math.max(0,hints.y-y-errorLabel.height);contentWidth:width;contentHeight:pageColumn.implicitHeight;clip:true;boundsBehavior:Flickable.StopAtBounds
            Column {
                id:pageColumn;width:scroll.width;spacing:Kit.Runtime.px(8);topPadding:Kit.Runtime.px(12);bottomPadding:Kit.Runtime.px(14)
                Row {
                    visible:frame.retainedPage==="comms";width:parent.width;height:Kit.Runtime.px(26)
                    Kit.Micro { width:parent.width-clearButton.width;anchors.verticalCenter:parent.verticalCenter;text:frame.rows.length+" "+Kit.Runtime.tr("count-unit") }
                    Kit.Button { id:clearButton;text:Kit.Runtime.label("clear-all");enabled:frame.rows.length>0;height:Kit.Runtime.px(26);onClicked:frame.clear() }
                }
                CommsList {
                    visible:frame.retainedPage==="comms";width:parent.width;rows:frame.visible && visible?frame.rows:[];full:true
                    onAction:(key,index)=>frame.action(key,index)
                }
                Loader {
                    id:pageLoader;width:parent.width
                    active:frame.terminalOpen && frame.visible && frame.retainedPage!=="comms"
                    source:({performance:"PerformancePage.qml",power:"PowerPage.qml",audio:"AudioPage.qml",system:"SystemPage.qml",calendar:"CalendarPage.qml"})[frame.retainedPage] || ""
                    onLoaded:item.snapshot=Qt.binding(()=>frame.snapshot)
                }
                Connections {
                    target:pageLoader.item;ignoreUnknownSignals:true
                    function onAction(name,value) { frame.command(name,value); }
                    function onFocusMoved(control) {
                        const point=control.mapToItem(scroll.contentItem,0,0);
                        if(point.y<scroll.contentY || point.y+control.height>scroll.contentY+scroll.height)
                            scroll.contentY=Math.max(0,Math.min(scroll.contentHeight-scroll.height,point.y-scroll.height/2));
                    }
                }
            }
        }
        Rectangle {
            id:bottomFade
            anchors.left:scroll.left;anchors.right:scroll.right;y:scroll.y+scroll.height-height;height:Kit.Runtime.px(14)
            visible:scroll.contentHeight-scroll.contentY-scroll.height>.5
            readonly property color ground:Kit.Runtime.c("ink-2")
            gradient:Gradient { GradientStop { position:0;color:Qt.rgba(bottomFade.ground.r,bottomFade.ground.g,bottomFade.ground.b,0) } GradientStop { position:1;color:bottomFade.ground } }
        }
        Kit.Label { id:errorLabel;x:Kit.Runtime.px(14);width:parent.width-Kit.Runtime.px(28);anchors.bottom:hints.top;text:frame.error;height:text?Kit.Runtime.px(36):0;color:Kit.Runtime.c("vermilion");wrapMode:Text.Wrap }
        Item {
            id:hints;anchors.bottom:parent.bottom;width:parent.width;height:Kit.Runtime.px(30)
            Rectangle { width:parent.width;height:1;color:Kit.Runtime.c("line") }
            Kit.Micro { x:Kit.Runtime.px(14);anchors.verticalCenter:parent.verticalCenter;width:parent.width-Kit.Runtime.px(28);text:Kit.Runtime.tr(frame.retainedPage==="comms"?"page-keys":frame.retainedPage+"-keys");pixels:frame.retainedPage==="comms"?8:7 }
        }
    }
    Rectangle { visible:Kit.Runtime.hud && motion.running && !Kit.Runtime.reduced;width:parent.width;height:1;y:parent.height*frame.progress;color:Kit.Runtime.c("accent-ink") }
}
