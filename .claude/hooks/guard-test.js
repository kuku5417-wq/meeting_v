// guard.js 시험기. 실행: node .claude/hooks/guard-test.js  → FAIL 0 이어야 한다.
// 막아야 할 것과 통과해야 할 것을 같이 둔다. 새 우회로를 찾으면 여기에 한 줄 추가하고 guard.js를 고친다.
const { decide } = require("./guard.js");

const E = (file_path) => ({ tool_name: "Edit", tool_input: { file_path } });
const W = (file_path) => ({ tool_name: "Write", tool_input: { file_path } });
const S = (command) => ({ tool_name: "PowerShell", tool_input: { command } });
const B = (command) => ({ tool_name: "Bash", tool_input: { command } });

const CASES = [
  ["block", E("C:\\code_N\\secret\\.env")],
  ["block", E("C:\\code_N\\meeting_v\\.env")],
  ["block", W("C:/code_N/meeting_v/.env.local")],
  ["block", E("C:\\code_N\\meeting_v\\certs\\corp.pem")],
  ["block", E("C:\\code_N\\data\\raw\\조립팀_자주검사기록.xlsx")],
  ["block", W("C:\\code_N\\meeting_v\\.git\\config")],
  ["block", S("Remove-Item -Path out -Recurse -Force")],
  ["block", B("rm -rf build")],
  ["block", B("git push --force origin main")],
  ["block", S("git reset --hard HEAD~1")],
  ["block", S("Copy-Item out\\fixed.xlsx ..\\data\\raw\\a.xlsx")],
  ["block", S("Get-Content ..\\secret\\.env")],
  ["block", B("cat ../secret/.env")],
  ["block", S("python -c \"open('../data/raw/a.csv','w').write('x')\"")],
  ["block", S("Expand-Archive x.zip -DestinationPath ..\\data\\raw")],
  ["block", "이건 JSON이 아님"],
  ["block", { tool_name: "Edit", tool_input: {} }],
  ["allow", E("C:\\code_N\\meeting_v\\.env.template")],
  ["allow", E("C:\\code_N\\meeting_v\\modules\\models.py")],
  ["allow", W("C:\\code_N\\meeting_v\\out\\audit.md")],
  ["allow", E("C:\\code_N\\meeting_v\\data\\samples\\masters\\hull.csv")],
  ["allow", S("uv run pytest -q")],
  ["allow", B("git diff HEAD")],
  ["allow", S("git push origin feature/s2")],
  ["allow", S("python -X utf8 data/samples/masters/_check.py")],
  ["allow", { tool_name: "Read", tool_input: { file_path: "C:/code_N/meeting_v/SPEC.md" } }],
];

let fail = 0;
for (const [want, input] of CASES) {
  const raw = typeof input === "string" ? input : JSON.stringify(input);
  const [code] = decide(raw);
  const got = code === 2 ? "block" : "allow";
  const ok = got === want;
  if (!ok) fail++;
  const label = typeof input === "string" ? input : `${input.tool_name} ${input.tool_input.file_path || input.tool_input.command || ""}`;
  console.log(`${ok ? "ok  " : "FAIL"} ${want.padEnd(5)} ${label}`);
}
console.log(`\nFAIL ${fail} / ${CASES.length}`);
process.exit(fail ? 1 : 0);
