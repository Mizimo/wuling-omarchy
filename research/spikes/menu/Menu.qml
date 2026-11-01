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
    function open(payloadJson) {
        calls++;
        lastPayload = payloadJson;
        opened = true;
        if (!modelApi) {
            var url = "file://" + omarchyPath + "/shell/plugins/menu/MenuModel.js";
            modelApi = Qt.createQmlObject('import QtQuick; import ' + JSON.stringify(url)
                + ' as Upstream; QtObject { function parse(raw) { return Upstream.parseMenuJsonc(raw); }'
                + ' function merge(a,b) { return Upstream.mergeMenuSources(a,b); }'
                + ' function route(model, input) { return Upstream.resolveRoute(model.items, model.itemOrder, input); } }', probe);
        }
    }
    function close() { opened = false; }
    function ping() { return "research.menu"; }
    function refresh() {}
    FileView { id: defaults; path: probe.omarchyPath + "/default/omarchy/omarchy-menu.jsonc"; blockLoading: true; watchChanges: true; onFileChanged: reload() }
    FileView { id: extensions; path: Quickshell.env("HOME") + "/.config/omarchy/extensions/omarchy-menu.jsonc"; blockLoading: true; printErrors: false; watchChanges: true; onFileChanged: reload() }
    IpcHandler {
        target: "research.menu"
        function inspect(): string {
            var a = probe.modelApi ? probe.modelApi.parse(defaults.text()) : [];
            var b = probe.modelApi ? probe.modelApi.parse(extensions.text()) : [];
            var model = probe.modelApi ? probe.modelApi.merge(a, b) : null;
            var input = probe.lastPayload ? JSON.parse(probe.lastPayload).menu : "";
            return JSON.stringify({calls: probe.calls, opened: probe.opened, payload: probe.lastPayload,
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
            Keys.onEscapePressed: event => {
                if (probe.shell) probe.shell.hide("research.menu");
                else {
                    // Record the facade failure separately; continue testing
                    // route delivery using the ordinary public CLI.
                    probe.ipcCloses++;
                    Quickshell.execDetached(["omarchy-shell", "shell", "hide", "research.menu"]);
                }
                event.accepted = true;
            }
            Text { anchors.centerIn: parent; text: "ROUTE PROBE " + probe.lastPayload; textFormat: Text.PlainText; color: "white"; font.pixelSize: 22 }
        }
    }
}
