import QtQuick
import "kit" as Kit

Column {
    id:form
    property bool busy:false
    property bool revealed:false
    signal submitted(string secret)
    signal cancelled()
    signal focusMoved(var control)
    spacing:Kit.Runtime.px(8)
    function submit() { if(!busy && input.text) { const value=input.text;input.clear();submitted(value); } }
    function focusInput() { input.forceActiveFocus();focusMoved(input); }
    Component.onCompleted:Qt.callLater(focusInput)
    Component.onDestruction:input.clear()
    Kit.Micro { text:Kit.Runtime.label("passphrase") }
    Rectangle {
        width:parent.width;height:Kit.Runtime.px(32);color:Kit.Runtime.c("ink-1");border.width:1;border.color:Kit.Runtime.c("accent-ink")
        TextInput {
            id:input;x:Kit.Runtime.px(8);width:parent.width-reveal.width-Kit.Runtime.px(16);height:parent.height
            verticalAlignment:TextInput.AlignVCenter;clip:true;selectByMouse:true;activeFocusOnTab:true
            color:Kit.Runtime.c("paper-1");selectionColor:Kit.Runtime.c("fill");selectedTextColor:Kit.Runtime.c("on-accent")
            font.family:Kit.Runtime.mono;font.pixelSize:Kit.Runtime.px(12);maximumLength:256
            echoMode:form.revealed?TextInput.Normal:TextInput.Password;inputMethodHints:Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
            Accessible.name:Kit.Runtime.tr("passphrase");readOnly:form.busy
            Keys.onPressed:event=> {
                if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter) { form.submit();event.accepted=true; }
                else if(event.key===Qt.Key_Escape) { input.clear();form.cancelled();event.accepted=true; }
                else if(event.key===Qt.Key_Tab) { reveal.forceActiveFocus();event.accepted=true; }
                else if(event.key===Qt.Key_Backspace && cursorPosition===0 || event.key===Qt.Key_Left && cursorPosition===0)event.accepted=true;
            }
            // Cursor movement and edits must not reach the page's shortcuts.
            Keys.onShortcutOverride:event=> { if(event.key!==Qt.Key_Escape)event.accepted=true; }
            cursorDelegate:Rectangle { width:Kit.Runtime.px(7);color:Kit.Runtime.c("fill");visible:input.activeFocus }
        }
        Kit.Button { id:reveal;anchors.right:parent.right;height:parent.height;icon:form.revealed?"visibility_off":"visibility";Accessible.name:Kit.Runtime.tr("show-passphrase");borderVisible:false;onClicked: { form.revealed=!form.revealed;form.focusInput(); } }
    }
    Kit.Button { width:parent.width;text:Kit.Runtime.label("connect");accent:true;enabled:!form.busy && input.text.length>0;onClicked:form.submit() }
}
