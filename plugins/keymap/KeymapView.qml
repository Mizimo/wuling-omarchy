import QtQuick
import Quickshell
import Quickshell.Wayland
import "kit" as Kit

PanelWindow {
    id:surface
    required property var controller
    property alias query:input.text
    readonly property real scrollY:list.contentY
    readonly property bool inhibited:shortcutGuard.active
    readonly property var rows:controller.listing.rows.filter(row=>!query || ((row.description_key?Kit.Runtime.tr(row.description_key):row.description)+" "+row.keys.map(caps=>caps.join(" ")).join(" ")).toLocaleLowerCase().indexOf(query.toLocaleLowerCase())>=0)
    readonly property int columnCount:Math.max(1,Math.min(6,Math.floor((width-Kit.Runtime.px(210))/Kit.Runtime.px(320))))
    readonly property real railWidth:width<Kit.Runtime.px(900)?Kit.Runtime.px(106):Kit.Runtime.px(180)
    screen:controller.targetScreen;visible:!!controller.targetScreen;color:"transparent";exclusionMode:ExclusionMode.Ignore
    anchors { top:true;bottom:true;left:true;right:true }
    WlrLayershell.namespace:"wuling-keymap"
    WlrLayershell.layer:WlrLayer.Overlay
    WlrLayershell.keyboardFocus:controller.opened?WlrKeyboardFocus.Exclusive:WlrKeyboardFocus.None
    ShortcutInhibitor { id:shortcutGuard;window:surface;enabled:controller.opened;onCancelled:surface.controller.dismiss() }
    Component.onCompleted:input.forceActiveFocus()
    function scroll(direction) { list.contentY=Math.max(0,Math.min(Math.max(0,list.contentHeight-list.height),list.contentY+direction*Kit.Runtime.px(72))); }
    function key(event) {
        if(event.key===Qt.Key_Escape) { if(query)input.text="";else controller.dismiss(); }
        else if(event.key===Qt.Key_Down)scroll(1);
        else if(event.key===Qt.Key_Up)scroll(-1);
        else if(event.key===Qt.Key_PageDown)scroll(Math.max(1,Math.floor(list.height/Kit.Runtime.px(72))-1));
        else if(event.key===Qt.Key_PageUp)scroll(-Math.max(1,Math.floor(list.height/Kit.Runtime.px(72))-1));
        else return;
        event.accepted=true;
    }
    onQueryChanged:list.contentY=0
    Item {
        anchors.fill:parent;opacity:controller.appearance
        Rectangle { anchors.fill:parent;color:Kit.Runtime.c("ink-0");opacity:.86 }
        MouseArea { anchors.fill:parent;onClicked:surface.controller.dismiss() }
        Row {
            x:Kit.Runtime.px(52);y:Kit.Runtime.px(26);spacing:Kit.Runtime.px(12)
            Kit.Micro { text:"06";color:Kit.Runtime.c("accent-ink") }
            Kit.Micro { text:Kit.Runtime.label("keymap");color:Kit.Runtime.c("paper-1") }
        }
        Kit.Label {
            x:(surface.railWidth-width)/2;y:Kit.Runtime.px(74);width:Kit.Runtime.px(80)
            text:Kit.Runtime.tr("vertical");elide:Text.ElideNone;horizontalAlignment:Text.AlignHCenter
            lineHeight:Kit.Runtime.px(67.2);lineHeightMode:Text.FixedHeight
            font.family:Kit.Runtime.serif;font.pixelSize:Kit.Runtime.px(64);font.weight:Font.Black
            color:Kit.Runtime.c("paper-1")
        }
        Rectangle { x:Kit.Runtime.px(36);y:Kit.Runtime.px(140);width:surface.railWidth-Kit.Runtime.px(70);height:1;color:Kit.Runtime.c("fill") }
        Rectangle {
            x:Math.max(surface.railWidth,Kit.Runtime.px(225));y:Kit.Runtime.px(22);width:Math.min(Kit.Runtime.px(400),surface.width-x-Kit.Runtime.px(52));height:Kit.Runtime.px(30)
            color:"transparent";border.width:1;border.color:Kit.Runtime.c("line")
            Kit.Label { x:Kit.Runtime.px(10);anchors.verticalCenter:parent.verticalCenter;text:Kit.Runtime.tr("filter");visible:!input.text;color:Kit.Runtime.c("mist-4") }
            TextInput {
                id:input;x:Kit.Runtime.px(10);width:parent.width-Kit.Runtime.px(20);height:parent.height
                verticalAlignment:TextInput.AlignVCenter;clip:true;selectByMouse:true;activeFocusOnTab:true
                color:Kit.Runtime.c("paper-1");font.family:Kit.Runtime.mono;font.pixelSize:Kit.Runtime.px(12);maximumLength:256
                selectionColor:Kit.Runtime.c("fill");selectedTextColor:Kit.Runtime.c("on-accent")
                Accessible.name:Kit.Runtime.tr("filter")
                Keys.priority:Keys.BeforeItem;Keys.onPressed:event=>surface.key(event)
                Keys.onShortcutOverride:event=>event.accepted=true
            }
        }
        Flickable {
            id:list;x:surface.railWidth;y:Kit.Runtime.px(70);width:surface.width-x-Kit.Runtime.px(52);height:surface.height-y-Kit.Runtime.px(80)
            clip:true;contentWidth:width;contentHeight:columns.height;boundsBehavior:Flickable.StopAtBounds
            flickableDirection:Flickable.VerticalFlick;interactive:true
            MouseArea { anchors.fill:parent;onClicked:input.forceActiveFocus() }
            Row {
                id:columns;width:parent.width;spacing:Kit.Runtime.px(26)
                Repeater {
                    model:surface.columnCount
                    Column {
                        required property int index
                        width:(columns.width-columns.spacing*(surface.columnCount-1))/surface.columnCount;spacing:Kit.Runtime.px(28)
                        readonly property var groups:surface.controller.listing.groups.filter((name,i)=>i%surface.columnCount===index)
                        Repeater {
                            model:parent.groups
                            Column {
                                id:group;required property string modelData
                                readonly property var entries:surface.rows.filter(row=>row.group===modelData)
                                visible:entries.length>0;width:parent.width;spacing:Kit.Runtime.px(8)
                                Kit.Micro { text:Kit.Runtime.label(group.modelData);color:Kit.Runtime.c("paper-1") }
                                Rectangle { width:parent.width;height:1;color:Kit.Runtime.c("line") }
                                Repeater {
                                    model:group.entries
                                    KeymapRow { required property var modelData;width:group.width;entry:modelData }
                                }
                            }
                        }
                    }
                }
            }
            Kit.Label {
                width:parent.width;wrapMode:Text.Wrap;elide:Text.ElideNone;font.pixelSize:Kit.Runtime.px(14)
                text:surface.controller.error || (surface.controller.listing.rows.length?Kit.Runtime.tr("no-matches"):Kit.Runtime.tr("loading"))
                visible:!!surface.controller.error || !surface.rows.length
            }
        }
        Item {
            x:Kit.Runtime.px(52);y:surface.height-Kit.Runtime.px(50);width:surface.width-2*x;height:Kit.Runtime.px(30)
            Rectangle { width:parent.width;height:1;color:Kit.Runtime.c("line") }
            Kit.Micro { y:Kit.Runtime.px(12);text:Kit.Runtime.tr("footer");color:Kit.Runtime.c("paper-2") }
            Kit.Micro { y:Kit.Runtime.px(12);anchors.right:parent.right;text:surface.rows.length+" / "+surface.controller.listing.rows.length;color:Kit.Runtime.c("mist-4") }
        }
    }
}
