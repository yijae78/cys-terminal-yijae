<#
.SYNOPSIS
  cys-app.exe 무중단(데몬 유지) 핫스왑 — 분리 프로세스 안전 집행기.

.DESCRIPTION
  스테이징된 신규 cys-app.exe(GUI 실행체)를 설치본과 교체하고 앱을 재시작한다.
  데몬 cysd·노드 PTY 프로세스는 유지되고(앱 GUI만 교체), 앱 재시작 시 모든 surface 화면이
  잠시 절단되나 재부착된다. 이 스크립트는 -Execute 시 자기 자신을 분리(detached) 프로세스로
  재기동하므로, 앱 절단이 이 스크립트를 죽여도 분리 인스턴스가 완주한다.

  안전장치:
    · 백업     — 설치본 exe + ~/.cys/pack 을 타임스탬프 폴더에 보관(전례 규칙)
    · 버전게이트 — 신규 exe 존재·크기·ProductVersion(ExpectVersion) 일치·설치본과 상이 확인
    · 자동롤백  — 교체 후 헬스체크 실패 시 백업 exe로 원복·재시작·재검
    · 헬스체크  — 재시작 후 cys-app 프로세스 생존 + cysd(cys identify) 응답 확인
    · 로그      — ~/.cys/swap-cysapp-YYYYMMDD.log 에 전 단계 타임스탬프 기록

  ★기본은 DRY-RUN(검증만·무변경). 실제 집행은 -Execute. master가 검토 후 기동 조율한다.

.PARAMETER Execute
  실제 집행. 미지정 시 프리플라이트 검증만 수행하고 변경 없이 종료(dry-run).

.PARAMETER Detached
  내부용 — 분리 재기동된 인스턴스 표시(직접 지정 금지).

.EXAMPLE
  # 1) dry-run 검증(무변경 · master 사전 검토용)
  powershell -ExecutionPolicy Bypass -File scripts\win\swap-cysapp.ps1
  # 2) 실제 집행(분리 프로세스 자동 재기동 → 완주)
  powershell -ExecutionPolicy Bypass -File scripts\win\swap-cysapp.ps1 -Execute
#>
[CmdletBinding()]
param(
  [switch]$Execute,
  [switch]$Detached,
  [string]$NewExe        = "",
  [string]$InstalledExe  = (Join-Path $env:LOCALAPPDATA "cys\cys-app.exe"),
  [string]$CysCli        = (Join-Path $env:LOCALAPPDATA "cys\cys.EXE"),
  [string]$PackDir       = (Join-Path $env:USERPROFILE ".cys\pack"),
  [string]$ExpectVersion = "0.12.54",
  [int]$HealthTimeoutSec = 45
)

$ErrorActionPreference = "Stop"

# 신규 exe 기본 경로 = 이 스크립트 기준 리포 target/release (파라미터 미지정 시).
if (-not $NewExe) {
  $NewExe = (Resolve-Path (Join-Path $PSScriptRoot "..\..\target\release\cys-app.exe") -ErrorAction SilentlyContinue)
  if (-not $NewExe) { $NewExe = (Join-Path $PSScriptRoot "..\..\target\release\cys-app.exe") }
}

$stamp    = Get-Date -Format "yyyyMMdd-HHmmss"
$day      = Get-Date -Format "yyyyMMdd"
$logDir   = Join-Path $env:USERPROFILE ".cys"
$logFile  = Join-Path $logDir ("swap-cysapp-{0}.log" -f $day)
$backupDir= Join-Path $env:USERPROFILE (".cys\swap-backups\{0}" -f $stamp)

