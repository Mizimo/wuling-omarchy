import QtQuick
import Quickshell
import Quickshell.Io
import qs.Ui as Ui
import "kit" as Kit

Ui.Panel {
    id: terminal
    moduleName: "wuling.terminal"
    manageIpc: false // Shell routes to the instance on the focused output.
    implicitWidth: bar && bar.vertical ? bar.barSize : Kit.Runtime.px(Kit.Runtime.setting("labels") ? 86 : 34)
    implicitHeight: bar ? bar.barSize : Kit.Runtime.px(30)
    property var state: ({})
    property var actionQueue: []
    property string actionError: ""
    property bool restartingCollector: false
    property var collectingSections: []
    property string hostname: ""
    property string pageName: ""
    property string pageNumber: "08"
    property string pageSection: "comms"
    readonly property string screenName: QsWindow.window && QsWindow.window.screen ? QsWindow.window.screen.name : ""
    property var logRows: []
    FileView { path: "/etc/hostname"; printErrors: false; onLoaded: terminal.hostname = text().trim().toUpperCase() }
    readonly property var sections: Kit.Runtime.setting("terminal.sections")
    readonly property var activeSections: pageName ? sections.filter(key => key === "clock").concat([pageName]) : sections
    onSectionsChanged: { if(pageName === "comms" && sections.indexOf("comms")<0)backPage(); else restartCollector(); }
    onPageNameChanged: restartCollector()
    function restartCollector() {
        if (!opened) return;
        restartingCollector = true;
        collector.running = false;
        if (!collector.running) Qt.callLater(startCollector);
    }
    function startCollector() {
        if (collector.running || !opened || !activeSections.length) return;
        collectingSections = activeSections.slice();
        restartingCollector = false;
        collector.command = ["wuling", "status", "--watch", "--sections"].concat(collectingSections);
        collector.running = true;
    }
    readonly property var shown: sections.filter(key => key !== "agent" || (state.agent || []).length > 0)
        .filter(key => key !== "link" || (state.link || []).length > 0)
        .filter(key => key !== "comms" || !!state.comms && state.comms.available)
        .filter(key => key !== "levels" || !!state.levels && (state.levels.volume !== null || state.levels.brightness !== null))
    function number(key) { return String(shown.indexOf(key) + 2).padStart(2, "0"); }
    function has(key) { return shown.indexOf(key) >= 0; }
    function geometry() { return {open:opened, x:panel.cardOrigin.x, y:panel.cardOrigin.y, width:panel.contentWidth, height:panel.contentHeight}; }
    function reportGeometry() { geometryChanged.restart(); }
    Timer {
        id:geometryChanged; interval:0
        onTriggered: if(terminal.screenName)Quickshell.execDetached(["omarchy-shell", "-q", "wuling.notifications", "terminal", terminal.screenName, JSON.stringify(terminal.geometry())]);
    }
    function history() {
        return openPage("comms");
    }
    function openPage(name, source) {
        const section=source || ({comms:"comms",performance:"telemetry",power:"telemetry",audio:"levels",system:"clock",calendar:"clock"})[name];
        if(!section || name==="comms" && sections.indexOf("comms")<0 || bar && bar.barHidden)return "off";
        const index=shown.indexOf(section)>=0?shown.indexOf(section):sections.indexOf(section);
        pageNumber=String(Math.max(0,index)+2).padStart(2,"0");pageSection=section;
        pageName=name;scroll.contentY=0;actionError="";open();Kit.Runtime.cue("select");
        body.resetNavigation();return "ok";
    }
    function backPage() {
        if(!pageName)return false;
        pageName="";actionError="";Kit.Runtime.cue("close");body.resetNavigation();return true;
    }
    IpcHandler {
        enabled: terminal.screenName !== ""
        target: "wuling.terminal." + terminal.screenName
        function geometry(): string { return JSON.stringify(terminal.geometry()); }
        function history(): string { return terminal.history(); }
        function page(name: string): string { return terminal.openPage(name); }
        function state(): string { return JSON.stringify({open:terminal.opened,page:terminal.pageName,sections:terminal.opened?terminal.collectingSections:[],historyRows:terminal.logRows.length,detailLoaded:detail.loaded,spectrum:signalPanel.inspection()}); }
    }
    function act(name, value) {
        const next = ["wuling", "action", name]; if (value !== undefined) next.push(String(value));
        // Slider drags retain the latest pending value, not a queue of stale
        // commands. Discrete clicks remain ordered and bounded.
        let queue = actionQueue.filter(row => !(["volume", "brightness"].indexOf(name) >= 0 && row[2] === name || name==="audio-volume" && row[2]===name && JSON.parse(row[3]).id===JSON.parse(value).id && JSON.parse(row[3]).serial===JSON.parse(value).serial));
        actionQueue = queue.concat([next]).slice(-16); runNext();
    }
    function runNext() {
        if (actionProcess.running || !actionQueue.length) return;
        actionProcess.command = actionQueue[0]; actionQueue = actionQueue.slice(1); actionProcess.running = true;
    }
    function tileValue(tile) {
        const word = tile.active ? "On" : "Off";
        if(tile.id === "wifi" && tile.network)return tile.network;
        if(tile.id === "tailscale" && tile.active)return Kit.Runtime.tr("connected");
        if (tile.id === "power") {
            const value = ({balanced:"Balanced", performance:"Performance", "power-saver":"Saver"})[tile.state] || tile.state;
            return Kit.Runtime.language === "en" ? value : Kit.Runtime.tr(tile.state) + " " + value;
        }
        if (Kit.Runtime.language === "en") return word;
        return ["dnd", "night"].indexOf(tile.id) >= 0 ? Kit.Runtime.tr(tile.id) + " " + word : word + " " + Kit.Runtime.tr(tile.active ? "on" : "off");
    }
    function foot(action) { close(); act(action); }
    onOpenedChanged: {
        Kit.Runtime.cue(opened ? "open" : "close");
        if (!opened) { collector.running = false; restartingCollector = false; pageName="";state = ({});overviewComms.expandedKeys=({}); }
        else { actionError = ""; startCollector(); body.resetNavigation(); }
        reportGeometry();
    }
    onScreenNameChanged: reportGeometry()
    Component.onDestruction: if (screenName) Quickshell.execDetached(["omarchy-shell", "-q", "wuling.notifications", "terminal", screenName, '{"open":false,"width":0}'])
    onStateChanged: {
        if(opened && state.comms===undefined)return;
        const rows=state.comms && state.comms.available ? state.comms.items : [];
        // Unchanged status samples must not destroy a row underneath a press.
        if(JSON.stringify(rows)!==JSON.stringify(logRows))logRows=rows;
    }
    Process {
        id: collector
        onExited: if (terminal.restartingCollector) Qt.callLater(terminal.startCollector)
        stdout: SplitParser {
            onRead: line => { try { const data = JSON.parse(line); if (terminal.opened && !terminal.restartingCollector && JSON.stringify(terminal.collectingSections)===JSON.stringify(terminal.activeSections) && data.schema_version === 1) terminal.state = data; } catch (_) {} }
        }
    }
    Process {
        id: actionProcess
        stdout: StdioCollector {
            onStreamFinished: {
                try { const response = JSON.parse(text); terminal.actionError = response.error ? Kit.Runtime.tr(response.error.code === "panel_unavailable" ? "panel-unavailable" : "action-failed") : ""; }
                catch (_) { terminal.actionError = Kit.Runtime.tr("unavailable"); }
                if (terminal.actionError) Kit.Runtime.cue("deny");
                else if(["performance-monitor","system-fastfetch"].indexOf(actionProcess.command[2])>=0)terminal.close();
            }
        }
        onExited: Qt.callLater(terminal.runNext)
    }
    Kit.Button {
        id: button; anchors.fill: parent; host: terminal.bar
        sound: ""
        borderVisible: false
        accent: Kit.Runtime.hud; selected: terminal.opened
        chamfer: Kit.Runtime.hud ? Kit.Runtime.px(8) : 0
        chamferLeft: true
        Accessible.name: Kit.Runtime.tr("terminal")
        onClicked: terminal.toggle()
        Row {
            anchors.centerIn: parent; spacing: Kit.Runtime.px(7)
            Kit.Icon { name: "side_navigation"; color: button.foreground; anchors.verticalCenter: parent.verticalCenter; font.pixelSize: Kit.Runtime.px(16) }
            Column {
                visible: Kit.Runtime.setting("labels") && !(terminal.bar && terminal.bar.vertical)
                anchors.verticalCenter: parent.verticalCenter; spacing: Kit.Runtime.px(1)
                Kit.Label { text: "TERMINAL"; font.pixelSize: Kit.Runtime.px(Kit.Runtime.language === "en" ? 9 : 8); color: button.foreground }
                Kit.Label { visible: Kit.Runtime.language !== "en"; text: Kit.Runtime.tr("terminal"); font.pixelSize: Kit.Runtime.px(11); color: button.foreground }
            }
        }
    }
    Ui.KeyboardPanel {
        id: panel
        anchorItem: button
        bar: terminal.bar
        owner: terminal
        open: terminal.opened
        padding: 0
        margin: Kit.Runtime.px(10)
        gap: Kit.Runtime.px(10)
        contentWidth: Math.min(Kit.Runtime.g("terminal_width"), availableCardWidth)
        onContentWidthChanged: if (terminal.opened) terminal.reportGeometry()
        onContentHeightChanged: if (terminal.opened) terminal.reportGeometry()
        onCardOriginChanged: if (terminal.opened) terminal.reportGeometry()
        contentHeight: availableCardHeight
        focusTarget: body
        popoutSwitching: terminal.popoutSwitching
        popoutSwitchClosing: terminal.popoutSwitchClosing
        FocusScope {
            id: body; anchors.fill: parent; focus: true
            function controls(item, result) {
                if (!item.visible || !item.enabled) return;
                if (item.activeFocusOnTab) result.push(item);
                for (let i = 0; i < item.children.length; i++) controls(item.children[i], result);
            }
            function resetNavigation() {
                function blur(item) {
                    item.focus=false;
                    for(let i=0;i<item.children.length;i++)blur(item.children[i]);
                }
                blur(body);body.forceActiveFocus();
            }
            function move(direction) {
                let list = [];
                if(terminal.pageName)controls(detail.controls,list);else { controls(contents,list);controls(foot,list); }
                // A focused child and its FocusScope can both be active.
                // Continue from the deepest control, not its enclosing level.
                let index=-1;for(let i=0;i<list.length;i++)if(list[i].activeFocus)index=i;
                if (!list.length) return;
                const next = index < 0 ? (direction > 0 ? 0 : list.length - 1) : (index + direction + list.length) % list.length;
                const target = list[next]; target.forceActiveFocus();
                const area=terminal.pageName?detail.flickable:scroll;
                const point=target.mapToItem(area.contentItem,0,0);
                if(point.y>=0 && point.y<area.contentHeight)area.contentY=Math.max(0,Math.min(area.contentHeight-area.height,point.y-area.height/2));
            }
            Keys.onPressed: event => {
                event.accepted=false;
                if(terminal.pageName)detail.key(event);
                if(event.accepted)return;
                if (event.key === Qt.Key_Escape) { if(!terminal.backPage())terminal.close(); event.accepted = true; }
                else if(terminal.pageName && (event.key===Qt.Key_Left || event.key===Qt.Key_Backspace)) { terminal.backPage();event.accepted=true; }
                else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) { terminal.switchPanel(event.key === Qt.Key_Backtab || event.modifiers & Qt.ShiftModifier ? -1 : 1); event.accepted = true; }
                else if ([Qt.Key_Down, Qt.Key_Up].indexOf(event.key) >= 0) { move(event.key === Qt.Key_Down ? 1 : -1); event.accepted = true; }
            }
            Rectangle {
                id: header; width: parent.width; height: Kit.Runtime.hud ? Kit.Runtime.px(26) : 0; visible: height > 0
                color: Kit.Runtime.c("fill")
                Kit.Label { id: headerTitle; x: Kit.Runtime.px(14); height: parent.height; text: "FIELD TERMINAL"; color: Kit.Runtime.c("on-accent"); font.pixelSize: Kit.Runtime.px(10); font.weight: Font.Bold; font.letterSpacing: Kit.Runtime.px(1.6) }
                Kit.Label { id: headerHost; anchors.right: parent.right; anchors.rightMargin: Kit.Runtime.px(14); width: Math.min(implicitWidth, Kit.Runtime.px(105)); height: parent.height; text: terminal.hostname; color: Kit.Runtime.c("on-accent"); font.pixelSize: Kit.Runtime.px(10); font.weight: Font.Bold }
                Kit.Hazard { anchors.left: headerTitle.right; anchors.right: headerHost.left; anchors.margins: Kit.Runtime.px(10); anchors.verticalCenter: parent.verticalCenter; height: Kit.Runtime.px(6); ink: Kit.Runtime.c("on-accent"); ground: header.color }
            }
            Flickable {
                id: scroll; anchors.top: header.bottom; anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: errorLabel.top
                interactive:terminal.pageName===""
                contentWidth: width; contentHeight: contents.height; clip: true
                boundsBehavior: Flickable.StopAtBounds
                Column {
                    id: contents; width: scroll.width
                    component Part: Item {
                        default property alias contentData: sectionContent.data
                        implicitHeight: layout.height + Kit.Runtime.px(10) + 1
                        id: part
                        property string sectionKey: ""
                        property bool revealed: false
                        visible: terminal.has(sectionKey)
                        width: contents.width
                        opacity: revealed ? 1 : 0
                        function reveal() {
                            if (!terminal.opened) { entry.stop(); revealed = false; }
                            else if (visible && !revealed) entry.restart();
                        }
                        onVisibleChanged: reveal()
                        Component.onCompleted: reveal()
                        Connections { target: terminal; function onOpenedChanged() { part.reveal(); } }
                        Timer { id: entry; interval: Kit.Runtime.reduced ? 0 : 150 + Math.min(12, Math.max(0, terminal.shown.indexOf(part.sectionKey))) * (Kit.Runtime.hud ? 60 : 20); onTriggered: part.revealed = true }
                        Behavior on opacity { NumberAnimation { duration: 90 } }
                        property Column layout: Column {
                            parent: part; width: part.width
                            Kit.Section {
                                width: parent.width; number: terminal.number(part.sectionKey); title: Kit.Runtime.label(part.sectionKey === "signal" && !terminal.state.signal ? "no-signal-head" : part.sectionKey); detail: ""
                                Kit.Button {
                                    visible:part.sectionKey==="clock";anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(14);y:Kit.Runtime.px(4)
                                    height:Kit.Runtime.px(22);text:Quickshell.env("USER");labelSize:8;borderVisible:false;onClicked:terminal.openPage("system")
                                }
                                Rectangle {
                                    visible:part.sectionKey==="comms";anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(14);y:Kit.Runtime.px(6)
                                    width:headingActions.implicitWidth;height:Kit.Runtime.px(20);color:Kit.Runtime.c("ink-2")
                                    Row { id:headingActions;spacing:Kit.Runtime.px(5)
                                    Kit.Micro { anchors.verticalCenter:parent.verticalCenter;text:terminal.logRows.length+" "+Kit.Runtime.tr("count-unit");pixels:7.5 }
                                    Kit.Button { height:Kit.Runtime.px(20);text:Kit.Runtime.label("clear-all");labelSize:8;borderVisible:false;enabled:terminal.logRows.length>0;onClicked:terminal.act("comms-clear") }
                                    }
                                }
                            }
                            Column { id: sectionContent; width: parent.width; topPadding: Kit.Runtime.px(8) }
                        }
                        property Rectangle divider: Rectangle {
                            parent: part; anchors.bottom: parent.bottom; width: parent.width; height: 1
                            visible: terminal.shown[terminal.shown.length - 1] !== part.sectionKey
                            color: Kit.Runtime.c("line")
                        }
                        property Rectangle scan: Rectangle {
                            parent: part
                            visible: Kit.Runtime.hud && !Kit.Runtime.reduced && sweep.running
                            width: parent.width; height: 1; color: Kit.Runtime.c("accent-ink")
                            property real progress: 0
                            y: progress * part.height
                            NumberAnimation on progress { id: sweep; from: 0; to: 1; duration: 160; running: part.revealed && terminal.opened }
                        }
                    }
                    Part {
                        id:clockPart
                        sectionKey: "clock"
                        Item {
                            width: parent.width; height: Kit.Runtime.g("terminal_clock_size") * .9 + Kit.Runtime.px(2)
                            activeFocusOnTab:true
                            Accessible.role:Accessible.Button;Accessible.name:Kit.Runtime.tr("calendar")
                            Keys.onReturnPressed:terminal.openPage("calendar")
                            Keys.onEnterPressed:terminal.openPage("calendar")
                            Rectangle { anchors.fill:parent;color:"transparent";border.width:parent.activeFocus?1:0;border.color:Kit.Runtime.c("accent-ink") }
                            MouseArea { anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:terminal.openPage("calendar") }
                            Kit.Label { id: hours; x: Kit.Runtime.px(14); anchors.bottom: parent.bottom; anchors.bottomMargin: Kit.Runtime.px(2); height: Kit.Runtime.g("terminal_clock_size") * .9; text: terminal.state.clock ? terminal.state.clock.time.slice(0, 5) : "—:—"; font.family: Kit.Runtime.display; font.weight: Font.DemiBold; font.pixelSize: Kit.Runtime.g("terminal_clock_size"); color: Kit.Runtime.c("paper-1") }
                            Kit.Label { x: hours.x + hours.width + Kit.Runtime.px(5); anchors.bottom: hours.bottom; anchors.bottomMargin: Kit.Runtime.px(4); text: terminal.state.clock ? terminal.state.clock.time.slice(5) : ""; font.family: Kit.Runtime.display; font.pixelSize: Kit.Runtime.px(18); font.weight: Font.DemiBold; height: Kit.Runtime.px(18); color: Kit.Runtime.c("accent-ink") }
                            Column {
                                anchors.right: parent.right; anchors.rightMargin: Kit.Runtime.px(14); anchors.bottom: parent.bottom; anchors.bottomMargin: Kit.Runtime.px(2); spacing: Kit.Runtime.px(4)
                                Kit.Micro { anchors.right: parent.right; text: { const c = terminal.state.clock; if (!c) return ""; const day = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][c.weekday - 1]; return c.date.slice(0, 4) + " · " + day + (Kit.Runtime.language === "en" ? "" : " " + Kit.Runtime.tr("weekday-" + c.weekday)); } }
                                Kit.Label { anchors.right: parent.right; height: Kit.Runtime.px(14.4); text: terminal.state.clock ? terminal.state.clock.date.slice(5).replace("-", ".") + " · " + terminal.state.clock.zone : ""; font.pixelSize: Kit.Runtime.px(12); font.weight: Font.DemiBold; font.letterSpacing: Kit.Runtime.px(.72); color: Kit.Runtime.c("paper-1") }
                                Kit.Micro { anchors.right: parent.right; text: { const n = terminal.state.clock ? terminal.state.clock.uptime_seconds : 0; return "UPTIME " + Math.floor(n / 3600) + "H " + Math.floor(n / 60) % 60 + "M"; } }
                            }
                        }
                    }
                    Part {
                        sectionKey: "link"
                        Grid {
                            x: Kit.Runtime.px(14); columns: 3; spacing: Kit.Runtime.px(6)
                            Repeater {
                                model: terminal.state.link || []
                                Kit.Button {
                                    required property var modelData
                                    sound: "toggle"
                                    width: (contents.width - Kit.Runtime.px(40)) / 3; height: Kit.Runtime.px(52)
                                    selected: modelData.active
                                    Accessible.name: Kit.Runtime.tr(modelData.id)
                                    onClicked: modelData.id==="power"?terminal.openPage("power","link"):terminal.act(modelData.action)
                                    onRightClicked: terminal.act("panel", modelData.id)
                                    Kit.Icon { x: Kit.Runtime.px(8); y: Kit.Runtime.px(7); name: ({wifi:"wifi",bluetooth:"bluetooth",tailscale:"hub",dnd:"do_not_disturb_on",night:"bedtime",power:"speed"})[parent.modelData.id]; color: parent.foreground; font.pixelSize: Kit.Runtime.px(15) }
                                    Kit.Micro { anchors.right: parent.right; anchors.rightMargin: Kit.Runtime.px(8); y: Kit.Runtime.px(10); text: ({wifi:"WI-FI", bluetooth:"BT", tailscale:"TAILNET", dnd:"DND", night:"NIGHT", power:"POWER"})[parent.modelData.id]; color: parent.foreground; pixels: 7.5 }
                                    Kit.Label { x: Kit.Runtime.px(8); y: Kit.Runtime.px(31); width: parent.width - Kit.Runtime.px(16); text: terminal.tileValue(parent.modelData); color: parent.foreground; font.family: Kit.Runtime.sans }
                                }
                            }
                        }
                    }
                    Part {
                        sectionKey: "levels"
                        Kit.Level { x: Kit.Runtime.px(14); width: parent.width - Kit.Runtime.px(28); visible: !!terminal.state.levels && !!terminal.state.levels.volume; name: Kit.Runtime.tr("volume"); iconNavigation:true; onIconClicked:terminal.openPage("audio"); icon: terminal.state.levels && terminal.state.levels.volume && terminal.state.levels.volume.muted ? "volume_off" : "volume_up"; value: terminal.state.levels && terminal.state.levels.volume ? terminal.state.levels.volume.percent : 0; onAdjusted: percent => terminal.act("volume", Math.round(percent)) }
                        Kit.Level { x: Kit.Runtime.px(14); width: parent.width - Kit.Runtime.px(28); visible: !!terminal.state.levels && terminal.state.levels.brightness !== null; name: Kit.Runtime.tr("brightness"); iconNavigation:true; onIconClicked:terminal.act("panel","night"); icon: "brightness_6"; fill: Kit.Runtime.c("paper-2"); value: terminal.state.levels && terminal.state.levels.brightness !== null ? terminal.state.levels.brightness : 0; onAdjusted: percent => terminal.act("brightness", Math.round(percent)) }
                    }
                    Part {
                        sectionKey: "signal"
                        Signal {
                            id:signalPanel
                            x:Kit.Runtime.px(14);width:parent.width-Kit.Runtime.px(28)
                            player:terminal.state.signal || null
                            collecting:terminal.opened && terminal.pageName==="" && terminal.has("signal")
                            onAction:name=>terminal.act(name)
                        }
                    }
                    Part {
                        sectionKey: "agent"
                        id:agentPart
                        function shortLabel(value) { return String(value || "").replace(/\s*\([^)]*\)/g, "").trim().toUpperCase(); }
                        FontMetrics { id:agentLabelMetrics;font.family:Kit.Runtime.mono;font.pixelSize:Kit.Runtime.px(7.5);font.weight:Font.Medium;font.letterSpacing:Kit.Runtime.px(1.05) }
                        property real labelWidth: {
                            let widest=0;
                            for(const agent of terminal.state.agent || [])for(const limit of agent.limits) { widest=Math.max(widest,agentLabelMetrics.advanceWidth(shortLabel(limit.title || limit.label))); }
                            return Math.min(Kit.Runtime.px(66),Math.ceil(widest)+1);
                        }
                        Repeater {
                            model: terminal.state.agent || []
                            Kit.Button {
                                required property var modelData
                                x: Kit.Runtime.px(14); width: contents.width - Kit.Runtime.px(28); height: Math.max(Kit.Runtime.px(40), meters.height + Kit.Runtime.px(8)); borderVisible: false
                                Accessible.name: modelData.name
                                onClicked: terminal.act("agent")
                                onRightClicked: terminal.act("panel", "agent")
                                Column {
                                    x: Kit.Runtime.px(4); y: Kit.Runtime.px(6); width: Kit.Runtime.px(86)
                                    Kit.Label { width: parent.width; text: modelData.name; color: parent.parent.foreground; font.family: Kit.Runtime.sans; font.pixelSize:Kit.Runtime.px(10) }
                                    Kit.Label { width: parent.width; text: modelData.plan; color: parent.parent.foreground; font.pixelSize: Kit.Runtime.px(8) }
                                }
                                Column {
                                    id: meters; x: Kit.Runtime.px(94); width: parent.width - x; y: Kit.Runtime.px(8); spacing: Kit.Runtime.px(4)
                                    Repeater {
                                        model: modelData.limits
                                        Row {
                                            required property var modelData
                                            width: meters.width; height: Kit.Runtime.px(12); spacing: Kit.Runtime.px(6)
                                            Kit.Micro {
                                                width:agentPart.labelWidth;height:parent.height;pixels:7.5
                                                text:agentPart.shortLabel(modelData.title || modelData.label);color:Kit.Runtime.c("mist-4")
                                                // Keep long micro labels inside the capped column without
                                                // reducing their type size. Still elide genuinely long names.
                                                font.letterSpacing:Math.max(Kit.Runtime.px(.5),Kit.Runtime.px(1.05)-Math.max(0,agentLabelMetrics.advanceWidth(text)+1-width)/Math.max(1,text.length))
                                            }
                                            Rectangle { anchors.verticalCenter: parent.verticalCenter; width: Math.max(0, meters.width - agentPart.labelWidth - Kit.Runtime.px(88)); height: Kit.Runtime.px(4); color: Kit.Runtime.c("ink-5"); Rectangle { width: parent.width * modelData.fraction; height: parent.height; color: Kit.Runtime.c("jade") } }
                                            Kit.Label { width: Kit.Runtime.px(30); height: parent.height; horizontalAlignment: Text.AlignRight; font.pixelSize: Kit.Runtime.px(10); text: Math.round(modelData.fraction * 100) + "%" }
                                            Kit.Label { width: Kit.Runtime.px(40); height: parent.height; horizontalAlignment: Text.AlignRight; font.pixelSize: Kit.Runtime.px(8); color: Kit.Runtime.c("mist-5"); text: { const now = terminal.state.clock ? terminal.state.clock.epoch_ms : Date.now(); const minutes = Math.max(0, Math.ceil((Date.parse(modelData.resets_at) - now) / 60000)); return minutes ? Math.floor(minutes / 60) + "h " + minutes % 60 + "m" : ""; } }
                                        }
                                    }
                                }
                            }
                        }
                        Kit.Button {
                            id:defaultAgent
                            x:Kit.Runtime.px(14);width:parent.width-Kit.Runtime.px(28);height:Kit.Runtime.px(26)
                            Accessible.name:Kit.Runtime.tr("open-agent")
                            onClicked:terminal.act("agent")
                            Kit.Icon { id:agentIcon;x:Kit.Runtime.px(8);anchors.verticalCenter:parent.verticalCenter;name:"smart_toy";color:defaultAgent.foreground }
                            Kit.Label { x:agentIcon.x+agentIcon.width+Kit.Runtime.px(6);height:parent.height;width:Math.max(0,agentTag.x-x-Kit.Runtime.px(8));text:Kit.Runtime.tr("open-agent");font.pixelSize:Kit.Runtime.px(10);color:defaultAgent.foreground }
                            Kit.Micro { id:agentTag;anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(8);anchors.verticalCenter:parent.verticalCenter;text:String(terminal.state.default_agent || "").toUpperCase();color:defaultAgent.foreground }
                        }
                    }
                    Part {
                        sectionKey: "telemetry"
                        Row {
                            x: Kit.Runtime.px(14); spacing: Kit.Runtime.px(10)
                            Repeater {
                                model: ["cpu", "memory", "temperature"]
                                Item {
                                    required property string modelData
                                    width: (contents.width - Kit.Runtime.px(48)) / 3;implicitHeight:telemetryContent.implicitHeight
                                    activeFocusOnTab:true;Accessible.role:Accessible.Button;Accessible.name:Kit.Runtime.tr(modelData)
                                    Keys.onReturnPressed:terminal.openPage("performance")
                                    Keys.onEnterPressed:terminal.openPage("performance")
                                    Column {
                                        id:telemetryContent;width:parent.width;spacing:Kit.Runtime.px(4)
                                    Kit.Micro { text: ({cpu:"CPU", memory:"MEM", temperature:"TEMP"})[modelData] + (Kit.Runtime.language === "en" ? "" : " " + Kit.Runtime.tr(modelData)) }
                                    Row {
                                        height: Kit.Runtime.px(16); spacing: Kit.Runtime.px(3)
                                        Kit.Label { height: parent.height; font.family: Kit.Runtime.display; font.pixelSize: Kit.Runtime.px(16); font.weight: Font.DemiBold; color: Kit.Runtime.c("paper-1"); text: { const t = terminal.state.telemetry; if (!t) return "—"; const value = modelData === "cpu" ? t.cpu_percent : modelData === "memory" ? t.memory_used / 1073741824 : t.temperature_c; return value === null ? "—" : value.toFixed(modelData === "memory" ? 1 : 0) + (modelData === "cpu" ? "%" : modelData === "memory" ? "" : "°"); } }
                                        Kit.Label { visible: modelData === "memory" && !!terminal.state.telemetry; anchors.bottom: parent.bottom; height: Kit.Runtime.px(9); font.pixelSize: Kit.Runtime.px(9); font.weight: Font.Medium; color: Kit.Runtime.c("mist-4"); text: terminal.state.telemetry ? "/ " + (terminal.state.telemetry.memory_total / 1073741824).toFixed(1) + "G" : "" }
                                    }
                                    Kit.Spark { width: Math.min(parent.width, Kit.Runtime.px(96)); height: Kit.Runtime.px(16); samples: terminal.state.telemetry ? terminal.state.telemetry.history[modelData] : []; ink: Kit.Runtime.c(modelData === "cpu" ? "accent-ink" : modelData === "memory" ? "paper-2" : "jade") }
                                    }
                                    Rectangle { anchors.fill:parent;color:"transparent";border.width:parent.activeFocus?1:0;border.color:Kit.Runtime.c("accent-ink") }
                                    MouseArea { anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:terminal.openPage("performance") }
                                }
                            }
                        }
                        BatteryCells { x:Kit.Runtime.px(14);width:parent.width-Kit.Runtime.px(28);rows:terminal.state.batteries || [];onOpen:terminal.openPage("power") }
                    }
                    Part {
                        id:commsPart;sectionKey:"comms"
                        CommsList {
                            id:overviewComms;x:Kit.Runtime.px(14);width:parent.width-Kit.Runtime.px(28)
                            rows:terminal.logRows
                            limit:Math.max(3,Math.floor((scroll.height-commsPart.y-Kit.Runtime.px(60))/Kit.Runtime.px(90)))
                            onMore:terminal.openPage("comms")
                            onAction:(key,index)=>terminal.act("comms-action",JSON.stringify({key:key,index:index}))
                        }
                    }
                }
            }
            Rectangle {
                anchors.left:scroll.left;anchors.right:scroll.right;anchors.bottom:scroll.bottom;height:Kit.Runtime.px(14)
                visible:scroll.contentHeight-scroll.contentY-scroll.height>.5
                readonly property color ground:Kit.Runtime.c("ink-2")
                gradient:Gradient { GradientStop { position:0;color:Qt.rgba(bodyFade.ground.r,bodyFade.ground.g,bodyFade.ground.b,0) } GradientStop { position:1;color:bodyFade.ground } }
                id:bodyFade
            }
            Kit.Label { id: errorLabel; anchors.bottom: foot.top; x:Kit.Runtime.px(14); width: parent.width-Kit.Runtime.px(28); height: text ? Kit.Runtime.px(30) : 0; text: terminal.pageName ? "" : terminal.actionError; color: Kit.Runtime.c("vermilion"); wrapMode: Text.Wrap; font.pixelSize: Kit.Runtime.px(10) }
            Row {
                id: foot; anchors.bottom: parent.bottom; anchors.bottomMargin: Kit.Runtime.px(12); x: Kit.Runtime.px(22); spacing: Kit.Runtime.px(6)
                Repeater {
                    model: [{key:"lock",icon:"lock",action:"lock"},{key:"sleep",icon:"bedtime",action:"sleep"},{key:"exit",icon:"logout",action:"power-menu"},{key:"reboot",icon:"restart_alt",action:"power-menu"},{key:"shutdown",icon:"power_settings_new",action:"power-menu"}]
                    Kit.Button {
                        required property var modelData
                        width: (body.width - Kit.Runtime.px(60)) / 5; height: Kit.Runtime.px(40)
                        danger: modelData.action === "power-menu"
                        Accessible.name: Kit.Runtime.tr(modelData.key)
                        onClicked: terminal.foot(modelData.action)
                        Kit.Icon { anchors.horizontalCenter: parent.horizontalCenter; y: Kit.Runtime.px(6); name: parent.modelData.icon; font.pixelSize: Kit.Runtime.px(15); color: parent.foreground }
                        Kit.Micro { anchors.horizontalCenter: parent.horizontalCenter; y: Kit.Runtime.px(25); text: parent.modelData.key === "shutdown" ? "OFF" : parent.modelData.key.toUpperCase(); pixels: 7.5; color: parent.foreground }
                    }
                }
            }
            DetailFrame {
                id:detail;y:header.height+(clockPart.visible?clockPart.height:0);width:parent.width;height:Math.max(0,parent.height-y)
                pageName:terminal.pageName;terminalOpen:terminal.opened
                snapshot:terminal.state[retainedPage] || ({})
                crumb:retainedPage==="comms"?Kit.Runtime.label("comms-page"):Kit.Runtime.label(terminal.pageSection)+" › "+Kit.Runtime.label(retainedPage)
                onCommand:(name,value)=>terminal.act(name,value || undefined)
                showing:terminal.opened && terminal.pageName!=="";rows:terminal.logRows;number:terminal.pageNumber;error:terminal.actionError
                onBack:terminal.backPage()
                onClear:terminal.act("comms-clear")
                onAction:(key,index)=>terminal.act("comms-action",JSON.stringify({key:key,index:index}))
            }
        }
    }
}
