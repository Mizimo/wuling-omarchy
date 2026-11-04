import QtQuick
import "kit" as Kit

Column {
    id: list
    property var rows: []
    property bool full: false
    property int limit: 3
    property var expandedKeys: ({})
    signal action(string key, int index)
    signal more()
    spacing: Kit.Runtime.px(6)
    function toggle(key) {
        const next=Object.assign({},expandedKeys);
        if(next[key])delete next[key];else next[key]=true;
        expandedKeys=next;
    }
    onRowsChanged: {
        const next={};for(const entry of rows)if(expandedKeys[entry.key])next[entry.key]=true;
        expandedKeys=next;
    }
    Repeater {
        model:list.full?list.rows:list.rows.slice(0,list.limit)
        CommsRow {
            required property var modelData
            width:list.width;entry:modelData;expanded:list.full || !!list.expandedKeys[modelData.key];expandable:!list.full
            onToggled:list.toggle(modelData.key)
            onInvoke:index=>list.action(modelData.key,index)
        }
    }
    Kit.Button {
        visible:!list.full && list.rows.length>list.limit
        width:parent.width;height:Kit.Runtime.px(25);borderVisible:false
        text:"+"+(list.rows.length-list.limit)+" "+Kit.Runtime.tr("more-count")
        Accessible.name:Kit.Runtime.tr("show-all");onClicked:list.more()
    }
    Kit.Label { width:parent.width;visible:list.rows.length===0;text:Kit.Runtime.tr("no-notifications");color:Kit.Runtime.c("mist-4");wrapMode:Text.Wrap }
}