function Log {
  param([string]$msg, [string]$level = "INFO")
  $line = ("{0} [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $level, $msg)
  try { Add-Content -Path $logFile -Value $line -Encoding UTF8 } catch {}
  Write-Host $line
}

# ── 분리(detached) 재기동: 앱 절단이 이 프로세스를 죽여도 사본이 완주 ──
if ($Execute -and -not $Detached) {
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  Log "분리 프로세스로 재기동한다(앱 절단 대비). 이 콘솔은 종료됨 — 진행은 로그로 추적: $logFile"
  $psArgs = @(
    "-ExecutionPolicy","Bypass","-NonInteractive","-WindowStyle","Hidden",
    "-File", $PSCommandPath, "-Execute", "-Detached",
    "-NewExe", $NewExe, "-InstalledExe", $InstalledExe, "-CysCli", $CysCli,
    "-PackDir", $PackDir, "-ExpectVersion", $ExpectVersion, "-HealthTimeoutSec", $HealthTimeoutSec
  )
  $p = Start-Process -FilePath "powershell.exe" -ArgumentList $psArgs -WindowStyle Hidden -PassThru
  Log ("분리 인스턴스 기동 PID={0}. 집행은 그 프로세스가 수행한다." -f $p.Id)
  exit 0
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$modeStr = if ($Execute) { "EXECUTE" } else { "DRY-RUN" }
$detStr  = if ($Detached) { "yes" } else { "no" }
Log "════════ cys-app swap 시작 (mode=$modeStr, detached=$detStr) ════════"
Log "NewExe=$NewExe"
Log "InstalledExe=$InstalledExe"
Log "PackDir=$PackDir  ExpectVersion=$ExpectVersion"

# ── 1) 버전게이트/프리플라이트 (항상 · 무변경) ──
$gateOk = $true
function Gate([bool]$cond, [string]$ok, [string]$bad) {
  if ($cond) { Log "GATE OK  · $ok" } else { Log "GATE FAIL · $bad" "ERROR"; $script:gateOk = $false }
}
Gate (Test-Path $NewExe)       "신규 exe 존재: $NewExe"                 "신규 exe 없음: $NewExe (먼저 cargo build --release -p cys-app)"
Gate (Test-Path $InstalledExe) "설치본 존재: $InstalledExe"             "설치본 없음: $InstalledExe"
Gate (Test-Path $PackDir)      "pack 존재: $PackDir"                     "pack 없음: $PackDir"
if (Test-Path $NewExe) {
  $newSize = (Get-Item $NewExe).Length
  Gate ($newSize -gt 5MB) ("신규 exe 크기 정상: {0:N0} bytes" -f $newSize) ("신규 exe 크기 비정상(<5MB): {0}" -f $newSize)
  $newVer = (Get-Item $NewExe).VersionInfo.ProductVersion
  if ($newVer) { $newVer = ($newVer -replace "\s","") }
  Gate ($newVer -eq $ExpectVersion) "신규 exe ProductVersion=$newVer (기대치 일치)" "신규 exe 버전=$newVer ≠ 기대 $ExpectVersion"
}
if ((Test-Path $NewExe) -and (Test-Path $InstalledExe)) {
  $differ = -not (Get-FileHash $NewExe).Hash.Equals((Get-FileHash $InstalledExe).Hash)
  Gate $differ "신규 exe가 설치본과 상이(교체 대상 유효)" "신규 exe가 설치본과 동일 — 교체 불요(이미 최신?)"
}

if (-not $gateOk) { Log "버전게이트 실패 — 변경 없이 중단." "ERROR"; exit 2 }
Log "버전게이트 전부 통과."

if (-not $Execute) {
  Log "DRY-RUN 완료 — 검증만 수행, 변경 없음. 실제 집행은 -Execute 로 재실행하라."
  Log "════════ end (dry-run) ════════"
  exit 0
}

# ── 2) 백업 (exe + pack) ──
try {
  New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
  $exeBackup = Join-Path $backupDir "cys-app.exe"
  Copy-Item -Path $InstalledExe -Destination $exeBackup -Force
  if (-not (Test-Path $exeBackup)) { throw "exe 백업 실패" }
  Log "백업: 설치본 exe → $exeBackup"

  $packBackup = Join-Path $backupDir "pack"
  # robocopy /MIR (미러) — 대용량 트리 효율. exit code 0-7=성공, 8+=오류.
  $rc = Start-Process robocopy -ArgumentList @($PackDir, $packBackup, "/MIR", "/NFL","/NDL","/NJH","/NJS","/NP","/R:1","/W:1") -Wait -PassThru -WindowStyle Hidden
  if ($rc.ExitCode -ge 8) { throw ("pack 백업(robocopy) 실패 exit={0}" -f $rc.ExitCode) }
  Log ("백업: pack → $packBackup (robocopy exit={0})" -f $rc.ExitCode)
} catch {
  Log "백업 단계 실패: $_ — 변경 없이 중단." "ERROR"; exit 3
}

# ── 프로세스 헬퍼 (정지·재시작·롤백 — 호출 이전에 정의) ──
function Stop-CysApp {
  $procs = Get-Process -Name "cys-app" -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $InstalledExe }
  foreach ($pr in $procs) {
    Log ("cys-app 정지 PID={0}" -f $pr.Id)
    try { $pr | Stop-Process -Force -ErrorAction Stop } catch { Log "정지 경고: $_" "WARN" }
  }
  # 종료 대기(최대 15초)
  for ($i=0; $i -lt 30; $i++) {
    $still = Get-Process -Name "cys-app" -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $InstalledExe }
    if (-not $still) { return $true }
    Start-Sleep -Milliseconds 500
  }
  return $false
}
function Start-CysApp {
  $p = Start-Process -FilePath $InstalledExe -WorkingDirectory (Split-Path $InstalledExe) -PassThru
  Log ("cys-app 재시작 PID={0}" -f $p.Id)
  return $p
}
function Rollback([string]$reason) {
  Log "롤백 개시 — 사유: $reason" "WARN"
  try {
    [void](Stop-CysApp)
    Copy-Item -Path $exeBackup -Destination $InstalledExe -Force
    Log "롤백: 백업 exe 원복 → $InstalledExe"
    [void](Start-CysApp)
    Start-Sleep -Seconds 3
    $alive = Get-Process -Name "cys-app" -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $InstalledExe }
    if ($alive) { Log "롤백 완료 — 이전 버전으로 복구·앱 기동 확인." "WARN" }
    else { Log "롤백 후 앱 기동 미확인 — 수동 점검 필요! 백업: $backupDir" "ERROR" }
  } catch {
    Log "롤백 실패: $_ — 수동 복구 필요! 백업 exe=$exeBackup, pack=$packBackup" "ERROR"
  }
}

