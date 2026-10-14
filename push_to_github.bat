@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Malivu Mama: GitHub push ===
where git >nul 2>nul || (echo [X] Git install aagala. https://git-scm.com/download/win la install pannu. & pause & exit /b 1)

if not exist ".github\workflows" mkdir ".github\workflows"
if exist "deals.yml" move /y "deals.yml" ".github\workflows\deals.yml" >nul

if not exist ".git" (
  git init -q
  git remote add origin https://github.com/nithish0703/real_deal.git
)
git config user.name >nul 2>nul || git config user.name "nithish0703"
git config user.email >nul 2>nul || git config user.email "nithish0703@users.noreply.github.com"

echo Fetching repo...
git fetch -q origin || (echo [X] Fetch fail. Internet / GitHub login check pannu. & pause & exit /b 1)
set BR=main
git rev-parse -q --verify origin/main >nul 2>nul || set BR=master
git checkout -q -B %BR%
git reset -q origin/%BR%

git add -A
git commit -q -m "Malivu Mama deal bot: Amazon scraper + GitHub Actions workflow" && echo Commit done.
echo Pushing (GitHub login window vandha sign in pannu)...
git push -u origin %BR% && (echo. & echo [OK] Push success! & echo.) || echo [X] Push fail. Mela irukkra error-ai Claude-ku anuppu.
git log --oneline -3
pause
