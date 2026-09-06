const fs = require("fs");
const path = require("path");

const bins = {
  prettier: "prettier/bin/prettier.cjs",
  eslint: "eslint/bin/eslint.js",
  tsc: "typescript/bin/tsc",
  vitest: "vitest/vitest.mjs",
  next: "next/dist/bin/next",
  playwright: "@playwright/test/cli.js",
};

function createShims(targetDir, relPrefix) {
  fs.mkdirSync(targetDir, { recursive: true });
  for (const [name, target] of Object.entries(bins)) {
    const cmdPath = path.join(targetDir, name + ".cmd");
    const targetWin = path.join(relPrefix, target);
    const cmdContent = `@ECHO off\r\nnode "%~dp0\\${targetWin}" %*\r\n`;
    fs.writeFileSync(cmdPath, cmdContent);
  }
}

createShims(path.join(__dirname, "../../node_modules/.bin"), "..");
createShims(
  path.join(__dirname, "../../apps/web/node_modules/.bin"),
  "../../../../node_modules",
);
console.log("Shims created successfully");
