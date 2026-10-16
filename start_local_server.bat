@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo  量子图谱工作台 - 本地服务
echo  启动后浏览器会自动打开 http://127.0.0.1:8790/
echo  关闭本窗口即停止服务
echo ================================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 llm_proxy.py --port 8790
) else (
  python llm_proxy.py --port 8790
)
echo.
echo 服务已停止。按任意键关闭窗口。
pause >nul
