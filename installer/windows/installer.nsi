; Albion Command Desk - Windows Installer Script
; Requires NSIS 3.0+ from https://nsis.sourceforge.io/

!define APP_NAME "Albion Command Desk"
!define APP_EXECUTABLE "AlbionCommandDesk.exe"
!define APP_VERSION "1.0.0"
!define COMP_NAME "Albion Command Desk"
!define WEB_SITE "https://github.com/albioncommanddesk"

; Installer configuration
OutFile "AlbionCommandDesk-Setup-${APP_VERSION}.exe"
InstallDir "$PROGRAMFILES\Albion Command Desk"
InstallDirRegKey HKCU "Software\Albion Command Desk" ""
RequestExecutionLevel admin
SetCompressor /SOLID lzma
ShowInstDetails show
ShowUnInstDetails show

; Modern UI
!include "MUI2.nsh"

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "albion_dps\qt\ui\command_desk_icon.ico"
!define MUI_UNICON "albion_dps\qt\ui\command_desk_icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer Sections
Section "Main Application" SecMain
  SectionIn RO

  SetOutPath $INSTDIR
  File /r "dist\AlbionCommandDesk\*"

  ; Store installation folder
  WriteRegStr HKCU "Software\Albion Command Desk" "" $INSTDIR

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Add uninstaller to Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Albion Command Desk" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Albion Command Desk" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Albion Command Desk" "Publisher" "${COMP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Albion Command Desk" "DisplayVersion" "${APP_VERSION}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Albion Command Desk" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Albion Command Desk" "NoRepair" 1

  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\Albion Command Desk"
  CreateShortCut "$SMPROGRAMS\Albion Command Desk\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_EXECUTABLE}" 0
  CreateShortCut "$SMPROGRAMS\Albion Command Desk\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0

  ; Create desktop shortcut
  CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_EXECUTABLE}" 0
SectionEnd

Section "Npcap Installation" SecNpcap
  ; Offer to install Npcap if not present
  ; Check if Npcap is installed
  IfFileExists "$WINDIR\System32\drivers\npcap.sys" NpcapInstalled

  MessageBox MB_YESNO "Npcap is required for the scanner feature. Would you like to install Npcap now?" IDYES InstallNpcap IDNO NpcapInstalled

  InstallNpcap:
    File "npcap-1.80.exe" ; Include Npcap installer
    ExecWait "$INSTDIR\npcap-1.80.exe /loopback_support=no /winpcap_mode=yes"
    Delete "$INSTDIR\npcap-1.80.exe"

  NpcapInstalled:
SectionEnd

Section "Auto-start on Windows boot" SecAutostart
  CreateShortCut "$SMSTARTUP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_EXECUTABLE}" 0
SectionEnd

; Uninstaller Section
Section "Uninstall"
  ; Remove files and folders
  RMDir /r "$INSTDIR"

  ; Remove shortcuts
  Delete "$DESKTOP\${APP_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\Albion Command Desk"
  Delete "$SMSTARTUP\${APP_NAME}.lnk"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Albion Command Desk"
  DeleteRegKey HKCU "Software\Albion Command Desk"
SectionEnd

; Component Descriptions
LangString DESC_SecMain ${LANG_ENGLISH} "Main application files"
LangString DESC_SecNpcap ${LANG_ENGLISH} "Npcap packet capture driver (required for scanner)"
LangString DESC_SecAutostart ${LANG_ENGLISH} "Start application automatically on Windows boot"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecNpcap} $(DESC_SecNpcap)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecAutostart} $(DESC_SecAutostart)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Functions
Function .onInit
  ; Check for already installed version
  ReadRegStr $R0 HKCU "Software\Albion Command Desk" ""
  StrCmp $R0 "" done

  MessageBox MB_YESNO|MB_ICONQUESTION "${APP_NAME} is already installed. $\n$\nDo you want to overwrite the existing installation?" IDYES done IDNO no_install

  no_install:
    Abort

  done:
FunctionEnd
