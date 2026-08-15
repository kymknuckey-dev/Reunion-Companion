#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import argparse, json, plistlib, shutil, subprocess

APP_NAME = "Reunion Companion"
APP_VERSION = "2.0"
APP_BUILD = "3"
APP_RELEASE = "FFD 2.0 Build 3 — Native Application Integration"
ENGINE_BASELINE = "FFD 1.9 RC1"
BUNDLE_ID = "com.reunioncompanion.app"

SWIFT_TEMPLATE = '\nimport AppKit\nimport Foundation\nimport WebKit\n\nfinal class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate {\n    let repoPath = __REPO__\n    let companionURL = URL(string: "http://127.0.0.1:8765/")!\n    var backend: Process?\n    var backendLog: FileHandle?\n    var window: NSWindow?\n    var webView: WKWebView?\n\n    func applicationDidFinishLaunching(_ notification: Notification) {\n        configureMenu(); NSApp.setActivationPolicy(.regular); createWindow(); NSApp.activate(ignoringOtherApps: true); startOrAttach()\n    }\n    func configureMenu() {\n        let mainMenu=NSMenu(); let appItem=NSMenuItem(); let appMenu=NSMenu()\n        appMenu.addItem(withTitle:"About Reunion Companion",action:#selector(showAbout),keyEquivalent:"")\n        appMenu.addItem(withTitle:"Diagnostics…",action:#selector(showDiagnostics),keyEquivalent:"")\n        appMenu.addItem(NSMenuItem.separator()); appMenu.addItem(withTitle:"Quit Reunion Companion",action:#selector(NSApplication.terminate(_:)),keyEquivalent:"q")\n        appItem.submenu=appMenu; mainMenu.addItem(appItem)\n        let editItem=NSMenuItem(); let editMenu=NSMenu(title:"Edit")\n        editMenu.addItem(withTitle:"Cut",action:#selector(NSText.cut(_:)),keyEquivalent:"x")\n        editMenu.addItem(withTitle:"Copy",action:#selector(NSText.copy(_:)),keyEquivalent:"c")\n        editMenu.addItem(withTitle:"Paste",action:#selector(NSText.paste(_:)),keyEquivalent:"v")\n        editMenu.addItem(NSMenuItem.separator())\n        editMenu.addItem(withTitle:"Select All",action:#selector(NSText.selectAll(_:)),keyEquivalent:"a")\n        editItem.submenu=editMenu; mainMenu.addItem(editItem)\n        let viewItem=NSMenuItem(); let viewMenu=NSMenu(title:"View")\n        viewMenu.addItem(withTitle:"Reload",action:#selector(reloadCurrentPage),keyEquivalent:"r")\n        viewItem.submenu=viewMenu; mainMenu.addItem(viewItem)\n        let windowItem=NSMenuItem(); let windowMenu=NSMenu(title:"Window")\n        windowMenu.addItem(withTitle:"Reunion Companion",action:#selector(showMainWindow),keyEquivalent:"0"); windowItem.submenu=windowMenu; mainMenu.addItem(windowItem); NSApp.windowsMenu=windowMenu; NSApp.mainMenu=mainMenu\n    }\n    func createWindow() {\n        let frame=NSRect(x:0,y:0,width:1280,height:820)\n        let w=NSWindow(contentRect:frame,styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)\n        w.title="Reunion Companion"; w.minSize=NSSize(width:900,height:600); w.center(); w.delegate=self; w.isReleasedWhenClosed=false\n        let web=WKWebView(frame:w.contentView?.bounds ?? frame,configuration:WKWebViewConfiguration()); web.autoresizingMask=[.width,.height]; web.navigationDelegate=self\n        w.contentView=web; window=w; webView=web; w.makeKeyAndOrderFront(nil)\n    }\n    @objc func showAbout() { let a=NSAlert(); a.messageText="Reunion Companion"; a.informativeText="FFD 2.0 Build 3 — Native Application Integration\\\\nGenealogy Engine: FFD 1.9 RC1"; a.addButton(withTitle:"OK"); a.runModal() }\n    @objc func reloadCurrentPage() { webView?.reload() }\n    @objc func showDiagnostics() {\n        let backendState = isCompanionReady() ? "Running" : "Not responding"\n        let ollamaState = isOllamaReady() ? "Running" : "Not responding"\n        let dbPath = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".reunion-companion/companion.sqlite3").path\n        let logPath = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/Reunion Companion/backend.log").path\n        let model = ProcessInfo.processInfo.environment["REUNION_LLM_MODEL"] ?? configuredModel()\n        let modelDisplay = model.isEmpty ? "(automatic)" : model\n        let a=NSAlert(); a.messageText="Reunion Companion Diagnostics"\n        a.informativeText="Application: FFD 2.0 Build 3 — Native Application Integration\\nGenealogy Engine: FFD 1.9 RC1\\nBackend: \\(backendState)\\nDatabase: \\(dbPath)\\nOllama: \\(ollamaState)\\nModel: \\(modelDisplay)\\nLog: \\(logPath)"\n        a.addButton(withTitle:"OK"); a.runModal()\n    }\n    func configuredModel() -> String {\n        let url=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".reunion-companion/config.json")\n        guard let data=try? Data(contentsOf:url),\n              let obj=try? JSONSerialization.jsonObject(with:data) as? [String:Any] else { return "" }\n        return obj["llm_model"] as? String ?? ""\n    }\n    func isOllamaReady() -> Bool {\n        guard let url=URL(string:"http://127.0.0.1:11434/api/tags") else { return false }\n        let sem=DispatchSemaphore(value:0); var ready=false; var req=URLRequest(url:url); req.timeoutInterval=0.75\n        URLSession.shared.dataTask(with:req) { _,response,error in\n            if error == nil, let http=response as? HTTPURLResponse, (200..<500).contains(http.statusCode) { ready=true }\n            sem.signal()\n        }.resume()\n        _=sem.wait(timeout:.now()+1.0); return ready\n    }\n    @objc func showMainWindow() { window?.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps:true) }\n    func applicationShouldHandleReopen(_ sender:NSApplication,hasVisibleWindows flag:Bool)->Bool { showMainWindow(); return true }\n    func windowShouldClose(_ sender:NSWindow)->Bool { sender.orderOut(nil); return false }\n    func startOrAttach() {\n        DispatchQueue.global(qos:.userInitiated).async {\n            if self.isCompanionReady() { DispatchQueue.main.async { self.loadCompanion() }; return }\n            do { try self.launchBackend() } catch { DispatchQueue.main.async { self.showStartupError("Companion could not be started.\\\\n\\\\n\\\\(error.localizedDescription)") }; return }\n            for _ in 0..<80 { if self.isCompanionReady() { DispatchQueue.main.async { self.loadCompanion() }; return }; if let p=self.backend,!p.isRunning { break }; Thread.sleep(forTimeInterval:0.25) }\n            DispatchQueue.main.async { self.showStartupError("Companion did not become ready on 127.0.0.1:8765.\\\\n\\\\nSee ~/Library/Logs/Reunion Companion/backend.log") }\n        }\n    }\n    func launchBackend() throws {\n        let repo=URL(fileURLWithPath:repoPath); let python=repo.appendingPathComponent(".venv/bin/python")\n        guard FileManager.default.isExecutableFile(atPath:python.path) else { throw NSError(domain:"ReunionCompanion",code:1,userInfo:[NSLocalizedDescriptionKey:"Python environment not found at \\\\(python.path)."]) }\n        let logDir=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/Reunion Companion",isDirectory:true); try FileManager.default.createDirectory(at:logDir,withIntermediateDirectories:true)\n        let logURL=logDir.appendingPathComponent("backend.log"); if !FileManager.default.fileExists(atPath:logURL.path) { FileManager.default.createFile(atPath:logURL.path,contents:nil) }\n        let log=try FileHandle(forWritingTo:logURL); try log.seekToEnd(); backendLog=log\n        let p=Process(); p.executableURL=python; p.arguments=["-m","reunion_companion.companion.ui","--no-browser"]; p.currentDirectoryURL=repo\n        var env=ProcessInfo.processInfo.environment; let src=repo.appendingPathComponent("src").path; env["PYTHONPATH"]=src+(env["PYTHONPATH"].map { ":"+$0 } ?? ""); p.environment=env; p.standardOutput=log; p.standardError=log; try p.run(); backend=p\n    }\n    func isCompanionReady()->Bool {\n        let sem=DispatchSemaphore(value:0); var ready=false; var request=URLRequest(url:companionURL); request.timeoutInterval=1.0\n        URLSession.shared.dataTask(with:request) { data,response,error in defer { sem.signal() }; guard error==nil,let data=data,let http=response as? HTTPURLResponse,(200..<500).contains(http.statusCode),let body=String(data:data,encoding:.utf8) else { return }; ready=body.localizedCaseInsensitiveContains("Reunion Companion") }.resume(); _=sem.wait(timeout:.now()+1.5); return ready\n    }\n    func loadCompanion() { guard let web=webView else { return }; web.load(URLRequest(url:companionURL)); showMainWindow() }\n    func webView(_ webView:WKWebView,decidePolicyFor navigationAction:WKNavigationAction,decisionHandler:@escaping(WKNavigationActionPolicy)->Void) {\n        guard let url=navigationAction.request.url else { decisionHandler(.cancel); return }; let host=(url.host ?? "").lowercased(); let local=host=="127.0.0.1" || host=="localhost" || url.scheme=="about"\n        if local { decisionHandler(.allow) } else { NSWorkspace.shared.open(url); decisionHandler(.cancel) }\n    }\n    func showStartupError(_ text:String) { let a=NSAlert(); a.alertStyle = .critical; a.messageText="Reunion Companion could not start"; a.informativeText=text; a.addButton(withTitle:"Quit"); a.runModal(); NSApp.terminate(nil) }\n    func applicationWillTerminate(_ notification:Notification) { if let p=backend,p.isRunning { p.terminate(); Thread.sleep(forTimeInterval:0.2); if p.isRunning { p.interrupt() } }; try? backendLog?.close() }\n}\nlet app=NSApplication.shared; let delegate=AppDelegate(); app.delegate=delegate; app.run()\n'

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
    subprocess.run([plan.swiftc, str(source), "-framework","AppKit", "-framework","WebKit", "-o", str(macos/APP_NAME)], check=True)
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
