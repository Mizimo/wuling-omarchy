import QtQuick
import QtQml.Models
import Quickshell.Io

// No windows, files, dynamic objects, or upstream imports.
Item {
    id: probe
    property var shell: null
    property var assignments: []
    property var sequenceCheck: ({})
    Instantiator {
        model: [{manifest: {kinds: ["menu"]}}]
        delegate: QtObject {
            required property var modelData
            readonly property var manifest: modelData.manifest
            Component.onCompleted: probe.sequenceCheck = {
                directArray: Array.isArray(["menu"]),
                modelArray: Array.isArray(modelData.manifest.kinds),
                propertyArray: Array.isArray(manifest.kinds),
                index: manifest.kinds.indexOf("menu")
            }
        }
    }
    onShellChanged: assignments = assignments.concat([shell ? {
        pluginId: shell.pluginId, appLibrary: !!shell.appLibrary
    } : null])
    function open(payloadJson) {}
    function close() {}
    IpcHandler {
        target: "research.facade"
        function inspect(): string {
            return JSON.stringify({hasShell: !!probe.shell,
                appLibrary: !!(probe.shell && probe.shell.appLibrary),
                assignments: probe.assignments, sequenceCheck: probe.sequenceCheck});
        }
    }
}
