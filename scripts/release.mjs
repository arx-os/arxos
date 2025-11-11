#!/usr/bin/env node
import { execSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";

function run(command, options = {}) {
  execSync(command, { stdio: "inherit", ...options });
}

function runCapture(command, options = {}) {
  return execSync(command, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], ...options }).trim();
}

function parseArgs() {
  const args = process.argv.slice(2);
  const result = { skipTags: false, dryRun: false };
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === "--version" || arg === "-v") {
      result.version = args[i + 1];
      i += 1;
    } else if (arg === "--skip-tags") {
      result.skipTags = true;
    } else if (arg === "--dry-run") {
      result.dryRun = true;
    } else if (arg === "--from") {
      result.fromTag = args[i + 1];
      i += 1;
    } else {
      console.error(`Unknown argument: ${arg}`);
      process.exit(1);
    }
  }
  return result;
}

function ensureVersion(version) {
  if (!version) {
    console.error("Release version is required. Usage: node scripts/release.mjs --version 2.1.0");
    process.exit(1);
  }
  if (!/^\d+\.\d+\.\d+$/.test(version)) {
    console.error(`Version "${version}" must follow SemVer (e.g. 2.1.0).`);
    process.exit(1);
  }
}

function readWorkspaceVersion() {
  const cargoToml = readFileSync("Cargo.toml", "utf8");
  const match = cargoToml.match(/\[workspace\.package][^[]*?version\s*=\s*"([^"]+)"/s);
  if (!match) {
    throw new Error("Unable to read current workspace version from Cargo.toml");
  }
  return match[1];
}

function compareVersions(current, next) {
  const currentParts = current.split(".").map(Number);
  const nextParts = next.split(".").map(Number);
  for (let i = 0; i < 3; i += 1) {
    if (nextParts[i] > currentParts[i]) {
      return true;
    }
    if (nextParts[i] < currentParts[i]) {
      return false;
    }
  }
  return false;
}

function updateWorkspaceVersion(version, dryRun) {
  const cargoPath = "Cargo.toml";
  const content = readFileSync(cargoPath, "utf8");
  const updated = content.replace(
    /(\[workspace\.package][^[]*?version\s*=\s*")(\d+\.\d+\.\d+)(")/s,
    `$1${version}$3`
  );
  if (content === updated) {
    throw new Error("Failed to update workspace version in Cargo.toml");
  }
  if (!dryRun) {
    writeFileSync(cargoPath, updated);
  }
  console.log(`Updated Cargo.toml workspace version to ${version}`);
}

function updatePackageVersion(version, dryRun) {
  if (dryRun) {
    console.log(`[dry-run] npm version ${version} --no-git-tag-version`);
    return;
  }
  run(`npm version ${version} --no-git-tag-version`, { cwd: path.resolve("pwa") });
}

function generateChangelog(version, fromTag, dryRun) {
  const changelogPath = path.resolve("CHANGELOG.md");
  let previousTag = fromTag;
  if (!previousTag) {
    try {
      previousTag = runCapture("git describe --tags --abbrev=0");
    } catch (error) {
      console.warn("No previous git tag found; changelog will cover entire history.");
    }
  }
  let logRange = "";
  if (previousTag) {
    logRange = `${previousTag}..HEAD`;
  }
  let changes = "";
  try {
    changes = runCapture(`git log ${logRange} --pretty=format:%s`);
  } catch {
    changes = "";
  }
  const formatted =
    changes
      .split("\n")
      .filter(Boolean)
      .map((line) => `- ${line}`)
      .join("\n") || "- Internal maintenance";

  const today = new Date().toISOString().slice(0, 10);
  const entry = `## v${version} - ${today}\n\n${formatted}\n\n`;
  const existing = existsSync(changelogPath) ? readFileSync(changelogPath, "utf8") : "";
  if (dryRun) {
    console.log(`[dry-run] Would prepend changelog entry for v${version}`);
    return;
  }
  writeFileSync(changelogPath, entry + existing);
  console.log(`Updated changelog at ${changelogPath}`);
}

function tagRelease(version, skipTags) {
  if (skipTags) {
    console.log("Skipping git tag creation (--skip-tags provided).");
    return;
  }
  const tags = [
    { name: `v${version}`, message: `Release v${version}` },
    { name: `wasm/v${version}`, message: `WASM release v${version}` }
  ];
  for (const tag of tags) {
    try {
      run(`git tag -a ${tag.name} -m "${tag.message}"`);
      console.log(`Created git tag ${tag.name}`);
    } catch (error) {
      console.warn(`Failed to create tag ${tag.name}: ${error.message}`);
    }
  }
}

function buildWasm(dryRun) {
  if (dryRun) {
    console.log("[dry-run] npm run build:wasm (pwa)");
    return;
  }
  run("npm run build:wasm", { cwd: path.resolve("pwa") });
}

function updateLockfile(dryRun) {
  if (dryRun) {
    console.log("[dry-run] cargo generate-lockfile");
    return;
  }
  run("cargo generate-lockfile");
}

function main() {
  const args = parseArgs();
  ensureVersion(args.version);
  const currentVersion = readWorkspaceVersion();
  if (!compareVersions(currentVersion, args.version)) {
    console.error(`New version (${args.version}) must be greater than current version (${currentVersion}).`);
    process.exit(1);
  }

  console.log(`Preparing release v${args.version}${args.dryRun ? " (dry run)" : ""}`);

  updateWorkspaceVersion(args.version, args.dryRun);
  updatePackageVersion(args.version, args.dryRun);
  updateLockfile(args.dryRun);
  buildWasm(args.dryRun);
  generateChangelog(args.version, args.fromTag, args.dryRun);
  tagRelease(args.version, args.skipTags || args.dryRun);

  console.log("Release preparation complete. Review changes and push tags when ready.");
  if (!args.dryRun) {
    run("git status -sb");
  }
}

main();

