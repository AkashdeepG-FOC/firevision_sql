
; Fire Vision Pro Installer Script
!define APPNAME "Fire Vision Pro"
!define COMPANYNAME "FOC Security"
!define DESCRIPTION "AI-Powered CCTV Surveillance System"
!define VERSIONMAJOR 2
!define VERSIONMINOR 0
!define VERSIONBUILD 0

!define HELPURL "https://github.com/your-repo/fire-vision-pro"
!define UPDATEURL "https://github.com/your-repo/fire-vision-pro/releases"
!define ABOUTURL "https://github.com/your-repo/fire-vision-pro"

!define INSTALLSIZE 500000  ; Estimate size in KB

RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\${COMPANYNAME}\${APPNAME}"

Name "${APPNAME}"
Icon "icon.ico"
outFile "FireVisionPro_Installer.exe"

!include LogicLib.nsh

page components
page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    messageBox mb_iconstop "Administrator rights required!"
    setErrorLevel 740
    quit
${EndIf}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "install"
    setOutPath $INSTDIR
    
    ; Copy all files
    file /r "dist\FireVisionPro\*"
    
    ; Create uninstaller
    writeUninstaller "$INSTDIR\uninstall.exe"
    
    ; Create start menu shortcut
    createDirectory "$SMPROGRAMS\${COMPANYNAME}"
    createShortCut "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk" "$INSTDIR\FireVisionPro.exe" "" "$INSTDIR\icon.ico"
    
    ; Create desktop shortcut
    createShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\FireVisionPro.exe" "" "$INSTDIR\icon.ico"
    
    ; Registry information for add/remove programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayIcon" "$INSTDIR\icon.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
sectionEnd

section "uninstall"
    delete "$INSTDIR\uninstall.exe"
    rmDir /r "$INSTDIR"
    
    delete "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk"
    rmDir "$SMPROGRAMS\${COMPANYNAME}"
    
    delete "$DESKTOP\${APPNAME}.lnk"
    
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}"
sectionEnd
