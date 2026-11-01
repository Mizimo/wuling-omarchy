import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// Independent contract experiment. Widgets and panels come from the installed
// registry. No upstream Bar.qml, drag implementation, or widget is copied.
Item {
    id: host
    property var shell: null
    property var manifest: null
    property var pluginRegistry: null
    property var barWidgetRegistry: null
    property var barConfig: ({})
    property string omarchyPath: ""
    property bool barHidden: false
    readonly property string position: barConfig.position || "top"
    readonly property bool vertical: position === "left" || position === "right"
    readonly property int barSize: vertical ? Style.bar.sizeVertical : Style.bar.sizeHorizontal
    readonly property string fontFamily: barConfig.fontFamily || Style.font.family
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

    function entries(section) { return layoutConfig[section] || []; }
    function entryId(entry) { return typeof entry === "string" ? entry : String(entry.id || ""); }
    function registerClickTarget(target) {
        if (clickTargets.indexOf(target) < 0) clickTargets = clickTargets.concat([target]);
    }
    function unregisterClickTarget(target) { clickTargets = clickTargets.filter(t => t !== target); }
    function targetBelongsToWindow(target, window) { return !!target && target.QsWindow.window === window; }
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
        const candidates = slots.filter(s => s.widgetId === id && s.widget && typeof s.widget.open === "function" && typeof s.widget.close === "function");
        const screen = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "";
        return candidates.find(s => s.window.screen.name === screen) || candidates[0] || null;
    }
    function summonBarWidget(id) { const s = choose(id); if (!s) return false; s.widget.open(); return true; }
    function hideBarWidget(id) { const s = choose(id); if (!s) return false; s.widget.close(); return true; }
    function isBarWidgetOpen(id) { const s = choose(id); return !!s && s.widget.opened; }
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
        list[(index + (direction < 0 ? list.length-1 : 1)) % list.length].widget.open();
        return true;
    }
    Timer { id: tipDelay; interval: 400 }
    IpcHandler {
        target: "research.bar-host"
        function inspect(): string {
            return JSON.stringify({position: host.position, transparent: host.transparent,
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
        readonly property bool skinned: host.barConfig.skinProbe === true && (widgetId === "omarchy.clock" || widgetId === "omarchy.audio")
        readonly property string labelText: customLabel.text
        property var ownedTargets: []
        readonly property var scoped: ScopedBar { ownerSlot: slot }
        implicitWidth: widget && widget.visible ? (host.vertical ? host.barSize : skinned ? customLabel.implicitWidth+20 : widget.implicitWidth) : 0
        implicitHeight: widget && widget.visible ? widget.implicitHeight : 0
        width: implicitWidth
        height: implicitHeight
        Component.onCompleted: host.slots = host.slots.concat([slot])
        Component.onDestruction: host.slots = host.slots.filter(s => s !== slot)
        function bindWidget() {
            if (!widget) return;
            const firstParty = !!(registration.metadata && registration.metadata.firstParty);
            if ("_notePopoutCard" in scoped) {
                scoped._notePopoutCard = card => host.notePopoutCard(card);
                scoped._popoutCardFor = owner => host.popoutCardFor(owner);
                scoped.traySectionDragActive = Qt.binding(() => host.traySectionDragActive);
                scoped.traySectionPopoutOpen = Qt.binding(() => host.traySectionPopoutOpen);
            }
            if (!firstParty && host.shell) scoped.shell = host.shell.pluginShellForBarEntry("research.bar-host", widgetId);
            if ("bar" in widget) widget.bar = firstParty ? host : scoped;
            if ("moduleName" in widget) widget.moduleName = widgetId;
            if ("settings" in widget) widget.settings = typeof entry === "string" ? {} : JSON.parse(JSON.stringify(entry));
        }
        onEntryChanged: bindWidget()
        Text {
            id: customLabel
            visible: slot.skinned
            anchors.centerIn: parent
            text: !slot.widget ? "" : slot.widgetId === "omarchy.clock" ? slot.widget.displayText :
                slot.widget.sink && slot.widget.sink.audio ? Math.round(slot.widget.sink.audio.volume*100)+"%" : "--"
            textFormat: Text.PlainText
            color: host.foreground
            font.family: slot.widgetId === "omarchy.clock" ? "Barlow Condensed" : host.fontFamily
            font.pixelSize: slot.widgetId === "omarchy.clock" ? 21 : 15
        }
        Loader {
            id: load
            opacity: slot.skinned ? 0 : 1
            anchors.fill: parent
            sourceComponent: slot.registration ? slot.registration.component : null
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
    component Strip: Item {
        id: strip
        required property string section
        property var window
        readonly property var entries: host.entries(section)
        readonly property real extent: {
            let total = 0;
            for (let i=0;i<items.count;i++) { const s=items.itemAt(i); if(s) total += host.vertical ? s.height : s.width; }
            return total;
        }
        readonly property real anchorOffset: {
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
            model: strip.entries
            Slot {
                required property var modelData
                required property int index
                entry: modelData
                section: strip.section
                window: strip.window
                readonly property real offset: {
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
    Variants {
        model: Quickshell.screens
        PanelWindow {
            id: surface
            required property var modelData
            screen: modelData
            anchors.top: host.position !== "bottom"
            anchors.bottom: host.position !== "top"
            anchors.left: host.position !== "right"
            anchors.right: host.position !== "left"
            implicitWidth: host.barSize
            implicitHeight: host.barSize
            exclusiveZone: host.barSize
            color: host.transparent ? "transparent" : host.background
            WlrLayershell.namespace: "research-bar-host"
            WlrLayershell.layer: WlrLayer.Top
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            Strip { section:"left"; window:surface; x:host.vertical?0:6; y:host.vertical?6:0 }
            Strip { section:"right"; window:surface; x:host.vertical?0:surface.width-width-6; y:host.vertical?surface.height-height-6:0 }
            Strip { id: center; section:"center"; window:surface; x:host.vertical?0:surface.width/2-anchorOffset; y:host.vertical?surface.height/2-anchorOffset:0 }
            Strip { section:"centerBegin"; window:surface; x:host.vertical?0:center.x-width; y:host.vertical?center.y-height:0 }
            Strip { section:"centerEnd"; window:surface; x:host.vertical?0:center.x+center.width; y:host.vertical?center.y+center.height:0 }
            HoverHandler { onHoveredChanged: host.centerSectionRevealHeld = hovered }
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