# ── 3) 앱 정지 (cys-app GUI만 · cysd 불가침) ──
if (-not (Stop-CysApp)) { Log "cys-app 종료 확인 실패(파일 잠금 위험) — 중단." "ERROR"; exit 4 }
Log "cys-app 정지 완료(cysd·노드 프로세스는 유지)."

# ── 4) 교체 ──
try {
  Copy-Item -Path $NewExe -Destination $InstalledExe -Force
  $instVer = (Get-Item $InstalledExe).VersionInfo.ProductVersion -replace "\s",""
  if (-not (Get-FileHash $InstalledExe).Hash.Equals((Get-FileHash $NewExe).Hash)) { throw "교체 후 해시 불일치" }
  Log "교체 완료: 신규 exe → $InstalledExe (ver=$instVer)"
} catch {
  Log "교체 실패: $_ — 롤백 시도." "ERROR"
  Rollback "교체 실패"; exit 5
}

# ── 5) 재시작 ──
[void](Start-CysApp)

# ── 6) 헬스체크 (앱 생존 + cysd 응답) ──
$healthy = $false
$deadline = (Get-Date).AddSeconds($HealthTimeoutSec)
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 2
  $appAlive = [bool](Get-Process -Name "cys-app" -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $InstalledExe })
  $cysdOk = $false
  if (Test-Path $CysCli) {
    try { & $CysCli identify *> $null; $cysdOk = ($LASTEXITCODE -eq 0) } catch { $cysdOk = $false }
  } else { $cysdOk = $true } # CLI 부재면 데몬 응답 검사 스킵(앱 생존만)
  if ($appAlive -and $cysdOk) { $healthy = $true; break }
}

if ($healthy) {
  Log "헬스체크 통과 — cys-app 생존 + cysd 응답. swap 성공."
  Log "백업 보관: $backupDir (문제 시 이 exe로 수동 원복 가능)"
  Log "════════ end (SUCCESS) ════════"
  exit 0
} else {
  Log "헬스체크 실패(앱 생존 또는 cysd 응답 미확인, ${HealthTimeoutSec}s) — 자동 롤백." "ERROR"
  Rollback "헬스체크 실패"
  Log "════════ end (ROLLED BACK) ════════"
  exit 6
}
