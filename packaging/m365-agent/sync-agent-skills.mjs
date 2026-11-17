import { cpSync, mkdirSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageDirectory = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(packageDirectory, "../..");
const skillName = "validate-gtm-output";
const source = resolve(repositoryRoot, "skills", skillName);
const destinationRoot = resolve(packageDirectory, "appPackage", "skills");
const destination = resolve(destinationRoot, skillName);

rmSync(destinationRoot, { recursive: true, force: true });
mkdirSync(destinationRoot, { recursive: true });
cpSync(source, destination, { recursive: true });

console.log(`Bundled skills/${skillName} into the Microsoft 365 agent package.`);
