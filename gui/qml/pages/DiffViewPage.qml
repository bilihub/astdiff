import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import FluentUI

FluContentPage {
    id: page
    title: "代码对比"

    property string oldContent: window.diffOldContent
    property string newContent: window.diffNewContent
    property string funcName: window.diffFuncName

    // ── No data placeholder ─────────────────────────────────

    FluText {
        visible: oldContent.length === 0 && newContent.length === 0
        text: "请在「变更详情」页面点击一个修改函数查看代码对比。"
        font: FluTextStyle.Body
        anchors.centerIn: parent
        color: FluTheme.dark ? "#888888" : "#666666"
    }

    // ── Header ──────────────────────────────────────────────

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12
        visible: oldContent.length > 0 || newContent.length > 0

        FluText {
            text: "函数: " + funcName
            font: FluTextStyle.BodyStrong
        }

        // ── Side-by-side diff view ──────────────────────────

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8

            // Old version
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 4

                FluText {
                    text: "旧版本"
                    font: FluTextStyle.Body
                    color: "#F44336"
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 6
                    color: FluTheme.dark ? "#1E1E1E" : "#FAFAFA"
                    border.color: FluTheme.dark ? "#333333" : "#E0E0E0"
                    border.width: 1
                    clip: true

                    Flickable {
                        id: flickOld
                        anchors.fill: parent
                        anchors.margins: 8
                        contentWidth: oldText.paintedWidth
                        contentHeight: oldText.paintedHeight
                        clip: true

                        // Sync scrolling
                        onContentYChanged: {
                            if (!flickNew.moving) {
                                flickNew.contentY = contentY
                            }
                        }

                        TextEdit {
                            id: oldText
                            width: flickOld.width
                            text: formatDiffText(oldContent, "old")
                            textFormat: TextEdit.RichText
                            readOnly: true
                            selectByMouse: true
                            font.family: "Consolas, 'Courier New', monospace"
                            font.pixelSize: 13
                            color: FluTheme.dark ? "#D4D4D4" : "#333333"
                            wrapMode: TextEdit.NoWrap
                        }

                        ScrollBar.vertical: FluScrollBar {}
                        ScrollBar.horizontal: FluScrollBar {}
                    }
                }
            }

            // New version
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 4

                FluText {
                    text: "新版本"
                    font: FluTextStyle.Body
                    color: "#4CAF50"
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 6
                    color: FluTheme.dark ? "#1E1E1E" : "#FAFAFA"
                    border.color: FluTheme.dark ? "#333333" : "#E0E0E0"
                    border.width: 1
                    clip: true

                    Flickable {
                        id: flickNew
                        anchors.fill: parent
                        anchors.margins: 8
                        contentWidth: newText.paintedWidth
                        contentHeight: newText.paintedHeight
                        clip: true

                        onContentYChanged: {
                            if (!flickOld.moving) {
                                flickOld.contentY = contentY
                            }
                        }

                        TextEdit {
                            id: newText
                            width: flickNew.width
                            text: formatDiffText(newContent, "new")
                            textFormat: TextEdit.RichText
                            readOnly: true
                            selectByMouse: true
                            font.family: "Consolas, 'Courier New', monospace"
                            font.pixelSize: 13
                            color: FluTheme.dark ? "#D4D4D4" : "#333333"
                            wrapMode: TextEdit.NoWrap
                        }

                        ScrollBar.vertical: FluScrollBar {}
                        ScrollBar.horizontal: FluScrollBar {}
                    }
                }
            }
        }
    }

    // ── Helper: format code with line numbers ───────────────

    function formatDiffText(content, side) {
        if (!content) return ""
        var lines = content.split("\n")
        var parts = []
        for (var i = 0; i < lines.length; i++) {
            var lineNum = String(i + 1).padStart(4, ' ')
            var escaped = escapeHtml(lines[i])
            parts.push("<span style='color:#888;'>" + lineNum + " │ </span>" + escaped)
        }
        return "<pre style='margin:0;'>" + parts.join("\n") + "</pre>"
    }

    function escapeHtml(text) {
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    }
}
