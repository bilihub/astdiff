import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import FluentUI

FluScrollablePage {
    id: page
    title: "对比配置"

    // ── Path inputs ─────────────────────────────────────────

    FluArea {
        Layout.fillWidth: true
        Layout.topMargin: 20
        height: 220
        paddings: 20

        ColumnLayout {
            anchors.fill: parent
            spacing: 16

            FluText {
                text: "选择要对比的代码路径"
                font: FluTextStyle.BodyStrong
            }

            // Old path
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                FluText {
                    text: "旧版本："
                    Layout.preferredWidth: 70
                    verticalAlignment: Text.AlignVCenter
                }

                FluTextBox {
                    id: txt_old_path
                    Layout.fillWidth: true
                    placeholderText: "选择旧版本文件或目录..."
                }

                FluButton {
                    text: "文件"
                    onClicked: {
                        var path = backend.chooseFile()
                        if (path) txt_old_path.text = path
                    }
                }
                FluButton {
                    text: "目录"
                    onClicked: {
                        var path = backend.chooseFolder()
                        if (path) txt_old_path.text = path
                    }
                }
            }

            // New path
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                FluText {
                    text: "新版本："
                    Layout.preferredWidth: 70
                    verticalAlignment: Text.AlignVCenter
                }

                FluTextBox {
                    id: txt_new_path
                    Layout.fillWidth: true
                    placeholderText: "选择新版本文件或目录..."
                }

                FluButton {
                    text: "文件"
                    onClicked: {
                        var path = backend.chooseFile()
                        if (path) txt_new_path.text = path
                    }
                }
                FluButton {
                    text: "目录"
                    onClicked: {
                        var path = backend.chooseFolder()
                        if (path) txt_new_path.text = path
                    }
                }
            }
        }
    }

    // ── Options ─────────────────────────────────────────────

    FluArea {
        Layout.fillWidth: true
        Layout.topMargin: 16
        height: 160
        paddings: 20

        ColumnLayout {
            anchors.fill: parent
            spacing: 16

            FluText {
                text: "分析选项"
                font: FluTextStyle.BodyStrong
            }

            RowLayout {
                spacing: 40

                ColumnLayout {
                    spacing: 8
                    FluText { text: "AST 深度分析" }
                    FluToggleSwitch {
                        id: sw_ast
                        checked: true
                    }
                }

                ColumnLayout {
                    spacing: 8
                    visible: !sw_ast.checked

                    FluText { text: "忽略格式变化" }
                    FluToggleSwitch {
                        id: sw_format
                        checked: false
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                FluText {
                    text: "排除目录："
                    Layout.preferredWidth: 70
                }

                FluTextBox {
                    id: txt_excludes
                    Layout.fillWidth: true
                    placeholderText: "用逗号分隔，例如 build,test,.git"
                }
            }
        }
    }

    // ── Run button ──────────────────────────────────────────

    FluFilledButton {
        Layout.fillWidth: true
        Layout.topMargin: 20
        Layout.preferredHeight: 44
        text: backend.running ? "分析中..." : "开始分析"
        disabled: backend.running || txt_old_path.text.length === 0 || txt_new_path.text.length === 0

        onClicked: {
            backend.compare(
                txt_old_path.text,
                txt_new_path.text,
                sw_ast.checked,
                sw_format.checked,
                txt_excludes.text
            )
        }
    }

    FluProgressRing {
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 16
        visible: backend.running
    }
}
