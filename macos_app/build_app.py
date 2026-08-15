#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import argparse, json, plistlib, shutil, subprocess

APP_NAME = "Reunion Companion"
APP_VERSION = "2.0"
APP_BUILD = "1"
APP_RELEASE = "FFD 2.0 Build 1 — macOS Application Foundation"
ENGINE_BASELINE = "FFD 1.9 RC1"
BUNDLE_ID = "com.reunioncompanion.app"

SWIFT_TEMPLATE = '\nimport AppKit\nimport Foundation\n\nfinal class AppDelegate: NSObject, NSApplicationDelegate {\n    let repoPath = __REPO__\n    let companionURL = URL(string: "http://127.0.0.1:8765/")!\n    var backend: Process?\n    var backendLog: FileHandle?\n    var opened = false\n\n    func applicationDidFinishLaunching(_ notification: Notification) {\n        configureMenu()\n        NSApp.setActivationPolicy(.regular)\n        startOrAttach()\n    }\n\n    func configureMenu() {\n        let mainMenu = NSMenu()\n        let appItem = NSMenuItem()\n        mainMenu.addItem(appItem)\n        let appMenu = NSMenu()\n        appMenu.addItem(withTitle: "About Reunion Companion", action: #selector(showAbout), keyEquivalent: "")\n        appMenu.addItem(NSMenuItem.separator())\n        appMenu.addItem(withTitle: "Open Reunion Companion", action: #selector(openCompanion), keyEquivalent: "o")\n        appMenu.addItem(NSMenuItem.separator())\n        appMenu.addItem(withTitle: "Quit Reunion Companion", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")\n        appItem.submenu = appMenu\n        NSApp.mainMenu = mainMenu\n    }\n\n    @objc func showAbout() {\n        let alert = NSAlert()\n        alert.messageText = "Reunion Companion"\n        alert.informativeText = "FFD 2.0 Build 1 — macOS Application Foundation\\nGenealogy Engine: FFD 1.9 RC1"\n        alert.addButton(withTitle: "OK")\n        alert.runModal()\n    }\n\n    @objc func openCompanion() {\n        NSWorkspace.shared.open(companionURL)\n    }\n\n    func startOrAttach() {\n        DispatchQueue.global(qos: .userInitiated).async {\n            if self.isCompanionReady() {\n                DispatchQueue.main.async { self.openWhenReady() }\n                return\n            }\n            do {\n                try self.launchBackend()\n            } catch {\n                DispatchQueue.main.async {\n                    self.showStartupError("Companion could not be started.\\n\\n\\(error.localizedDescription)")\n                }\n                return\n            }\n\n            for _ in 0..<80 {\n                if self.isCompanionReady() {\n                    DispatchQueue.main.async { self.openWhenReady() }\n                    return\n                }\n                if let p = self.backend, !p.isRunning { break }\n                Thread.sleep(forTimeInterval: 0.25)\n            }\n            DispatchQueue.main.async {\n                self.showStartupError("Companion did not become ready on 127.0.0.1:8765.\\n\\nSee ~/Library/Logs/Reunion Companion/backend.log")\n            }\n        }\n    }\n\n    func launchBackend() throws {\n        let repo = URL(fileURLWithPath: repoPath)\n        let python = repo.appendingPathComponent(".venv/bin/python")\n        guard FileManager.default.isExecutableFile(atPath: python.path) else {\n            throw NSError(domain: "ReunionCompanion", code: 1,\n                          userInfo: [NSLocalizedDescriptionKey: "Python environment not found at \\(python.path)."])\n        }\n\n        let logDir = FileManager.default.homeDirectoryForCurrentUser\n            .appendingPathComponent("Library/Logs/Reunion Companion", isDirectory: true)\n        try FileManager.default.createDirectory(at: logDir, withIntermediateDirectories: true)\n        let logURL = logDir.appendingPathComponent("backend.log")\n        if !FileManager.default.fileExists(atPath: logURL.path) {\n            FileManager.default.createFile(atPath: logURL.path, contents: nil)\n        }\n        let log = try FileHandle(forWritingTo: logURL)\n        try log.seekToEnd()\n        backendLog = log\n\n        let p = Process()\n        p.executableURL = python\n        p.arguments = ["-m","reunion_companion.companion.ui","--no-browser"]\n        p.currentDirectoryURL = repo\n        var env = ProcessInfo.processInfo.environment\n        let src = repo.appendingPathComponent("src").path\n        env["PYTHONPATH"] = src + (env["PYTHONPATH"].map { ":" + $0 } ?? "")\n        p.environment = env\n        p.standardOutput = log\n        p.standardError = log\n        try p.run()\n        backend = p\n    }\n\n    func isCompanionReady() -> Bool {\n        let sem = DispatchSemaphore(value: 0)\n        var ready = false\n        var request = URLRequest(url: companionURL)\n        request.timeoutInterval = 1.0\n        URLSession.shared.dataTask(with: request) { data, response, error in\n            defer { sem.signal() }\n            guard error == nil,\n                  let data = data,\n                  let http = response as? HTTPURLResponse,\n                  (200..<500).contains(http.statusCode),\n                  let body = String(data: data, encoding: .utf8) else { return }\n            ready = body.localizedCaseInsensitiveContains("Reunion Companion")\n        }.resume()\n        _ = sem.wait(timeout: .now() + 1.5)\n        return ready\n    }\n\n    func openWhenReady() {\n        guard !opened else { return }\n        opened = true\n        NSWorkspace.shared.open(companionURL)\n    }\n\n    func showStartupError(_ text: String) {\n        let alert = NSAlert()\n        alert.alertStyle = .critical\n        alert.messageText = "Reunion Companion could not start"\n        alert.informativeText = text\n        alert.addButton(withTitle: "Quit")\n        alert.runModal()\n        NSApp.terminate(nil)\n    }\n\n    func applicationWillTerminate(_ notification: Notification) {\n        if let p = backend, p.isRunning {\n            p.terminate()\n            Thread.sleep(forTimeInterval: 0.2)\n            if p.isRunning { p.interrupt() }\n        }\n        try? backendLog?.close()\n    }\n}\n\nlet app = NSApplication.shared\nlet delegate = AppDelegate()\napp.delegate = delegate\napp.run()\n'

