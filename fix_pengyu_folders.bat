@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title PENGYU DIGITAL - Fix GitHub Folder Structure

echo.
echo =========================================
echo   PENGYU DIGITAL - Folder Repair
 echo =========================================
echo.
if not exist ".git\" (
  echo ERROR: Place this BAT inside the cloned pengyu-ig-auto folder first.
  echo Nothing was moved.
  pause
  exit /b 1
)
if not exist "publisher.py" (
  echo ERROR: publisher.py was not found in this folder.
  echo Nothing was moved.
  pause
  exit /b 1
)

if not exist ".github\workflows\" mkdir ".github\workflows"
if not exist "docs\media\" mkdir "docs\media"

if exist "instagram-auto.yml" (
  move /Y "instagram-auto.yml" ".github\workflows\instagram-auto.yml" >nul
  echo OK: .github/workflows/instagram-auto.yml
)
if exist "index.html" (
  move /Y "index.html" "docs\index.html" >nul
  echo OK: docs/index.html
)
if exist "brand_intro_30s.mp4" (
  move /Y "brand_intro_30s.mp4" "docs\media\brand_intro_30s.mp4" >nul
  echo OK: docs/media/brand_intro_30s.mp4
)
set "COUNT=0"
for %%F in (post_*.jpg) do (
  if exist "%%~fF" (
    move /Y "%%~fF" "docs\media\" >nul
    set /a COUNT+=1 >nul
  )
)
if exist "test_publisher.py" (
  if not exist "tests\" mkdir "tests"
  move /Y "test_publisher.py" "tests\test_publisher.py" >nul
  echo OK: tests/test_publisher.py
)

echo.
echo Moved %COUNT% JPG files into docs/media.
echo.
if exist ".github\workflows\instagram-auto.yml" (echo PASS: workflow path) else (echo MISSING: workflow file)
if exist "docs\index.html" (echo PASS: website index path) else (echo MISSING: docs/index.html)
if exist "docs\media\post_01.jpg" (echo PASS: images path) else (echo MISSING: docs/media/post_01.jpg)
if exist "docs\media\brand_intro_30s.mp4" (echo PASS: video path) else (echo MISSING: docs/media/brand_intro_30s.mp4)
echo.
echo Next: open GitHub Desktop, Commit to main, then Push origin.
echo This utility does not publish to Instagram or send any files online.
echo.
pause
