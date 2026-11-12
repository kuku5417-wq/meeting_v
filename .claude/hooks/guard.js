// 가드 훅 (PreToolUse): 비밀·원본 파일 편집과 위험 명령을 실행 전에 막는다.
// - Edit/Write/NotebookEdit: 보호 경로면 차단
// - Bash/PowerShell: 위험 명령, 보호 경로 쓰기·비밀 읽기 명령이면 차단
// - 입력을 읽지 못하면 막는다 (fail-closed). 종료 코드 2 = 차단, stderr가 Claude에게 이유로 간다.
// 보호 대상은 아래 목록만 고친다. 고친 뒤에는 guard-test.js 로 FAIL 0 확인.

const PROTECTED_DIRS = ["secret", "raw", ".git"]; // 경로 중간에 이 폴더가 있으면 보호
const SECRET_FILE = /(^|\/)\.env(\.(?!template$|example$)[^/]*)?$|\.(pem|key)$/i; // .env, .env.local 등 (template·example 제외)
const DANGEROUS = [
  [/\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r/i, "재귀 삭제(rm -rf)"],
  [/Remove-Item\b[^|;]*-Recurse/i, "재귀 삭제(Remove-Item -Recurse)"],
  [/\b(rd|rmdir|del)\s+\/s\b/i, "재귀 삭제(rd/del /s)"],
  [/git\s+push\b[^|;]*(--force\b|-f\b|--force-with-lease)/i, "강제 push"],
  [/git\s+reset\s+--hard/i, "git reset --hard"],
  [/git\s+clean\s+-[a-z]*f/i, "git clean -f"],
];
const WRITE_VERB = /(Copy-Item|Move-Item|Rename-Item|Set-Content|Add-Content|Out-File|Remove-Item|Expand-Archive|\bcopy\b|\bmove\b|\bdel\b|\bren\b|\bcp\b|\bmv\b|\brm\b|\btee\b|>|python|node|uv\s+run)/i;
const READ_VERB = /(Get-Content|\bcat\b|\btype\b|\bmore\b|\bless\b|\bhead\b|\btail\b|Select-String|findstr)/i;

function norm(p) {
  return String(p || "").replace(/\\/g, "/").toLowerCase();
}

function protectedPath(p) {
  const n = norm(p);
  if (!n) return null;
  const segs = n.split("/").filter(Boolean);
  const dir = PROTECTED_DIRS.find((d) => segs.slice(0, -1).includes(d));
  if (dir) return `${dir} 폴더`;
  if (SECRET_FILE.test(n)) return "비밀 파일";
  return null;
}

function commandHit(cmd) {
  for (const [re, label] of DANGEROUS) if (re.test(cmd)) return label;
  const c = norm(cmd);
  const mentionsProtected =
    PROTECTED_DIRS.some((d) => new RegExp(`(^|[\\s"'/])${d.replace(".", "\\.")}(/|[\\s"']|$)`).test(c)) ||
    /(^|[\s"'/])\.env(\.local|\.prod)?(\s|"|'|$)|\.(pem|key)(\s|"|'|$)/.test(c);
  if (!mentionsProtected) return null;
  if (WRITE_VERB.test(cmd)) return "보호 경로를 바꾸는 명령";
  if (READ_VERB.test(cmd)) return "비밀·보호 경로를 읽는 명령";
  return null;
}

function decide(raw) {
  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    return [2, "차단: 훅 입력을 읽지 못함 (fail-closed)"];
  }
  const tool = input.tool_name || "";
  const ti = input.tool_input || {};
  if (/^(Edit|Write|MultiEdit|NotebookEdit)$/.test(tool)) {
    const target = ti.file_path || ti.notebook_path;
    if (!target) return [2, "차단: 편집 대상 경로가 없음 (fail-closed)"];
    const hit = protectedPath(target);
    if (hit) return [2, `차단: ${target} (${hit})\n다음 행동: 원본은 고치지 말고 결과는 out/ 등 작업 폴더에 쓴다. 값이 틀렸다면 보고서에 정정 주석을 달고 사람에게 알린다.`];
    return [0, ""];
  }
  if (/^(Bash|PowerShell)$/.test(tool)) {
    const cmd = ti.command || "";
    if (!cmd) return [2, "차단: 명령이 비어 있음 (fail-closed)"];
    const hit = commandHit(cmd);
    if (hit) return [2, `차단: ${hit}\n명령: ${cmd}\n다음 행동: 꼭 필요하면 사람에게 이유를 말하고 직접 실행을 요청한다.`];
    return [0, ""];
  }
  return [0, ""];
}

if (require.main === module) {
  let raw = "";
  process.stdin.on("data", (c) => (raw += c));
  process.stdin.on("end", () => {
    const [code, msg] = decide(raw);
    if (msg) console.error(msg);
    process.exit(code);
  });
}

module.exports = { decide };
