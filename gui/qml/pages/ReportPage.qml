import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import FluentUI

FluScrollablePage {
    id: page
    title: "结果概览"

    property var report: window.currentReport
    property var metrics: report && report.metrics ? report.metrics : {}
    property var astMetrics: report && report.ast_metrics ? report.ast_metrics : null
    property real stdRate: report && report.design_standardization_rate !== undefined
                           ? report.design_standardization_rate : -1

    // ── No data placeholder ─────────────────────────────────

    FluText {
        visible: !window.hasReport
        text: "暂无分析结果，请先在「对比配置」页面运行分析。"
        font: FluTextStyle.Body
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 80
        color: FluTheme.dark ? "#888888" : "#666666"
    }

    // ── Target info ─────────────────────────────────────────

    FluArea {
        visible: window.hasReport
        Layout.fillWidth: true
        Layout.topMargin: 20
        height: 60
        paddings: 16

        RowLayout {
            anchors.fill: parent
            FluText {
                text: "目标：" + (report.target || "")
                font: FluTextStyle.Body
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }
            FluText {
                text: "类型：" + (report.type === "directory" ? "目录对比" : "文件对比")
                font: FluTextStyle.Body
            }
        }
    }

    // ── Summary cards (matches CLI: 变动项 | 变动行数 | 标准化率) ────

    GridLayout {
        visible: window.hasReport
        Layout.fillWidth: true
        Layout.topMargin: 16
        columns: 3
        columnSpacing: 12
        rowSpacing: 12

        // Card: 变动项
        FluArea {
            Layout.fillWidth: true
            height: 100
            paddings: 16

            ColumnLayout {
                anchors.fill: parent
                spacing: 8
                FluText {
                    text: "变动项"
                    font: FluTextStyle.Caption
                    color: FluTheme.dark ? "#AAAAAA" : "#666666"
                }
                FluText {
                    text: String((metrics.added_functions || 0) + (metrics.deleted_functions || 0) + (metrics.modified_functions || 0))
                    font: FluTextStyle.Title
                    color: FluTheme.primaryColor
                }
            }
        }

        // Card: 变动行数 (same logic as CLI line 94-98)
        FluArea {
            Layout.fillWidth: true
            height: 100
            paddings: 16

            ColumnLayout {
                anchors.fill: parent
                spacing: 8
                FluText {
                    text: "变动行数"
                    font: FluTextStyle.Caption
                    color: FluTheme.dark ? "#AAAAAA" : "#666666"
                }
                FluText {
                    text: {
                        if (astMetrics) {
                            return String((astMetrics.ast_lines_added || 0) + (astMetrics.ast_lines_deleted || 0) + (astMetrics.ast_lines_modified || 0))
                        } else {
                            return String((metrics.lines_added_in_mod || 0) + (metrics.lines_deleted_in_mod || 0))
                        }
                    }
                    font: FluTextStyle.Title
                    color: "#FF9800"
                }
            }
        }

        // Card: 标准化率
        FluArea {
            Layout.fillWidth: true
            height: 100
            paddings: 16

            ColumnLayout {
                anchors.fill: parent
                spacing: 8
                FluText {
                    text: "标准化率"
                    font: FluTextStyle.Caption
                    color: FluTheme.dark ? "#AAAAAA" : "#666666"
                }
                FluText {
                    text: stdRate >= 0 ? stdRate.toFixed(4) : "N/A"
                    font: FluTextStyle.Title
                    color: FluTheme.primaryColor
                }
            }
        }
    }

    // ── Function counts (matches CLI: 新增 / 删除 / 修改) ────────

    GridLayout {
        visible: window.hasReport
        Layout.fillWidth: true
        Layout.topMargin: 12
        columns: 3
        columnSpacing: 12

        FluArea {
            Layout.fillWidth: true
            height: 100
            paddings: 16
            ColumnLayout {
                anchors.fill: parent
                spacing: 8
                FluText { text: "新增"; font: FluTextStyle.Caption; color: FluTheme.dark ? "#AAAAAA" : "#666666" }
                FluText { text: String(metrics.added_functions || 0); font: FluTextStyle.Title; color: "#4CAF50" }
            }
        }
        FluArea {
            Layout.fillWidth: true
            height: 100
            paddings: 16
            ColumnLayout {
                anchors.fill: parent
                spacing: 8
                FluText { text: "删除"; font: FluTextStyle.Caption; color: FluTheme.dark ? "#AAAAAA" : "#666666" }
                FluText { text: String(metrics.deleted_functions || 0); font: FluTextStyle.Title; color: "#F44336" }
            }
        }
        FluArea {
            Layout.fillWidth: true
            height: 100
            paddings: 16
            ColumnLayout {
                anchors.fill: parent
                spacing: 8
                FluText { text: "修改"; font: FluTextStyle.Caption; color: FluTheme.dark ? "#AAAAAA" : "#666666" }
                FluText { text: String(metrics.modified_functions || 0); font: FluTextStyle.Title; color: "#FF9800" }
            }
        }
    }

    // ── Mode-specific line detail (text mode: 新增行/删除行, AST mode: 行+节点) ──

    GridLayout {
        visible: window.hasReport && !astMetrics
        Layout.fillWidth: true
        Layout.topMargin: 12
        columns: 2
        columnSpacing: 12

        FluArea {
            Layout.fillWidth: true
            height: 80
            paddings: 16
            ColumnLayout {
                anchors.fill: parent
                spacing: 6
                FluText { text: "新增行"; font: FluTextStyle.Caption; color: FluTheme.dark ? "#AAAAAA" : "#666666" }
                FluText { text: String(metrics.lines_added_in_mod || 0); font: FluTextStyle.Title; color: "#4CAF50" }
            }
        }
        FluArea {
            Layout.fillWidth: true
            height: 80
            paddings: 16
            ColumnLayout {
                anchors.fill: parent
                spacing: 6
                FluText { text: "删除行"; font: FluTextStyle.Caption; color: FluTheme.dark ? "#AAAAAA" : "#666666" }
                FluText { text: String(metrics.lines_deleted_in_mod || 0); font: FluTextStyle.Title; color: "#F44336" }
            }
        }
    }

    // ── AST Metrics (if available) ──────────────────────────

    FluArea {
        visible: window.hasReport && astMetrics !== null
        Layout.fillWidth: true
        Layout.topMargin: 16
        height: 120
        paddings: 16

        ColumnLayout {
            anchors.fill: parent
            spacing: 12

            FluText {
                text: "语法树(AST)度量"
                font: FluTextStyle.BodyStrong
            }

            RowLayout {
                spacing: 40

                ColumnLayout {
                    FluText { text: "新增节点"; font: FluTextStyle.Caption; color: "#888" }
                    FluText { text: String(astMetrics ? astMetrics.ast_nodes_added : 0); color: "#4CAF50" }
                }
                ColumnLayout {
                    FluText { text: "删除节点"; font: FluTextStyle.Caption; color: "#888" }
                    FluText { text: String(astMetrics ? astMetrics.ast_nodes_deleted : 0); color: "#F44336" }
                }
                ColumnLayout {
                    FluText { text: "变更节点"; font: FluTextStyle.Caption; color: "#888" }
                    FluText { text: String(astMetrics ? astMetrics.ast_nodes_modified : 0); color: "#FF9800" }
                }
                ColumnLayout {
                    FluText { text: "新增行数"; font: FluTextStyle.Caption; color: "#888" }
                    FluText { text: String(astMetrics ? astMetrics.ast_lines_added : 0); color: "#4CAF50" }
                }
                ColumnLayout {
                    FluText { text: "删除行数"; font: FluTextStyle.Caption; color: "#888" }
                    FluText { text: String(astMetrics ? astMetrics.ast_lines_deleted : 0); color: "#F44336" }
                }
                ColumnLayout {
                    FluText { text: "变更行数"; font: FluTextStyle.Caption; color: "#888" }
                    FluText { text: String(astMetrics ? astMetrics.ast_lines_modified : 0); color: "#FF9800" }
                }
            }
        }
    }

    // ── File changes (directory mode) ───────────────────────

    FluArea {
        visible: window.hasReport && report.file_changes !== undefined
        Layout.fillWidth: true
        Layout.topMargin: 16
        height: fileChangesCol.implicitHeight + 40
        paddings: 16

        ColumnLayout {
            id: fileChangesCol
            anchors.left: parent.left
            anchors.right: parent.right
            spacing: 8

            FluText {
                text: "文件级变更"
                font: FluTextStyle.BodyStrong
            }

            FluText {
                visible: !!(report.file_changes && report.file_changes.added_files && report.file_changes.added_files.length > 0)
                text: "新增文件：" + (report.file_changes ? report.file_changes.added_files.join(", ") : "")
                color: "#4CAF50"
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }

            FluText {
                visible: !!(report.file_changes && report.file_changes.deleted_files && report.file_changes.deleted_files.length > 0)
                text: "删除文件：" + (report.file_changes ? report.file_changes.deleted_files.join(", ") : "")
                color: "#F44336"
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }

            FluText {
                visible: !!(report.file_changes && (!report.file_changes.added_files || report.file_changes.added_files.length === 0) && (!report.file_changes.deleted_files || report.file_changes.deleted_files.length === 0))
                text: "无文件级增减"
                color: "#888"
            }
        }
    }
}
