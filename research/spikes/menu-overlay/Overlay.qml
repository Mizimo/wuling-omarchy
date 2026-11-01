import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

// Independently written probe. clonedFrom tests the host's replacement
// metadata; no upstream plugin is copied or cloned by this experiment.
Item {
    id: probe
    property var shell: null
    property var manifest: null
    property int shellChanges: 0
    onShellChanged: shellChanges++
    property string omarchyPath: Quickshell.env("OMARCHY_PATH")
    property bool opened: false
    property int calls: 0
    property int ipcCloses: 0
    property string lastPayload: ""
    property var modelApi: null
    property string lastLaunched: ""
    property string query: ""
    readonly property var apps: {
        const result=[];
        for (const entry of DesktopEntries.applications.values) {
            if (!entry.noDisplay && (!query || entry.name.toLowerCase().indexOf(query.toLowerCase()) >= 0)) result.push(entry);
        }
        return result.sort((a,b) => a.name.localeCompare(b.name));
    }
    function closeSelf() { if (shell) shell.hide("research.menu-overlay"); }
    function launchFirst() {
        if (!apps.length) return;
        lastLaunched=apps[0].id;
        apps[0].execute();
        closeSelf();
    }
    function open(payloadJson) {
        calls++;
        lastPayload = payloadJson;
        opened = true;
        query = "";
        if (!modelApi) {
            var url = "file://" + omarchyPath + "/shell/plugins/menu/MenuModel.js";
            modelApi = Qt.createQmlObject('import QtQuick; import ' + JSON.stringify(url)
                + ' as Upstream; QtObject { function parse(raw) { return Upstream.parseMenuJsonc(raw); }'
                + ' function merge(a,b) { return Upstream.mergeMenuSources(a,b); }'
                + ' function route(model, input) { return Upstream.resolveRoute(model.items, model.itemOrder, input); } }', probe);
        }
    }
    function close() { opened = false; }
    function ping() { return "research.menu-overlay"; }
    function refresh() {}
    FileView { id: defaults; path: probe.omarchyPath + "/default/omarchy/omarchy-menu.jsonc"; blockLoading: true; watchChanges: true; onFileChanged: reload() }
    FileView { id: extensions; path: Quickshell.env("HOME") + "/.config/omarchy/extensions/omarchy-menu.jsonc"; blockLoading: true; printErrors: false; watchChanges: true; onFileChanged: reload() }
    IpcHandler {
        target: "research.menu-overlay"
        function inspect(): string {
            var a = probe.modelApi ? probe.modelApi.parse(defaults.text()) : [];
            var b = probe.modelApi ? probe.modelApi.parse(extensions.text()) : [];
            var model = probe.modelApi ? probe.modelApi.merge(a, b) : null;
            var input = probe.lastPayload ? JSON.parse(probe.lastPayload).menu : "";
            return JSON.stringify({calls: probe.calls, opened: probe.opened, payload: probe.lastPayload,
                appCount: probe.apps.length, appNames: probe.apps.map(a=>({id:a.id,name:a.name})), lastLaunched:probe.lastLaunched,
                runtimeModel: !!probe.modelApi, defaultCount: a.length, extensionCount: b.length,
                resolvedRoute: model ? probe.modelApi.route(model, input) : "",
                appLibrary: !!(probe.shell && probe.shell.appLibrary),
                hasShell: !!probe.shell, shellChanges: probe.shellChanges,
                ipcCloses: probe.ipcCloses,
                manifestId: probe.manifest ? probe.manifest.id : "", sourceRoot: probe.omarchyPath});
        }
    }
    PanelWindow {
        visible: probe.opened
        anchors { top: true; bottom: true; left: true; right: true }
        WlrLayershell.namespace: "research-menu"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        exclusionMode: ExclusionMode.Ignore
        color: "#b0243447"
        Item {
            anchors.fill: parent
            focus: true
            Keys.onEscapePressed: event => { probe.closeSelf(); event.accepted = true; }
            Column {
                anchors.centerIn: parent
                spacing: 12
                Text { text: "OVERLAY ROUTE PROBE " + probe.lastPayload; textFormat: Text.PlainText; color: "white"; font.pixelSize: 20 }
                TextInput {
                    id: queryField
                    width: 500; height: 32
                    color: "white"; font.pixelSize: 18; focus: probe.opened
                    text: probe.query
                    onTextEdited: probe.query = text
                    onAccepted: probe.launchFirst()
                }
                Repeater {
                    model: probe.apps.slice(0,8)
                    Text { required property var modelData; text: modelData.name; textFormat: Text.PlainText; color: "white"; font.pixelSize: 16 }
                }
            }
        }
    }
}
