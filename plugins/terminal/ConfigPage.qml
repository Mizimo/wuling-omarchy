import QtQuick
import "kit" as Kit

Column {
    id:page
    property var snapshot:({})
    property bool busy:false
    readonly property var values:snapshot.settings || ({})
    readonly property var toggles:[{value:false,label:"OFF"},{value:true,label:"ON"}]
    readonly property var sections:["clock","link","levels","signal","agent","telemetry","comms"]
    property bool editingMusic:false
    signal action(string name,string value)
    signal setting(string key,string value)
    signal focusMoved(var control)
    spacing:Kit.Runtime.px(12)
    function key(event) {}
    function choose(key,value) { if(!busy)setting(key,typeof value==="string"?value:JSON.stringify(value)); }
    function section(key,on) {
        const current=values["terminal.sections"] || [];
        choose("terminal.sections",sections.filter(name=>name===key?on:current.indexOf(name)>=0));
    }
    function music() { choose("login_music",musicPath.text); }
    function result(name,ok) {
        if(name==="login_music" && ok)editingMusic=false;
    }
    onValuesChanged:if(!editingMusic)musicPath.text=String(values.login_music || "")
    Repeater {
        model:["theme","background"]
        Kit.Button {
            required property string modelData
            width:page.width;height:Kit.Runtime.px(38);enabled:!page.busy
            Accessible.name:Kit.Runtime.tr("config-"+modelData)
            onClicked:page.action("config-native",modelData)
            Column {
                x:Kit.Runtime.px(10);anchors.verticalCenter:parent.verticalCenter;width:parent.width-Kit.Runtime.px(42);spacing:Kit.Runtime.px(2)
                Kit.Micro { text:Kit.Runtime.label("config-"+modelData);color:parent.parent.foreground;pixels:8 }
                Kit.Label { width:parent.width;text:page.snapshot[modelData] || "—";elide:Text.ElideMiddle;color:parent.parent.foreground;font.pixelSize:Kit.Runtime.px(10) }
            }
            Kit.Icon { anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(10);anchors.verticalCenter:parent.verticalCenter;name:"launch";color:parent.foreground }
        }
    }
    ConfigChoice {
        title:Kit.Runtime.label("config-language");value:page.values.language;enabled:!page.busy
        options:[{value:"auto",label:Kit.Runtime.tr("automatic")},{value:"en",label:"EN"},{value:"zh-Hant",label:Kit.Runtime.tr("traditional")},{value:"zh-Hans",label:Kit.Runtime.tr("simplified")}]
        onChosen:value=>page.choose("language",value)
    }
    Repeater {
        model:[{key:"sounds",choices:["essential","full","off"]},{key:"motion",choices:["full","reduced"]},{key:"labels",choices:null},{key:"menu.selected",choices:["edge","fill"]}]
        ConfigChoice {
            required property var modelData
            title:Kit.Runtime.label("config-"+modelData.key);value:page.values[modelData.key];enabled:!page.busy
            options:modelData.choices?modelData.choices.map(value=>({value:value,label:Kit.Runtime.tr("choice-"+value)})):page.toggles
            onChosen:value=>page.choose(modelData.key,value)
        }
    }
    DetailHeading { width:parent.width;text:Kit.Runtime.label("config-sections") }
    Repeater {
        model:page.sections
        Row {
            required property string modelData
            width:page.width;height:Kit.Runtime.px(30)
            Kit.Label { width:parent.width-switches.width;height:parent.height;text:Kit.Runtime.label(modelData);font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(12) }
            Row {
                id:switches
                Repeater {
                    model:page.toggles
                    Kit.Button {
                        required property var modelData
                        width:Kit.Runtime.px(38);height:Kit.Runtime.px(24);labelSize:9;text:modelData.label;enabled:!page.busy
                        readonly property string sectionKey:parent.parent.modelData
                        selected:((page.values["terminal.sections"] || []).indexOf(sectionKey)>=0)===modelData.value
                        Accessible.name:Kit.Runtime.tr(sectionKey)+": "+text
                        onClicked:if(!selected)page.section(sectionKey,modelData.value)
                    }
                }
            }
        }
    }
    DetailHeading { width:parent.width;text:Kit.Runtime.label("session") }
    Repeater {
        model:["arrival","exit"]
        ConfigChoice {
            required property string modelData
            title:Kit.Runtime.label("config-"+modelData);value:page.values["session."+modelData];options:page.toggles;enabled:!page.busy
            onChosen:value=>page.choose("session."+modelData,value)
        }
    }
    Column {
        width:parent.width;spacing:Kit.Runtime.px(7)
        Kit.Label { text:Kit.Runtime.label("config-login-music");font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(12) }
        Rectangle {
            width:parent.width;height:Kit.Runtime.px(32);color:Kit.Runtime.c("ink-1");border.width:1;border.color:Kit.Runtime.c(musicPath.activeFocus?"accent-ink":"line")
            TextInput {
                id:musicPath;x:Kit.Runtime.px(8);width:parent.width-Kit.Runtime.px(16);height:parent.height
                verticalAlignment:TextInput.AlignVCenter;clip:true;selectByMouse:true;activeFocusOnTab:true;readOnly:page.busy
                color:Kit.Runtime.c("paper-1");selectionColor:Kit.Runtime.c("fill");selectedTextColor:Kit.Runtime.c("on-accent")
                font.family:Kit.Runtime.mono;font.pixelSize:Kit.Runtime.px(11);maximumLength:4096
                Accessible.name:Kit.Runtime.tr("config-login-music")
                onTextEdited:page.editingMusic=true
                onActiveFocusChanged:if(activeFocus)page.focusMoved(musicPath)
                Keys.onPressed:event=> {
                    if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter) { page.music();event.accepted=true; }
                    else if((event.key===Qt.Key_Left || event.key===Qt.Key_Backspace) && cursorPosition===0)event.accepted=true;
                }
                Keys.onShortcutOverride:event=> { if([Qt.Key_Escape,Qt.Key_Up,Qt.Key_Down].indexOf(event.key)<0)event.accepted=true; }
            }
        }
        Row {
            width:parent.width;spacing:Kit.Runtime.px(6)
            Kit.Button { width:(parent.width-parent.spacing)/2;text:Kit.Runtime.label("apply");enabled:!page.busy;onClicked:page.music() }
            Kit.Button { width:(parent.width-parent.spacing)/2;text:Kit.Runtime.label("clear");enabled:!page.busy;onClicked:page.choose("login_music","") }
        }
    }
    DetailHeading { width:parent.width;text:"OMARCHY" }
    Repeater {
        model:["display","input","font","keys","default-apps"]
        Kit.Button {
            required property string modelData
            width:page.width;height:Kit.Runtime.px(32);text:Kit.Runtime.label("config-"+(modelData==="keys"?"native-keys":modelData));icon:"launch";enabled:!page.busy
            onClicked:page.action("config-native",modelData)
        }
    }
}