@dataclass(frozen=True)
class BuildPlan:
    repo: Path
    output: Path
    python: Path
    swiftc: str

def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]

def make_plan(repo: Path | None = None, output: Path | None = None) -> BuildPlan:
    repo = (repo or repository_root()).resolve()
    output = (output or (repo / "dist" / f"{APP_NAME}.app")).resolve()
    return BuildPlan(repo, output, repo/".venv/bin/python", shutil.which("swiftc") or "")

def swift_source(repo: Path) -> str:
    return SWIFT_TEMPLATE.replace("__REPO__", json.dumps(str(repo)))

def info_plist() -> dict:
    return {
        "CFBundleDevelopmentRegion":"en",
        "CFBundleDisplayName":APP_NAME,
        "CFBundleExecutable":APP_NAME,
        "CFBundleIdentifier":BUNDLE_ID,
        "CFBundleInfoDictionaryVersion":"6.0",
        "CFBundleName":APP_NAME,
        "CFBundlePackageType":"APPL",
        "CFBundleShortVersionString":APP_VERSION,
        "CFBundleVersion":APP_BUILD,
        "LSMinimumSystemVersion":"13.0",
        "NSHighResolutionCapable":True,
        "LSApplicationCategoryType":"public.app-category.reference",
    }

def validate(plan: BuildPlan) -> list[str]:
    problems=[]
    if not plan.repo.joinpath("src/reunion_companion/companion/ui.py").exists():
        problems.append("Repository does not contain the Companion UI module.")
    if not plan.python.exists():
        problems.append(f"Virtual environment Python not found: {plan.python}")
    if not plan.swiftc:
        problems.append("swiftc was not found. Install Apple's Command Line Tools.")
    return problems

def build(plan: BuildPlan) -> Path:
    problems=validate(plan)
    if problems:
        raise SystemExit("\n".join(problems))
    app=plan.output
    if app.exists(): shutil.rmtree(app)
    macos=app/"Contents"/"MacOS"
    resources=app/"Contents"/"Resources"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)
    source=resources/"ReunionCompanionLauncher.swift"
    source.write_text(swift_source(plan.repo))
    with (app/"Contents"/"Info.plist").open("wb") as f:
        plistlib.dump(info_plist(),f)
    subprocess.run([plan.swiftc, str(source), "-framework","AppKit", "-o", str(macos/APP_NAME)], check=True)
    return app

def install(app: Path, destination: Path) -> Path:
    destination=destination.expanduser().resolve()
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists(): shutil.rmtree(destination)
    shutil.copytree(app,destination,symlinks=True)
    return destination

def main():
    ap=argparse.ArgumentParser(description=APP_RELEASE)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--install",type=Path)
    ap.add_argument("--plan",action="store_true")
    args=ap.parse_args()
    plan=make_plan(output=args.output)
    if args.plan:
        print(f"Release: {APP_RELEASE}")
        print(f"Engine: {ENGINE_BASELINE}")
        print(f"Repository: {plan.repo}")
        print(f"Python: {plan.python}")
        print(f"Output: {plan.output}")
        print(f"swiftc: {plan.swiftc or '(not found)'}")
        return
    app=build(plan)
    print(f"Built: {app}")
    if args.install:
        print(f"Installed: {install(app,args.install)}")

if __name__=="__main__":
    main()
