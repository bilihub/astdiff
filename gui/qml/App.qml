import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import FluentUI

FluWindow {
    id: window
    title: "StdDiff - 代码差异分析工具"
    width: 1100
    height: 720
    minimumWidth: 800
    minimumHeight: 600
    showDark: true

    property var currentReport: ({})
    property bool hasReport: false

    // Navigation items with proper FluentIcons enum values
    property var navItems: [
        { title: "对比配置", icon: FluentIcons.Settings,   idx: 0 },
        { title: "结果概览", icon: FluentIcons.Flag,       idx: 1 },
        { title: "变更详情", icon: FluentIcons.AllApps,    idx: 2 }
    ]

    // ── Navigation + Content ────────────────────────────────

    Row {
        anchors.fill: parent

        // Navigation sidebar
        Rectangle {
            id: sidebar
            width: 220
            height: parent.height
            color: FluTheme.dark ? "#202020" : "#F3F3F3"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 4

                // App title
                FluText {
                    text: "StdDiff"
                    font: FluTextStyle.BodyStrong
                    Layout.leftMargin: 12
                    Layout.topMargin: 8
                    Layout.bottomMargin: 16
                }

                // Nav items
                Repeater {
                    model: window.navItems.length

                    Rectangle {
                        required property int index
                        property var item: window.navItems[index]
                        Layout.fillWidth: true
                        height: 40
                        radius: 6
                        color: {
                            if (stackLayout.currentIndex === item.idx) {
                                return FluTheme.dark ? "#333333" : "#E8E8E8"
                            }
                            if (navMouse.containsMouse) {
                                return FluTheme.dark ? "#2A2A2A" : "#EEEEEE"
                            }
                            return "transparent"
                        }

                        // Active indicator
                        Rectangle {
                            width: 3
                            height: 16
                            radius: 1.5
                            color: FluTheme.primaryColor
                            visible: stackLayout.currentIndex === item.idx
                            anchors {
                                left: parent.left
                                leftMargin: 3
                                verticalCenter: parent.verticalCenter
                            }
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            spacing: 12

                            FluIcon {
                                iconSource: item.icon
                                iconSize: 16
                            }

                            FluText {
                                text: item.title
                                font: FluTextStyle.Body
                                Layout.fillWidth: true
                            }
                        }

                        MouseArea {
                            id: navMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                stackLayout.currentIndex = item.idx
                            }
                        }
                    }
                }

                // Spacer
                Item { Layout.fillHeight: true }

                // Theme toggle in footer
                Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    radius: 6
                    color: darkMouse.containsMouse
                           ? (FluTheme.dark ? "#2A2A2A" : "#EEEEEE")
                           : "transparent"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        spacing: 12

                        FluIcon {
                            iconSource: FluTheme.dark ? FluentIcons.Brightness : FluentIcons.QuietHours
                            iconSize: 16
                        }

                        FluText {
                            text: FluTheme.dark ? "浅色模式" : "深色模式"
                            font: FluTextStyle.Body
                            Layout.fillWidth: true
                        }
                    }

                    MouseArea {
                        id: darkMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (FluTheme.dark) {
                                FluTheme.darkMode = FluThemeType.Light
                            } else {
                                FluTheme.darkMode = FluThemeType.Dark
                            }
                        }
                    }
                }
            }
        }

        // Separator
        Rectangle {
            width: 1
            height: parent.height
            color: FluTheme.dark ? "#333333" : "#E0E0E0"
        }

        // Content area
        StackLayout {
            id: stackLayout
            width: parent.width - sidebar.width - 1
            height: parent.height
            currentIndex: 0

            Loader {
                source: "pages/ComparePage.qml"
            }

            Loader {
                source: "pages/ReportPage.qml"
            }

            Loader {
                source: "pages/DetailPage.qml"
            }
        }
    }

    // ── Backend connections ──────────────────────────────────

    Connections {
        target: backend

        function onCompareFinished() {
            var reportStr = backend.getReportJson()
            window.currentReport = JSON.parse(reportStr)
            window.hasReport = true
            window.showSuccess("分析完成！", 3000)
            stackLayout.currentIndex = 1
        }

        function onCompareError(message) {
            window.showError("分析失败：" + message, 5000)
        }
    }
}
