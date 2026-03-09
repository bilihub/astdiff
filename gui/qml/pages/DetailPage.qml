import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import FluentUI

FluScrollablePage {
    id: page
    title: "变更详情"

    property var report: window.currentReport
    property var details: report && report.details ? report.details : {}
    property bool isAst: report && report.ast_metrics !== undefined

    // Group all changes by file (matches CLI directory-mode output)
    property var fileGroups: {
        if (!window.hasReport || !details) return []

        var map = {}
        var order = []

        function ensureFile(filepath) {
            if (!(filepath in map)) {
                map[filepath] = { file: filepath, added: [], deleted: [], modified: [] }
                order.push(filepath)
            }
        }

        var addedList = details.added || []
        for (var i = 0; i < addedList.length; i++) {
            var a = addedList[i]
            var af = a.file || "未知文件"
            ensureFile(af)
            map[af].added.push(a)
        }

        var deletedList = details.deleted || []
        for (var j = 0; j < deletedList.length; j++) {
            var d = deletedList[j]
            var df = d.file || "未知文件"
            ensureFile(df)
            map[df].deleted.push(d)
        }

        var modifiedList = details.modified || []
        for (var k = 0; k < modifiedList.length; k++) {
            var m = modifiedList[k]
            var mf = m.file || "未知文件"
            ensureFile(mf)
            map[mf].modified.push(m)
        }

        var result = []
        for (var idx = 0; idx < order.length; idx++) {
            result.push(map[order[idx]])
        }
        return result
    }

    // ── No data placeholder ─────────────────────────────────

    FluText {
        visible: !window.hasReport
        text: "暂无分析结果，请先在「对比配置」页面运行分析。"
        font: FluTextStyle.Body
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 80
        color: FluTheme.dark ? "#888888" : "#666666"
    }

    // ── File-grouped details ────────────────────────────────

    Repeater {
        model: fileGroups.length

        delegate: FluArea {
            id: fileArea
            property int fileIndex: index
            property var grp: fileGroups[fileIndex]

            Layout.fillWidth: true
            Layout.topMargin: fileIndex === 0 ? 20 : 12
            height: fileCol.implicitHeight + 40
            paddings: 16

            ColumnLayout {
                id: fileCol
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: 4

                // File header
                FluText {
                    property int total: (fileArea.grp.added ? fileArea.grp.added.length : 0) +
                                        (fileArea.grp.deleted ? fileArea.grp.deleted.length : 0) +
                                        (fileArea.grp.modified ? fileArea.grp.modified.length : 0)
                    text: "📄 " + fileArea.grp.file + "  (" + total + " 项变动)"
                    font: FluTextStyle.BodyStrong
                    Layout.bottomMargin: 8
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }

                // ── Added functions ──
                Repeater {
                    model: fileArea.grp.added || []
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 32
                        radius: 4
                        color: FluTheme.dark ? "#1A4CAF50" : "#104CAF50"
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            FluText {
                                text: "+ " + modelData.name
                                color: "#4CAF50"
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                        }
                    }
                }

                // ── Deleted functions ──
                Repeater {
                    model: fileArea.grp.deleted || []
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 32
                        radius: 4
                        color: FluTheme.dark ? "#1AF44336" : "#10F44336"
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            FluText {
                                text: "- " + modelData.name
                                color: "#F44336"
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                        }
                    }
                }

                // ── Modified functions (expandable drawer) ──
                Repeater {
                    model: fileArea.grp.modified || []

                    delegate: ColumnLayout {
                        id: modItem
                        Layout.fillWidth: true
                        spacing: 0

                        property var funcData: modelData
                        property bool expanded: false

                        // Header row (clickable toggle)
                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: 4
                            color: modMouse.containsMouse
                                   ? (FluTheme.dark ? "#33FF9800" : "#20FF9800")
                                   : (FluTheme.dark ? "#1AFF9800" : "#10FF9800")

                            MouseArea {
                                id: modMouse
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                hoverEnabled: true
                                onClicked: modItem.expanded = !modItem.expanded
                            }

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                spacing: 8

                                FluIcon {
                                    iconSource: modItem.expanded ? FluentIcons.ChevronDown : FluentIcons.ChevronRight
                                    iconSize: 12
                                }

                                FluText {
                                    text: "~ " + modItem.funcData.name
                                    color: "#FF9800"
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                }

                                FluText {
                                    visible: page.isAst
                                    text: "(节点变更: " + (modItem.funcData.ast_nodes_modified || 0) + ")"
                                    font: FluTextStyle.Caption
                                    color: FluTheme.dark ? "#AAAAAA" : "#888888"
                                }

                                FluText {
                                    visible: !page.isAst
                                    text: "(+" + (modItem.funcData.lines_added || 0) + " / -" + (modItem.funcData.lines_deleted || 0) + ")"
                                    font: FluTextStyle.Caption
                                    color: FluTheme.dark ? "#AAAAAA" : "#888888"
                                }
                            }
                        }

                        // Drawer content (expanded)
                        Rectangle {
                            visible: modItem.expanded
                            Layout.fillWidth: true
                            Layout.leftMargin: 24
                            height: visible ? drawerCol.implicitHeight + 16 : 0
                            radius: 4
                            color: FluTheme.dark ? "#15FFFFFF" : "#08000000"

                            ColumnLayout {
                                id: drawerCol
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: 8
                                spacing: 2

                                // AST mode: show ast_change_details
                                Repeater {
                                    model: page.isAst ? (modItem.funcData.ast_change_details || []) : []
                                    delegate: FluText {
                                        Layout.fillWidth: true
                                        wrapMode: Text.Wrap
                                        font: FluTextStyle.Caption
                                        color: {
                                            if (modelData.type === "added") return "#4CAF50"
                                            if (modelData.type === "deleted") return "#F44336"
                                            return "#FF9800"
                                        }
                                        text: {
                                            var ct = modelData.type || ""
                                            var ot = (modelData.old_text || "").replace(/\s+/g, " ")
                                            var nt = (modelData.new_text || "").replace(/\s+/g, " ")
                                            if (ot.length > 60) ot = ot.substring(0, 57) + "..."
                                            if (nt.length > 60) nt = nt.substring(0, 57) + "..."

                                            if (ct === "modified" || ct === "replaced") {
                                                var label = ct === "modified" ? "修改" : "替换"
                                                return label + " <" + modelData.node_type + "> 旧" + modelData.old_line + "→新" + modelData.new_line + ":  「" + ot + "」→「" + nt + "」"
                                            } else if (ct === "added") {
                                                return "新增 <" + modelData.node_type + "> 新" + modelData.new_line + ":  「" + nt + "」"
                                            } else if (ct === "deleted") {
                                                return "删除 <" + modelData.node_type + "> 旧" + modelData.old_line + ":  「" + ot + "」"
                                            }
                                            return ct + " " + ot
                                        }
                                    }
                                }

                                // Non-AST mode: show unified diff lines
                                Repeater {
                                    model: !page.isAst ? page.computeDiffLines(modItem.funcData.old_content || "", modItem.funcData.new_content || "") : []
                                    delegate: FluText {
                                        Layout.fillWidth: true
                                        wrapMode: Text.Wrap
                                        font.family: "Consolas"
                                        font.pixelSize: 12
                                        color: {
                                            if (modelData.startsWith("+")) return "#4CAF50"
                                            if (modelData.startsWith("-")) return "#F44336"
                                            if (modelData.startsWith("@@")) return "#9C27B0"
                                            return FluTheme.dark ? "#CCCCCC" : "#333333"
                                        }
                                        text: modelData
                                    }
                                }

                                // Empty state
                                FluText {
                                    visible: page.isAst && (!modItem.funcData.ast_change_details || modItem.funcData.ast_change_details.length === 0)
                                    text: "(无 AST 变更详情)"
                                    font: FluTextStyle.Caption
                                    color: "#888"
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Simple line-diff computation for non-AST mode
    function computeDiffLines(oldText, newText) {
        if (!oldText && !newText) return []
        var oldLines = oldText.split("\n")
        var newLines = newText.split("\n")
        var result = []
        var m = oldLines.length
        var n = newLines.length

        if (m + n > 200) {
            result.push("@@ 内容过长，仅显示摘要 @@")
            result.push("- 旧版本 " + m + " 行")
            result.push("+ 新版本 " + n + " 行")
            return result
        }

        var dp = []
        for (var i = 0; i <= m; i++) {
            dp[i] = []
            for (var j = 0; j <= n; j++) {
                if (i === 0 || j === 0) dp[i][j] = 0
                else if (oldLines[i-1].trim() === newLines[j-1].trim()) dp[i][j] = dp[i-1][j-1] + 1
                else dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1])
            }
        }

        var diff = []
        var ii = m, jj = n
        while (ii > 0 || jj > 0) {
            if (ii > 0 && jj > 0 && oldLines[ii-1].trim() === newLines[jj-1].trim()) {
                diff.unshift({ type: " ", text: oldLines[ii-1] }); ii--; jj--
            } else if (jj > 0 && (ii === 0 || dp[ii][jj-1] >= dp[ii-1][jj])) {
                diff.unshift({ type: "+", text: newLines[jj-1] }); jj--
            } else {
                diff.unshift({ type: "-", text: oldLines[ii-1] }); ii--
            }
        }

        var changed = []
        for (var k = 0; k < diff.length; k++) {
            if (diff[k].type !== " ") changed.push(k)
        }
        if (changed.length === 0) { result.push("  (无文本差异)"); return result }

        var shown = {}
        for (var c = 0; c < changed.length; c++) {
            for (var w = Math.max(0, changed[c] - 2); w <= Math.min(diff.length - 1, changed[c] + 2); w++)
                shown[w] = true
        }

        var lastShown = -1
        for (var s = 0; s < diff.length; s++) {
            if (shown[s]) {
                if (lastShown >= 0 && s - lastShown > 1) result.push("@@ ... @@")
                result.push(diff[s].type + " " + diff[s].text)
                lastShown = s
            }
        }
        return result
    }
}
