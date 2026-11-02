import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.Commons
import qs.Commons as Commons
import qs.Ui
import "kit" as Kit

// WULING owns layout and its drawn cells. Native widgets and their panels are
// instantiated from the installed registry, with the installed scoped facade.
Item {
    id: host
    property var shell: null
    property var manifest: null
    property var pluginRegistry: null
    property var barWidgetRegistry: null
    property var barConfig: ({})
    property string omarchyPath: ""
    property bool barHidden: false
    property bool hiddenProbePending: false
    readonly property string position: barConfig.position || "top"
    readonly property bool vertical: position === "left" || position === "right"
    readonly property int barSize: Math.round(Kit.Runtime.g("bar_height") + (vertical ? Kit.Runtime.px(2) : 0))
    readonly property string fontFamily: Kit.Runtime.mono
    readonly property color foreground: Commons.Color.bar.text
    readonly property color barForeground: foreground
    readonly property color background: Commons.Color.bar.background
    readonly property color urgent: Commons.Color.bar.active
    readonly property int iconSlot: Style.bar.iconSlot
    readonly property int iconCanvas: Style.bar.iconCanvas
    readonly property int iconFont: Style.bar.iconFont
    readonly property int statusSlot: Style.bar.statusSlot
    readonly property bool transparent: (barConfig.background || (barConfig.transparent === true ? "none" : "opaque")) === "none"
    readonly property bool foregroundAnimationEnabled: false
    readonly property var layoutConfig: JSON.parse(JSON.stringify(barConfig.layout || {}))
    property bool centerSectionRevealHeld: false
    property bool centerHoverRevealSuppressed: false
    readonly property bool traySectionDragActive: false
    readonly property bool traySectionPopoutOpen: slots.some(s => s.section === "tray" && s.widget === activePopout)
    property var activePopout: null
    property var clickTargets: []
    property var slots: []
    property var tooltipTarget: null
    property string tooltipText: ""
    property var lastCard: null
    property string lastCardSection: ""
    property int commands: 0
    property var hoveredWindows: []
    readonly property var foregroundWindow: ToplevelManager.activeToplevel
    property string hostname: ""
    FileView { path: "/etc/hostname"; printErrors: false; onLoaded: host.hostname = text().trim().toUpperCase() }

    // Visibility belongs to the replacement host. Native overlay facades read
    // it from us; the shell does not inject the native bar's toggle state.
    function syncHidden() {
        if (hiddenProbe.running) hiddenProbePending = true;
        else hiddenProbe.running = true;
    }
    Process {
        id: hiddenProbe
        running: true
        command: ["test", "-f", Quickshell.env("HOME") + "/.local/state/omarchy/toggles/bar-off"]
        onExited: (code, status) => {
            host.barHidden = code === 0;
            if (host.hiddenProbePending) { host.hiddenProbePending = false; Qt.callLater(host.syncHidden); }
        }
    }
    FileView { path: Quickshell.env("HOME") + "/.local/state/omarchy/toggles"; watchChanges: true; printErrors: false; onFileChanged: host.syncHidden() }
    IpcHandler {
        target: "omarchy.bar"
        function syncHidden(): void { host.syncHidden(); }
    }

    onBarHiddenChanged: {
        if (!barHidden) return;
        if (activePopout && activePopout.close) activePopout.close();
        activePopout = null; tooltipTarget = null; hoveredWindows = []; centerSectionRevealHeld = false;
    }
    function hover(window, entered) {
        hoveredWindows = hoveredWindows.filter(item => item !== window);
        if (entered) hoveredWindows = hoveredWindows.concat([window]);
        if (hoveredWindows.length > 0) { hoverRelease.stop(); centerSectionRevealHeld = true; }
        else hoverRelease.restart();
    }
    Timer { id: hoverRelease; interval: 200; onTriggered: if (!host.hoveredWindows.length) host.centerSectionRevealHeld = false }

    function entries(section) {
        // Placement order is stable even when a hand-edited layout repeats an
        // id. Native allowMultiple widgets may have distinct entries; others
        // retain their first placement and cannot create duplicate IPC owners.
        let seen = new Set(), result = [];
        for (const key of ["left", "centerBegin", "center", "centerEnd", "right", "tray"]) {
            for (const entry of layoutConfig[key] || []) {
                const id = entryId(entry), reg = barWidgetRegistry.widgets[id];
                const multiple = reg && reg.metadata && reg.metadata.allowMultiple === true;
                if (!id || seen.has(id) && !multiple) continue;
                seen.add(id);
                if (key === section) {
                    result.push(entry);
                    if (id === "omarchy.menu") result.push("wuling.identity");
                    if (id === "omarchy.workspaces") result.push("wuling.window");
                }
            }
        }
        if (section === "right") result.push("wuling.power-cell");
        return result;
    }
    function entryId(entry) { return typeof entry === "string" ? entry : String(entry.id || ""); }
    function registerClickTarget(target) {
        if (clickTargets.indexOf(target) < 0) clickTargets = clickTargets.concat([target]);
    }
    function unregisterClickTarget(target) { clickTargets = clickTargets.filter(t => t !== target); }
    function targetBelongsToWindow(target, window) {
        if (!target || !target.visible || !window || target.QsWindow.window !== window) return false;
        let ancestor = target.parent;
        while (ancestor) {
            if (!ancestor.visible) return false;
            if (ancestor.clip) {
                const clipped = target.mapToItem(ancestor, 0, 0);
                if (clipped.x < 0 || clipped.y < 0 || clipped.x + target.width > ancestor.width + .5 || clipped.y + target.height > ancestor.height + .5) return false;
            }
            ancestor = ancestor.parent;
        }
        const point = target.mapToItem(window.contentItem, 0, 0);
        return point.x + target.width > 0 && point.y + target.height > 0 && point.x < window.width && point.y < window.height;
    }
    function moduleWidgets(id) { return slots.filter(s => s.widgetId === id && s.widget).map(s => s.widget); }
    function setCenterHoverRevealSuppressed(value) { centerHoverRevealSuppressed = value; }
    function showTooltip(target, text) { tooltipTarget = target; tooltipText = text || ""; tipDelay.restart(); }
    function hideTooltip(target) {
        if (tooltipTarget === target) { tipDelay.stop(); tooltipTarget = null; tooltipText = ""; }
    }
    function run(command) { commands++; Quickshell.execDetached(["bash", "-lc", command]); }
    function requestPopout(owner) {
        const previous = activePopout;
        activePopout = owner;
        tooltipTarget = null;
        if (previous && previous !== owner) {
            if (previous.closeForPopoutSwitch) previous.closeForPopoutSwitch();
            else if (previous.close) previous.close();
        }
    }
    function releasePopout(owner) { if (activePopout === owner) activePopout = null; }
    function sectionFor(owner) {
        const slot = slots.find(s => s.widget === owner);
        if (!slot) return "";
        return slot.section.indexOf("center") === 0 ? "center" : slot.section;
    }
    function notePopoutCard(card) { lastCard = JSON.parse(JSON.stringify(card)); lastCardSection = sectionFor(activePopout); }
    function popoutCardFor(owner) { return lastCardSection === sectionFor(owner) ? lastCard : null; }
    function panelSlots(section, window) {
        return slots.filter(s => (!section || s.section === section ||
            (section === "center" && s.section.indexOf("center") === 0)) &&
            (!window || s.window === window) && s.widget && s.widget.visible &&
            s.width > 0 && s.height > 0 && typeof s.widget.open === "function" &&
            typeof s.widget.close === "function" && s.widget.opened !== undefined)
            .sort((a,b) => vertical ? a.mapToItem(null,0,0).y-b.mapToItem(null,0,0).y :
                a.mapToItem(null,0,0).x-b.mapToItem(null,0,0).x);
    }
    function choose(id) {
        const candidates = slots.filter(s => s.widgetId === id && s.widget && s.widget.visible && s.width > 0 && s.height > 0 && typeof s.widget.open === "function" && typeof s.widget.close === "function");
        const screen = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "";
        return candidates.find(s => s.window.screen.name === screen) || candidates[0] || null;
    }
    function summonBarWidget(id) { const s = choose(id); if (!s || barHidden) return false; s.reveal(); s.widget.open(); return true; }
    function hideBarWidget(id) { const found = moduleWidgets(id).filter(widget => typeof widget.close === "function"); found.forEach(widget => widget.close()); return found.length > 0; }
    function isBarWidgetOpen(id) { return moduleWidgets(id).some(widget => widget.opened === true); }
    function panelWidgetIdAt(section, index) {
        const screen = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "";
        const window = slots.map(s => s.window).find(w => w.screen.name === screen);
        const list = panelSlots(section, window || (slots[0] && slots[0].window));
        return list[Number(index)-1] ? list[Number(index)-1].widgetId : "";
    }
    function switchPanelFrom(owner, direction) {
        const s = slots.find(s => s.widget === owner);
        if (!s) return false;
        const list = panelSlots(sectionFor(owner), s.window), index = list.indexOf(s);
        if (index < 0 || list.length < 2) return false;
        const next = list[(index + (direction < 0 ? list.length-1 : 1)) % list.length]; next.reveal(); next.widget.open();
        return true;
    }
    Timer { id: tipDelay; interval: 400 }
    IpcHandler {
        target: "wuling.bar"
        function inspect(): string {
            return JSON.stringify({schema_version: 1, position: host.position, hidden: host.barHidden, transparent: host.transparent,
                appearance: {preset: Kit.Runtime.hud ? "hud" : "field", language: Kit.Runtime.language, labels: Kit.Runtime.setting("labels"), reduced: Kit.Runtime.reduced},
                fontFamily: host.fontFamily, barSize: host.barSize, commands: host.commands,
                layout: host.layoutConfig, catalog: host.barWidgetRegistry.availableIds(),
                targets: host.clickTargets.filter(t => t && t.visible && t.QsWindow.window).map(t => {
                    const w=t.QsWindow.window, p=t.mapToItem(w.contentItem,0,0);
                    return {text:String(t.text||""),tooltip:String(t.tooltipText||""),screen:w.screen.name,x:p.x,y:p.y,width:t.width,height:t.height};
                }),
                tooltip: host.tooltipText, tooltipReady: !!host.tooltipTarget && !tipDelay.running,
                active: host.slots.filter(s => s.widget && s.widget.opened).map(s => s.widgetId),
                slots: host.slots.map(s => {
                    const p = s.mapToItem(s.window.contentItem,0,0);
                    return {id:s.widgetId,section:s.section,screen:s.window.screen.name,
                        x:p.x,y:p.y,width:s.width,height:s.height,loaded:!!s.widget,
                        visible:!!s.widget && s.widget.visible,opened:!!s.widget && !!s.widget.opened,skinned:s.skinned,nativeOpacity:s.widget?s.widget.opacity:null,inputOpacity:s.skinned?0:1,label:s.labelText,format:s.widget && "format" in s.widget?s.widget.format:null};
                })});
        }
    }
    component ScopedBar: PluginBarApi {
        required property var ownerSlot
        pluginId: ownerSlot.widgetId
        moduleName: ownerSlot.widgetId
        shell: null
        foreground: host.foreground
        barForeground: host.barForeground
        background: host.background
        urgent: host.urgent
        fontFamily: host.fontFamily
        position: host.position
        vertical: host.vertical
        barSize: host.barSize
        transparent: host.transparent
        foregroundAnimationEnabled: false
        centerSectionRevealHeld: host.centerSectionRevealHeld
        _centerHoverRevealSuppressed: host.centerHoverRevealSuppressed
        activePopout: host.activePopout === ownerSlot.widget ? ownerSlot.widget : (host.activePopout ? foreignPopoutMarker : null)
        clickTargets: ownerSlot.ownedTargets
        layoutConfig: host.layoutConfig
        _showTooltip: (target,text) => host.showTooltip(target,text)
        _hideTooltip: target => host.hideTooltip(target)
        _registerClickTarget: target => { ownerSlot.ownedTargets = ownerSlot.ownedTargets.concat([target]); host.registerClickTarget(target); }
        _unregisterClickTarget: target => { ownerSlot.ownedTargets = ownerSlot.ownedTargets.filter(t => t !== target); host.unregisterClickTarget(target); }
        _requestPopout: owner => host.requestPopout(owner)
        _releasePopout: owner => host.releasePopout(owner)
        _switchPanelFrom: (owner,direction) => host.switchPanelFrom(owner,direction)
        _targetBelongsToWindow: (target,window) => host.targetBelongsToWindow(target,window)
        _moduleWidgets: id => id === ownerSlot.widgetId ? host.moduleWidgets(id) : []
        _run: command => host.run(command)
        _setCenterHoverRevealSuppressed: value => host.setCenterHoverRevealSuppressed(value)
    }
    component Slot: Item {
        id: slot
        required property var entry
        required property string section
        required property var window
        readonly property string widgetId: host.entryId(entry)
        readonly property var registration: host.barWidgetRegistry.widgets[widgetId]
        readonly property var widget: load.item
        readonly property bool skinned: !host.vertical && widgetId === "omarchy.clock" && !!widget && "displayText" in widget && "displayDate" in widget && "configuredFormat" in widget
        readonly property bool showDate: skinned && window.screen.width >= Kit.Runtime.px(1024) && !/[dMy]/.test(widget.configuredFormat)
        readonly property bool internal: ["wuling.identity", "wuling.window", "wuling.power-cell"].indexOf(widgetId) >= 0
        readonly property string labelText: customLabel.text
        property var ownedTargets: []
        readonly property var scoped: ScopedBar { ownerSlot: slot }
        implicitWidth: widget && widget.visible ? (host.vertical ? host.barSize : skinned ? clockFace.width + Kit.Runtime.px(20) : widget.implicitWidth) : 0
        implicitHeight: widget && widget.visible ? (host.vertical ? widget.implicitHeight : host.barSize) : 0
        width: implicitWidth
        height: implicitHeight
        Component.onCompleted: host.slots = host.slots.concat([slot])
        Component.onDestruction: {
            host.slots = host.slots.filter(s => s !== slot);
            if (widget === host.activePopout) { if (widget && widget.close) widget.close(); host.activePopout = null; }
            for (const target of ownedTargets) host.unregisterClickTarget(target);
        }
        function reveal() {
            let parentItem = parent;
            while (parentItem && !("contentX" in parentItem && "contentY" in parentItem)) parentItem = parentItem.parent;
            if (!parentItem) return;
            const point = slot.mapToItem(parentItem.contentItem, 0, 0);
            if (host.vertical) parentItem.contentY = Math.max(0, Math.min(parentItem.contentHeight - parentItem.height, point.y));
            else parentItem.contentX = Math.max(0, Math.min(parentItem.contentWidth - parentItem.width, point.x));
        }
        function bindWidget() {
            if (!widget) return;
            const firstParty = internal || !!(registration && registration.metadata && registration.metadata.firstParty);
            if ("_notePopoutCard" in scoped) {
                scoped._notePopoutCard = card => host.notePopoutCard(card);
                scoped._popoutCardFor = owner => host.popoutCardFor(owner);
                scoped.traySectionDragActive = Qt.binding(() => host.traySectionDragActive);
                scoped.traySectionPopoutOpen = Qt.binding(() => host.traySectionPopoutOpen);
            }
            if (!firstParty && host.shell) scoped.shell = host.shell.pluginShellForBarEntry("wuling.bar", widgetId);
            if ("bar" in widget) widget.bar = firstParty ? host : scoped;
            if ("moduleName" in widget) widget.moduleName = widgetId;
            if ("settings" in widget) {
                const values = typeof entry === "string" ? {} : JSON.parse(JSON.stringify(entry));
                if (widgetId === "omarchy.clock" && !values.format) values.format = "HH:mm";
                widget.settings = values;
            }
        }
        onEntryChanged: bindWidget()
        Rectangle {
            visible: slot.skinned
            anchors.fill: parent
            color: clockHover.hovered || slot.widget && slot.widget.opened ? Kit.Runtime.c("paper-0") : "transparent"
            Rectangle { visible: !!slot.widget && slot.widget.opened === true; anchors.bottom: parent.bottom; width: parent.width; height: Kit.Runtime.px(2); color: Kit.Runtime.c("fill") }
        }
        HoverHandler { id: clockHover }
        Row {
            id: clockFace; visible: slot.skinned; anchors.centerIn: parent; spacing: Kit.Runtime.px(8)
            Kit.Label {
                id: customLabel; text: slot.skinned ? slot.widget.displayText : ""; height: host.barSize
                font.family: Kit.Runtime.display; font.pixelSize: Kit.Runtime.g("clock_size"); font.weight: Font.DemiBold
                color: clockHover.hovered || slot.widget && slot.widget.opened ? Kit.Runtime.c("ink-2") : Kit.Runtime.c("paper-1")
            }
            Column {
                visible: slot.showDate; anchors.verticalCenter: parent.verticalCenter
                Kit.Label { text: slot.showDate ? Qt.formatDateTime(slot.widget.displayDate, "ddd") : ""; font.pixelSize: Kit.Runtime.px(8); color: customLabel.color }
                Kit.Label { text: slot.showDate ? Qt.formatDateTime(slot.widget.displayDate, "MM.dd") : ""; font.pixelSize: Kit.Runtime.px(10); color: customLabel.color }
            }
        }
        Loader {
            id: load
            opacity: slot.skinned ? 0 : 1
            anchors.fill: parent
            sourceComponent: slot.widgetId === "omarchy.menu" ? menuCell : slot.widgetId === "omarchy.workspaces" ? workspaceCell :
                slot.widgetId === "wuling.identity" ? identityCell : slot.widgetId === "wuling.window" ? windowCell : slot.widgetId === "wuling.power-cell" ? powerCell :
                slot.registration ? slot.registration.component : null
            onLoaded: slot.bindWidget()
        }
        Loader {
            readonly property var drawer: slot.section !== "tray" && slot.widget && "sectionHost" in slot.widget ? slot.widget.sectionHost : null
            parent: drawer || slot
            active: !!drawer
            sourceComponent: trayContents
            onLoaded: item.window = slot.window
        }
    }
    Component { id: menuCell; MenuCell {} }
    Component { id: workspaceCell; Workspaces {} }
    Component { id: identityCell; Identity {} }
    Component { id: windowCell; WindowLabel {} }
    Component { id: powerCell; PowerCell {} }
    component Strip: Item {
        id: strip
        property int structureRevision: 0
        required property string section
        property var window
        readonly property var entries: host.entries(section)
        readonly property real extent: {
            structureRevision;
            let total = 0;
            for (let i=0;i<items.count;i++) { const s=items.itemAt(i); if(s) total += host.vertical ? s.height : s.width; }
            return total;
        }
        readonly property real anchorOffset: {
            structureRevision;
            let before = 0;
            for (let i=0;i<items.count;i++) {
                const s=items.itemAt(i); if(!s) continue;
                const size=host.vertical ? s.height : s.width;
                if(s.widgetId === (host.barConfig.centerAnchor || "omarchy.clock")) return before+size/2;
                before += size;
            }
            return extent/2;
        }
        implicitWidth: host.vertical ? host.barSize : extent
        implicitHeight: host.vertical ? extent : host.barSize
        width: implicitWidth
        height: implicitHeight
        Repeater {
            id: items
            onItemAdded: strip.structureRevision++
            onItemRemoved: strip.structureRevision++
            model: strip.entries
            Slot {
                required property var modelData
                required property int index
                entry: modelData
                section: strip.section
                window: strip.window
                readonly property real offset: {
                    strip.structureRevision;
                    let sum=0;
                    for(let j=0;j<index;j++) { const s=items.itemAt(j); if(s) sum+=host.vertical?s.height:s.width; }
                    return sum;
                }
                x: host.vertical ? 0 : offset
                y: host.vertical ? offset : 0
            }
        }
    }
    Component { id: trayContents; Strip { section: "tray" } }
    component SectionViewport: Flickable {
        id: viewport
        property int structureRevision: 0
        required property var sections
        required property var window
        property real available: 0
        readonly property real extent: {
            structureRevision;
            let sum = 0;
            for (let i = 0; i < groups.count; i++) { const strip = groups.itemAt(i); if (strip) sum += strip.extent; }
            return sum;
        }
        readonly property real anchorOffset: {
            structureRevision;
            let sum = 0;
            for (let i = 0; i < groups.count; i++) {
                const strip = groups.itemAt(i); if (!strip) continue;
                if (strip.section === "center") return sum + strip.anchorOffset;
                sum += strip.extent;
            }
            return extent / 2;
        }
        readonly property real length: Math.min(extent, Math.max(0, available))
        width: host.vertical ? host.barSize : length
        height: host.vertical ? length : host.barSize
        contentWidth: host.vertical ? host.barSize : extent
        contentHeight: host.vertical ? extent : host.barSize
        clip: true
        interactive: extent > available
        boundsBehavior: Flickable.StopAtBounds
        flickableDirection: host.vertical ? Flickable.VerticalFlick : Flickable.HorizontalFlick
        Repeater {
            id: groups; model: viewport.sections
            onItemAdded: viewport.structureRevision++
            onItemRemoved: viewport.structureRevision++
            Strip {
                required property string modelData
                required property int index
                section: modelData; window: viewport.window
                readonly property real preceding: {
                    viewport.structureRevision;
                    let sum = 0;
                    for (let i = 0; i < index; i++) { const before = groups.itemAt(i); if (before) sum += before.extent; }
                    return sum;
                }
                x: host.vertical ? 0 : preceding
                y: host.vertical ? preceding : 0
            }
        }
        WheelHandler {
            enabled: viewport.extent > viewport.available
            onWheel: event => {
                const step = -(event.angleDelta.y || event.angleDelta.x) / 120 * Kit.Runtime.px(30);
                if (host.vertical) viewport.contentY = Math.max(0, Math.min(viewport.contentHeight - viewport.height, viewport.contentY + step));
                else viewport.contentX = Math.max(0, Math.min(viewport.contentWidth - viewport.width, viewport.contentX + step));
                event.accepted = true;
            }
        }
        Kit.Label {
            visible: viewport.extent > viewport.available
            parent: viewport; anchors.right: parent.right; anchors.bottom: parent.bottom
            text: host.vertical ? "⌄" : "›"; color: Kit.Runtime.c("accent-ink"); font.pixelSize: Kit.Runtime.px(10)
        }
    }
    Variants {
        model: Quickshell.screens
        PanelWindow {
            id: surface
            required property var modelData
            screen: modelData
            visible: !host.barHidden
            anchors.top: host.position !== "bottom"
            anchors.bottom: host.position !== "top"
            anchors.left: host.position !== "right"
            anchors.right: host.position !== "left"
            implicitWidth: host.barSize
            implicitHeight: host.barSize
            exclusiveZone: host.barHidden ? 0 : host.barSize
            color: host.transparent ? "transparent" : host.background
            WlrLayershell.namespace: "wuling-bar"
            WlrLayershell.layer: WlrLayer.Top
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            readonly property real axisLength: host.vertical ? height : width
            readonly property real centerStart: Math.max(0, Math.min(axisLength - center.length, axisLength / 2 - Math.min(center.anchorOffset, center.length)))
            MouseArea {
                anchors.fill: parent; z: -1
                onDoubleClicked: Quickshell.execDetached(["omarchy", "bar", "transparent", host.transparent ? "false" : "true"])
            }
            SectionViewport { sections: ["left"]; window: surface; available: Math.max(0, surface.centerStart - Kit.Runtime.px(4)) }
            SectionViewport {
                id: center; sections: ["centerBegin", "center", "centerEnd"]; window: surface; available: surface.axisLength * .4
                x: host.vertical ? 0 : surface.centerStart
                y: host.vertical ? surface.centerStart : 0
            }
            SectionViewport {
                sections: ["right"]; window: surface; available: Math.max(0, surface.axisLength - surface.centerStart - center.length - Kit.Runtime.px(4))
                x: host.vertical ? 0 : surface.width - width
                y: host.vertical ? surface.height - height : 0
            }
            Rectangle {
                visible: Kit.Runtime.hud
                width: host.vertical ? Kit.Runtime.px(2) : parent.width
                height: host.vertical ? parent.height : Kit.Runtime.px(2)
                x: host.position === "right" ? 0 : host.vertical ? parent.width - width : 0
                y: host.position === "bottom" ? 0 : host.vertical ? 0 : parent.height - height
                color: Kit.Runtime.c("line")
            }
            HoverHandler { onHoveredChanged: host.hover(surface, hovered) }
            Component.onDestruction: host.hover(surface, false)
            PopupWindow {
                id: tip
                visible: !!host.tooltipTarget && !tipDelay.running && host.tooltipText !== "" && host.targetBelongsToWindow(host.tooltipTarget,surface)
                color: "transparent"
                implicitWidth: tipText.implicitWidth+16
                implicitHeight: tipText.implicitHeight+12
                anchor.window: surface
                anchor.edges: Edges.Top | Edges.Left
                anchor.gravity: Edges.Bottom | Edges.Right
                anchor.adjustment: PopupAdjustment.Slide
                anchor.rect.x: {
                    const t=host.tooltipTarget;
                    if(!t || !host.targetBelongsToWindow(t,surface)) return 0;
                    return t.mapToItem(surface.contentItem,0,0).x + (host.position==="left"?t.width+4:host.position==="right"?-tip.width-4:t.width/2-tip.width/2);
                }
                anchor.rect.y: {
                    const t=host.tooltipTarget;
                    if(!t || !host.targetBelongsToWindow(t,surface)) return 0;
                    return t.mapToItem(surface.contentItem,0,0).y + (host.position==="top"?t.height+4:host.position==="bottom"?-tip.height-4:t.height/2-tip.height/2);
                }
                Rectangle { anchors.fill:parent; color:Commons.Color.tooltip.background; border.color:Commons.Color.tooltip.border
                    Text { id:tipText; anchors.centerIn:parent; text:host.tooltipText; textFormat:Text.PlainText; color:Commons.Color.tooltip.text; font.family:host.fontFamily; font.pixelSize:12 }
                }
            }
        }
    }
}
