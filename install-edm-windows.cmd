@ECHO ON

SETLOCAL EnableDelayedExpansion

SET INSTALL_EDM_VERSION=3.0.1

SET EDM_MAJOR_MINOR=%MAJOR%.%MINOR%
SET EDM_PACKAGE=edm_cli_%INSTALL_EDM_VERSION%_x86_64.msi
SET EDM_INSTALLER_PATH=%HOMEDRIVE%%HOMEPATH%\.cache\%EDM_PACKAGE%
SET COMMAND="(new-object net.webclient).DownloadFile('https://package-data.enthought.com/edm/win_x86_64/%EDM_MAJOR_MINOR%/%EDM_PACKAGE%', '%EDM_INSTALLER_PATH%')"

IF NOT EXIST %EDM_INSTALLER_PATH% CALL powershell.exe -Command %COMMAND% || GOTO error
CALL msiexec /qn /i %EDM_INSTALLER_PATH% EDMAPPDIR=C:\Enthought\edm || GOTO error

ENDLOCAL
@ECHO.DONE
EXIT

:error:
ENDLOCAL
@ECHO.ERROR
EXIT /b %ERRORLEVEL%
