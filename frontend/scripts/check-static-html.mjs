import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const root = process.cwd();
const pages = fs.readdirSync(root).filter((name) => name.endsWith(".html"));
let checked = 0;
const failures = [];

for (const page of pages) {
  const html = fs.readFileSync(path.join(root, page), "utf8");
  const tags = html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi);
  let index = 0;
  for (const match of tags) {
    if (/\bsrc\s*=/.test(match[1])) continue;
    const source = match[2].trim();
    if (!source) continue;
    checked += 1;
    try {
      new vm.Script(source, { filename: page + ":inline-script-" + (++index) });
    } catch (error) {
      failures.push(page + ": " + error.message);
    }
  }
}

if (failures.length) {
  console.error("Inline JavaScript syntax errors:");
  for (const failure of failures) console.error(" - " + failure);
  process.exit(1);
}
console.log("Validated JavaScript syntax in " + checked + " inline script(s) across " + pages.length + " HTML pages.");
