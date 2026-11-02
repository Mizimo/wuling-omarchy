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
    property string hostname: ""
    property bool logExpanded: false
    property bool revealLog: false
    readonly property string screenName: QsWindow.window && QsWindow.window.screen ? QsWindow.window.screen.name : ""
    property var logRows: []
    FileView { path: "/etc/hostname"; printErrors: false; onLoaded: terminal.hostname = text().trim().toUpperCase() }
    readonly property var sections: Kit.Runtime.setting("terminal.sections")
    readonly property var shown: sections.filter(key => key !== "agent" || (state.agent || []).length > 0)
        .filter(key => key !== "signal" || !!state.signal)
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
        if (sections.indexOf("comms") < 0 || bar && bar.barHidden) return "off";
        logExpanded = true; revealLog = true; open(); scrollLog.restart(); return "ok";
    }
    IpcHandler {
        enabled: terminal.screenName !== ""
        target: "wuling.terminal." + terminal.screenName
        function geometry(): string { return JSON.stringify(terminal.geometry()); }
        function history(): string { return terminal.history(); }
    }
    Timer {
        id: scrollLog; interval: 30
        onTriggered: {
            if (!terminal.opened) return;
            if (terminal.has("comms")) { scroll.contentY = Math.max(0, Math.min(commsPart.y, contents.height - scroll.height)); terminal.revealLog = false; }
        }
    }
    function act(name, value) {
        const next = ["wuling", "action", name]; if (value !== undefined) next.push(String(value));
        // Slider drags retain the latest pending value, not a queue of stale
        // commands. Discrete clicks remain ordered and bounded.
        let queue = actionQueue.filter(row => !(["volume", "brightness"].indexOf(name) >= 0 && row[2] === name));
        actionQueue = queue.concat([next]).slice(-16); runNext();
    }
    function runNext() {
        if (actionProcess.running || !actionQueue.length) return;
        actionProcess.command = actionQueue[0]; actionQueue = actionQueue.slice(1); actionProcess.running = true;
    }
    function tileValue(tile) {
        const word = tile.active ? "On" : "Off";
        if (tile.id === "power") {
            const value = ({balanced:"Balanced", performance:"Performance", "power-saver":"Saver"})[tile.state] || tile.state;
            return Kit.Runtime.language === "en" ? value : Kit.Runtime.tr(tile.state) + " " + value;
        }
        if (Kit.Runtime.language === "en") return word;
        return ["dnd", "night"].indexOf(tile.id) >= 0 ? Kit.Runtime.tr(tile.id) + " " + word : word + " " + Kit.Runtime.tr(tile.active ? "on" : "off");
    }
    function foot(action) { close(); act(action); }
    onOpenedChanged: {
        if (!opened) { state = ({}); logExpanded = false; revealLog = false; }
        else actionError = "";
        reportGeometry();
    }
    onScreenNameChanged: reportGeometry()
    Component.onDestruction: if (screenName) Quickshell.execDetached(["omarchy-shell", "-q", "wuling.notifications", "terminal", screenName, '{"open":false,"width":0}'])
    onStateChanged: {
        const rows=state.comms && state.comms.available ? state.comms.items : [];
        // Unchanged status samples must not destroy a row underneath a press.
        if(JSON.stringify(rows)!==JSON.stringify(logRows))logRows=rows;
        if(revealLog)scrollLog.restart();
    }
    Process {
        id: collector
        command: ["wuling", "status", "--watch", "--sections"].concat(terminal.sections)
        running: terminal.opened && terminal.sections.length > 0
        stdout: SplitParser {
            onRead: line => { try { const data = JSON.parse(line); if (terminal.opened && data.schema_version === 1) terminal.state = data; } catch (_) {} }
        }
    }
    Process {
        id: actionProcess
        stdout: StdioCollector {
            onStreamFinished: {
                try { const response = JSON.parse(text); terminal.actionError = response.error ? response.error.message : ""; }
                catch (_) { terminal.actionError = Kit.Runtime.tr("unavailable"); }
            }
        }
        onExited: Qt.callLater(terminal.runNext)
    }
    Kit.Button {
        id: button; anchors.fill: parent; host: terminal.bar
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
                else for (let i = 0; i < item.children.length; i++) controls(item.children[i], result);
            }
            function move(direction) {
                let list = []; controls(contents, list); controls(foot, list);
                const index = list.findIndex(item => item.activeFocus);
                if (!list.length) return;
                const target = list[(index + direction + list.length) % list.length]; target.forceActiveFocus();
                const point = target.mapToItem(contents, 0, 0);
                if (point.y >= 0 && point.y < contents.height) scroll.contentY = Math.max(0, Math.min(contents.height - scroll.height, point.y - scroll.height / 2));
            }
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Escape) { terminal.close(); event.accepted = true; }
                else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) { terminal.switchPanel(event.key === Qt.Key_Backtab || event.modifiers & Qt.ShiftModifier ? -1 : 1); event.accepted = true; }
                else if ([Qt.Key_Down, Qt.Key_Up].indexOf(event.key) >= 0) { move(event.key === Qt.Key_Down ? 1 : -1); event.accepted = true; }
            }
            Rectangle {
                id: header; width: parent.width; height: Kit.Runtime.hud ? Kit.Runtime.px(26) : 0; visible: height > 0
                color: Kit.Runtime.c("fill")
                Kit.Label { id: headerTitle; x: Kit.Runtime.px(14); height: parent.height; text: "FIELD TERMINAL"; color: Kit.Runtime.c("on-accent"); font.pixelSize: Kit.Runtime.px(10); font.weight: Font.Bold; font.letterSpacing: Kit.Runtime.px(1.6) }
                Kit.Label { id: headerHost; anchors.right: parent.right; anchors.rightMargin: Kit.Runtime.px(14); width: Math.min(implicitWidth, Kit.Runtime.px(105)); height: parent.height; text: terminal.hostname; color: Kit.Runtime.c("on-accent"); font.pixelSize: Kit.Runtime.px(10); font.weight: Font.Bold }
                Kit.Hazard { anchors.left: headerTitle.right; anchors.right: headerHost.left; anchors.margins: Kit.Runtime.px(10); anchors.verticalCenter: parent.verticalCenter; height: Kit.Runtime.px(6); ink: Kit.Runtime.c("on-accent") }
            }
            Flickable {
                id: scroll; anchors.top: header.bottom; anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: errorLabel.top
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
                            Kit.Section { width: parent.width; number: terminal.number(part.sectionKey); title: Kit.Runtime.label(part.sectionKey); detail: part.sectionKey === "clock" ? Quickshell.env("USER") : part.sectionKey === "comms" ? terminal.logRows.length + (Kit.Runtime.language === "en" ? "" : " " + Kit.Runtime.tr("count-unit")) : "" }
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
                        sectionKey: "clock"
                        Item {
                            width: parent.width; height: Kit.Runtime.g("terminal_clock_size") * .9 + Kit.Runtime.px(2)
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
                                    width: (contents.width - Kit.Runtime.px(40)) / 3; height: Kit.Runtime.px(52)
                                    selected: modelData.active
                                    Accessible.name: Kit.Runtime.tr(modelData.id)
                                    onClicked: terminal.act(modelData.action)
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
                        Kit.Level { x: Kit.Runtime.px(14); width: parent.width - Kit.Runtime.px(28); visible: !!terminal.state.levels && !!terminal.state.levels.volume; name: Kit.Runtime.tr("volume"); icon: terminal.state.levels && terminal.state.levels.volume && terminal.state.levels.volume.muted ? "volume_off" : "volume_up"; value: terminal.state.levels && terminal.state.levels.volume ? terminal.state.levels.volume.percent : 0; onAdjusted: percent => terminal.act("volume", Math.round(percent)) }
                        Kit.Level { x: Kit.Runtime.px(14); width: parent.width - Kit.Runtime.px(28); visible: !!terminal.state.levels && terminal.state.levels.brightness !== null; name: Kit.Runtime.tr("brightness"); icon: "brightness_6"; fill: Kit.Runtime.c("paper-2"); value: terminal.state.levels && terminal.state.levels.brightness !== null ? terminal.state.levels.brightness : 0; onAdjusted: percent => terminal.act("brightness", Math.round(percent)) }
                    }
                    Part {
                        sectionKey: "signal"
                        Row {
                            x: Kit.Runtime.px(14); spacing: Kit.Runtime.px(10)
                            Kit.Icon { name: "music_note"; width: Kit.Runtime.px(38); height: Kit.Runtime.px(42); color: Kit.Runtime.c("accent-ink") }
                            Column {
                                width: contents.width - Kit.Runtime.px(80); spacing: Kit.Runtime.px(4)
                                Kit.Label { width: parent.width; text: terminal.state.signal ? terminal.state.signal.title || terminal.state.signal.identity : ""; font.family: Kit.Runtime.sans; font.weight: Font.DemiBold }
                                Kit.Label { width: parent.width; text: terminal.state.signal ? terminal.state.signal.artist : ""; color: Kit.Runtime.c("mist-4"); font.family: Kit.Runtime.sans; font.pixelSize: Kit.Runtime.px(10) }
                                Row {
                                    spacing: Kit.Runtime.px(6)
                                    Kit.Button { icon: "skip_previous"; Accessible.name: Kit.Runtime.tr("previous"); enabled: !!terminal.state.signal && terminal.state.signal.can_previous; onClicked: terminal.act("previous") }
                                    Kit.Button { icon: "pause"; Accessible.name: Kit.Runtime.tr("pause"); enabled: !!terminal.state.signal && terminal.state.signal.can_toggle; onClicked: terminal.act("play-pause") }
                                    Kit.Button { icon: "skip_next"; Accessible.name: Kit.Runtime.tr("next"); enabled: !!terminal.state.signal && terminal.state.signal.can_next; onClicked: terminal.act("next") }
                                }
                            }
                        }
                    }
                    Part {
                        sectionKey: "agent"
                        Repeater {
                            model: terminal.state.agent || []
                            Kit.Button {
                                required property var modelData
                                x: Kit.Runtime.px(14); width: contents.width - Kit.Runtime.px(28); height: Math.max(Kit.Runtime.px(40), meters.height + Kit.Runtime.px(8)); borderVisible: false
                                Accessible.name: modelData.name
                                onClicked: terminal.act("agent")
                                onRightClicked: terminal.act("panel", "agent")
                                Column {
                                    x: Kit.Runtime.px(4); y: Kit.Runtime.px(6); width: Kit.Runtime.px(74)
                                    Kit.Label { width: parent.width; text: modelData.name; color: parent.parent.foreground; font.family: Kit.Runtime.sans }
                                    Kit.Label { width: parent.width; text: modelData.plan; color: parent.parent.foreground; font.pixelSize: Kit.Runtime.px(8) }
                                }
                                Column {
                                    id: meters; x: Kit.Runtime.px(76); width: parent.width - x; y: Kit.Runtime.px(8); spacing: Kit.Runtime.px(4)
                                    Repeater {
                                        model: modelData.limits
                                        Row {
                                            required property var modelData
                                            width: meters.width; height: Kit.Runtime.px(12); spacing: Kit.Runtime.px(6)
                                            Kit.Label { width: Kit.Runtime.px(44); height: parent.height; font.pixelSize: Kit.Runtime.px(7.5); text: modelData.title || modelData.label; color: Kit.Runtime.c("mist-4") }
                                            Rectangle { anchors.verticalCenter: parent.verticalCenter; width: Math.max(0, meters.width - Kit.Runtime.px(132)); height: Kit.Runtime.px(4); color: Kit.Runtime.c("ink-5"); Rectangle { width: parent.width * modelData.fraction; height: parent.height; color: Kit.Runtime.c("jade") } }
                                            Kit.Label { width: Kit.Runtime.px(30); height: parent.height; horizontalAlignment: Text.AlignRight; font.pixelSize: Kit.Runtime.px(10); text: Math.round(modelData.fraction * 100) + "%" }
                                            Kit.Label { width: Kit.Runtime.px(40); height: parent.height; horizontalAlignment: Text.AlignRight; font.pixelSize: Kit.Runtime.px(8); color: Kit.Runtime.c("mist-5"); text: { const now = terminal.state.clock ? terminal.state.clock.epoch_ms : Date.now(); const minutes = Math.max(0, Math.ceil((Date.parse(modelData.resets_at) - now) / 60000)); return minutes ? Math.floor(minutes / 60) + "h " + minutes % 60 + "m" : ""; } }
                                        }
                                    }
                                }
                            }
                        }
                        Kit.Button { x: Kit.Runtime.px(14); width: parent.width - Kit.Runtime.px(28); height: Kit.Runtime.px(26); text: Kit.Runtime.tr("ask-agent"); icon: "smart_toy"; onClicked: terminal.act("agent") }
                    }
                    Part {
                        sectionKey: "telemetry"
                        Row {
                            x: Kit.Runtime.px(14); spacing: Kit.Runtime.px(10)
                            Repeater {
                                model: ["cpu", "memory", "temperature"]
                                Column {
                                    required property string modelData
                                    width: (contents.width - Kit.Runtime.px(48)) / 3; spacing: Kit.Runtime.px(4)
                                    Kit.Micro { text: ({cpu:"CPU", memory:"MEM", temperature:"TEMP"})[modelData] + (Kit.Runtime.language === "en" ? "" : " " + Kit.Runtime.tr(modelData)) }
                                    Row {
                                        height: Kit.Runtime.px(16); spacing: Kit.Runtime.px(3)
                                        Kit.Label { height: parent.height; font.family: Kit.Runtime.display; font.pixelSize: Kit.Runtime.px(16); font.weight: Font.DemiBold; color: Kit.Runtime.c("paper-1"); text: { const t = terminal.state.telemetry; if (!t) return "—"; const value = modelData === "cpu" ? t.cpu_percent : modelData === "memory" ? t.memory_used / 1073741824 : t.temperature_c; return value === null ? "—" : value.toFixed(modelData === "memory" ? 1 : 0) + (modelData === "cpu" ? "%" : modelData === "memory" ? "" : "°"); } }
                                        Kit.Label { visible: modelData === "memory" && !!terminal.state.telemetry; anchors.bottom: parent.bottom; height: Kit.Runtime.px(9); font.pixelSize: Kit.Runtime.px(9); font.weight: Font.Medium; color: Kit.Runtime.c("mist-4"); text: terminal.state.telemetry ? "/ " + (terminal.state.telemetry.memory_total / 1073741824).toFixed(1) + "G" : "" }
                                    }
                                    Kit.Spark { width: Math.min(parent.width, Kit.Runtime.px(96)); height: Kit.Runtime.px(16); samples: terminal.state.telemetry ? terminal.state.telemetry.history[modelData] : []; ink: Kit.Runtime.c(modelData === "cpu" ? "accent-ink" : modelData === "memory" ? "paper-2" : "jade") }
                                }
                            }
                        }
                    }
                    Part {
                        id: commsPart
                        sectionKey: "comms"
                        property int roomRows: Math.max(3, Math.floor((scroll.height - y - Kit.Runtime.px(60)) / Kit.Runtime.px(20)))
                        property int shownRows: terminal.logExpanded ? terminal.logRows.length : Math.min(terminal.logRows.length, roomRows)
                        Column {
                            x: Kit.Runtime.px(14); width: parent.width - Kit.Runtime.px(28); spacing: Kit.Runtime.px(5)
                            Repeater {
                                model: terminal.logRows.slice(0, commsPart.shownRows)
                                Kit.Button {
                                    required property var modelData
                                    width: parent.width; height: Kit.Runtime.px(15); borderVisible: false
                                    enabled: modelData.action
                                    Accessible.name: modelData.summary
                                    onClicked: Quickshell.execDetached(["omarchy-shell", "wuling.notifications", "historyAction", modelData.key])
                                    Kit.Micro { x: 0; width: Kit.Runtime.px(54); anchors.verticalCenter: parent.verticalCenter; text: parent.modelData.app.toUpperCase() }
                                    Kit.Label { x: Kit.Runtime.px(62); width: parent.width - Kit.Runtime.px(100); height: parent.height; text: parent.modelData.summary; font.family: Kit.Runtime.sans; color: parent.foreground }
                                    Kit.Label { anchors.right: parent.right; height: parent.height; text: Qt.formatDateTime(new Date(parent.modelData.time * 1000), "HH:mm"); font.pixelSize: Kit.Runtime.px(9); color: Kit.Runtime.c("mist-5") }
                                }
                            }
                            Kit.Button { visible: terminal.logRows.length > commsPart.shownRows; width: parent.width; height: Kit.Runtime.px(22); borderVisible: false; text: "+" + (terminal.logRows.length - commsPart.shownRows); Accessible.name: Kit.Runtime.tr("show-all"); onClicked: terminal.logExpanded = true }
                            Kit.Label { visible: !terminal.logRows.length; width: parent.width; height: Kit.Runtime.px(20); text: Kit.Runtime.tr("no-notifications"); color: Kit.Runtime.c("mist-4"); font.family: Kit.Runtime.sans }
                        }
                    }
                }
            }
            Kit.Label { id: errorLabel; anchors.bottom: foot.top; width: parent.width; height: text ? Kit.Runtime.px(30) : 0; text: terminal.actionError; color: Kit.Runtime.c("vermilion"); wrapMode: Text.Wrap; font.pixelSize: Kit.Runtime.px(10) }
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
        }
    }
}
