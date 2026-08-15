#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import argparse, plistlib, shutil, subprocess

APP_NAME="Reunion Companion"
APP_VERSION="2.0"
APP_BUILD="5"
APP_RELEASE="FFD 2.0 Build 5 — Installation & First-Run Experience"
ENGINE_BASELINE="FFD 1.9 RC1"
BUNDLE_ID="com.reunioncompanion.app"

SWIFT_TEMPLATE=r'''import AppKit
import Foundation
import WebKit
import UniformTypeIdentifiers

final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate {
    let companionURL = URL(string: "http://127.0.0.1:8765/")!
    var backend: Process?
    var backendLog: FileHandle?
    var window: NSWindow?
    var webView: WKWebView?

    func applicationDidFinishLaunching(_ notification: Notification) {
        configureMenu(); NSApp.setActivationPolicy(.regular); createWindow(); NSApp.activate(ignoringOtherApps: true); startOrAttach()
    }
    func configureMenu() {
        let mainMenu=NSMenu(); let appItem=NSMenuItem(); let appMenu=NSMenu()
        appMenu.addItem(withTitle:"About Reunion Companion",action:#selector(showAbout),keyEquivalent:"")
        appMenu.addItem(withTitle:"Diagnostics…",action:#selector(showDiagnostics),keyEquivalent:"")
        appMenu.addItem(NSMenuItem.separator()); appMenu.addItem(withTitle:"Quit Reunion Companion",action:#selector(NSApplication.terminate(_:)),keyEquivalent:"q")
        appItem.submenu=appMenu; mainMenu.addItem(appItem)
        let editItem=NSMenuItem(); let editMenu=NSMenu(title:"Edit")
        editMenu.addItem(withTitle:"Cut",action:#selector(NSText.cut(_:)),keyEquivalent:"x")
        editMenu.addItem(withTitle:"Copy",action:#selector(NSText.copy(_:)),keyEquivalent:"c")
        editMenu.addItem(withTitle:"Paste",action:#selector(NSText.paste(_:)),keyEquivalent:"v")
        editMenu.addItem(NSMenuItem.separator()); editMenu.addItem(withTitle:"Select All",action:#selector(NSText.selectAll(_:)),keyEquivalent:"a")
        editItem.submenu=editMenu; mainMenu.addItem(editItem)
        let viewItem=NSMenuItem(); let viewMenu=NSMenu(title:"View")
        viewMenu.addItem(withTitle:"Reload",action:#selector(reloadCurrentPage),keyEquivalent:"r"); viewItem.submenu=viewMenu; mainMenu.addItem(viewItem)
        let windowItem=NSMenuItem(); let windowMenu=NSMenu(title:"Window")
        windowMenu.addItem(withTitle:"Reunion Companion",action:#selector(showMainWindow),keyEquivalent:"0"); windowItem.submenu=windowMenu; mainMenu.addItem(windowItem); NSApp.windowsMenu=windowMenu; NSApp.mainMenu=mainMenu
    }
    func createWindow() {
        let frame=NSRect(x:0,y:0,width:1280,height:820)
        let w=NSWindow(contentRect:frame,styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)
        w.title="Reunion Companion"; w.minSize=NSSize(width:900,height:600); w.center(); w.delegate=self; w.isReleasedWhenClosed=false
        let web=WKWebView(frame:w.contentView?.bounds ?? frame,configuration:WKWebViewConfiguration()); web.autoresizingMask=[.width,.height]; web.navigationDelegate=self
        w.contentView=web; window=w; webView=web; w.makeKeyAndOrderFront(nil)
    }
    @objc func showAbout() { let a=NSAlert(); a.messageText="Reunion Companion"; a.informativeText="FFD 2.0 Build 5 — Installation & First-Run Experience\nGenealogy Engine: FFD 1.9 RC1"; a.addButton(withTitle:"OK"); a.runModal() }
    @objc func reloadCurrentPage() { webView?.reload() }
    @objc func showDiagnostics() {
        let backendState = isCompanionReady() ? "Running" : "Not responding"
        let ollamaState = isOllamaReady() ? "Running" : "Not responding"
        let dbPath = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".reunion-companion/companion.sqlite3").path
        let logPath = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/Reunion Companion/backend.log").path
        let runtimePath = Bundle.main.resourceURL?.appendingPathComponent("Runtime/ReunionCompanionBackend/ReunionCompanionBackend").path ?? "(not found)"
        let model = ProcessInfo.processInfo.environment["REUNION_LLM_MODEL"] ?? configuredModel()
        let modelDisplay = model.isEmpty ? "(automatic)" : model
        let a=NSAlert(); a.messageText="Reunion Companion Diagnostics"
        a.informativeText="Application: FFD 2.0 Build 5 — Installation & First-Run Experience\nGenealogy Engine: FFD 1.9 RC1\nBackend: \(backendState)\nDatabase: \(dbPath)\nOllama: \(ollamaState)\nModel: \(modelDisplay)\nRuntime: \(runtimePath)\nLog: \(logPath)"
        a.addButton(withTitle:"OK"); a.runModal()
    }
    func configuredModel() -> String {
        let url=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".reunion-companion/config.json")
        guard let data=try? Data(contentsOf:url), let obj=try? JSONSerialization.jsonObject(with:data) as? [String:Any] else { return "" }
        return obj["llm_model"] as? String ?? ""
    }
    func isOllamaReady() -> Bool {
        guard let url=URL(string:"http://127.0.0.1:11434/api/tags") else { return false }
        let sem=DispatchSemaphore(value:0); var ready=false; var req=URLRequest(url:url); req.timeoutInterval=0.75
        URLSession.shared.dataTask(with:req) { _,response,error in if error == nil, let http=response as? HTTPURLResponse, (200..<500).contains(http.statusCode) { ready=true }; sem.signal() }.resume()
        _=sem.wait(timeout:.now()+1.0); return ready
    }
    func ollamaModelStatus() -> String {
        guard let url=URL(string:"http://127.0.0.1:11434/api/tags") else { return "⚠ AI model status unavailable" }
        let sem=DispatchSemaphore(value:0); var status="⚠ No local AI model detected"
        var req=URLRequest(url:url); req.timeoutInterval=1.0
        URLSession.shared.dataTask(with:req) { data,response,error in
            defer { sem.signal() }
            guard error == nil, let data=data, let obj=try? JSONSerialization.jsonObject(with:data) as? [String:Any], let models=obj["models"] as? [[String:Any]] else { return }
            let names=models.compactMap { $0["name"] as? String }
            let configured=ProcessInfo.processInfo.environment["REUNION_LLM_MODEL"] ?? self.configuredModel()
            if !configured.isEmpty { status=names.contains(configured) ? "✓ AI model available: \(configured)" : "⚠ Configured AI model is not installed: \(configured)" }
            else if !names.isEmpty { status="✓ AI model available (automatic selection)" }
        }.resume(); _=sem.wait(timeout:.now()+1.5); return status
    }
    func setupRequired() -> Bool {
        guard let url=URL(string:"http://127.0.0.1:8765/setup/status") else { return false }
        let sem=DispatchSemaphore(value:0); var required=false; var req=URLRequest(url:url); req.timeoutInterval=1.0
        URLSession.shared.dataTask(with:req) { data,response,error in
            defer { sem.signal() }
            guard error == nil, let data=data, let obj=try? JSONSerialization.jsonObject(with:data) as? [String:Any] else { return }
            required=(obj["needs_genealogy_data"] as? Bool) ?? false
        }.resume(); _=sem.wait(timeout:.now()+1.5); return required
    }
    func finishStartup() {
        if setupRequired() { showFirstRun() } else { loadCompanion() }
    }
    func showFirstRun() {
        let ollama = isOllamaReady() ? "✓ Ollama detected" : "⚠ Ollama not detected — Biography AI will be unavailable until Ollama is installed and running"
        let a=NSAlert(); a.messageText="Welcome to Reunion Companion"
        a.informativeText="✓ Application runtime ready\n✓ User data area ready\n✓ Companion database ready\n\(ollama)\n\nGenealogy data\nNo family history has been loaded yet.\n\nYou can import a Reunion GEDCOM now or continue to Companion and import later."
        a.addButton(withTitle:"Import GEDCOM…"); a.addButton(withTitle:"Continue")
        if a.runModal() == .alertFirstButtonReturn { chooseAndImportGEDCOM() } else { loadCompanion() }
    }
    func chooseAndImportGEDCOM() {
        let panel=NSOpenPanel(); panel.title="Import Reunion GEDCOM"; panel.prompt="Import"; panel.canChooseFiles=true; panel.canChooseDirectories=false; panel.allowsMultipleSelection=false
        panel.allowedContentTypes=[UTType(filenameExtension:"ged") ?? .data, UTType(filenameExtension:"gedcom") ?? .data]
        guard panel.runModal() == .OK, let file=panel.url else { showFirstRun(); return }
        importGEDCOM(file)
    }
    func importGEDCOM(_ file:URL) {
        guard let url=URL(string:"http://127.0.0.1:8765/setup/import") else { loadCompanion(); return }
        var req=URLRequest(url:url); req.httpMethod="POST"; req.timeoutInterval=120
        var components=URLComponents(); components.queryItems=[URLQueryItem(name:"path",value:file.path)]
        req.httpBody=components.percentEncodedQuery?.data(using:.utf8); req.setValue("application/x-www-form-urlencoded",forHTTPHeaderField:"Content-Type")
        let sem=DispatchSemaphore(value:0); var ok=false; var message="Import failed."
        URLSession.shared.dataTask(with:req) { data,response,error in
            defer { sem.signal() }
            if let http=response as? HTTPURLResponse, (200..<300).contains(http.statusCode) { ok=true }
            if let data=data, let obj=try? JSONSerialization.jsonObject(with:data) as? [String:Any], let text=obj["message"] as? String { message=text }
            if let error=error { message=error.localizedDescription }
        }.resume(); _=sem.wait(timeout:.now()+125)
        if ok { let a=NSAlert(); a.messageText="GEDCOM imported"; a.informativeText=message; a.addButton(withTitle:"Continue"); a.runModal(); loadCompanion() }
        else { let a=NSAlert(); a.alertStyle = .warning; a.messageText="GEDCOM could not be imported"; a.informativeText=message; a.addButton(withTitle:"Choose Another…"); a.addButton(withTitle:"Continue Without Importing"); if a.runModal() == .alertFirstButtonReturn { chooseAndImportGEDCOM() } else { loadCompanion() } }
    }
    @objc func showMainWindow() { window?.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps:true) }
    func applicationShouldHandleReopen(_ sender:NSApplication,hasVisibleWindows flag:Bool)->Bool { showMainWindow(); return true }
    func windowShouldClose(_ sender:NSWindow)->Bool { sender.orderOut(nil); return false }
    func startOrAttach() {
        DispatchQueue.global(qos:.userInitiated).async {
            if self.isCompanionReady() { DispatchQueue.main.async { self.finishStartup() }; return }
            do { try self.launchBackend() } catch { DispatchQueue.main.async { self.showStartupError("Companion could not be started.\n\n\(error.localizedDescription)") }; return }
            for _ in 0..<80 { if self.isCompanionReady() { DispatchQueue.main.async { self.finishStartup() }; return }; if let p=self.backend,!p.isRunning { break }; Thread.sleep(forTimeInterval:0.25) }
            DispatchQueue.main.async { self.showStartupError("Companion did not become ready on 127.0.0.1:8765.\n\nSee ~/Library/Logs/Reunion Companion/backend.log") }
        }
    }
    func launchBackend() throws {
        guard let resources=Bundle.main.resourceURL else { throw NSError(domain:"ReunionCompanion",code:1,userInfo:[NSLocalizedDescriptionKey:"Application Resources directory is unavailable."]) }
        let executable=resources.appendingPathComponent("Runtime/ReunionCompanionBackend/ReunionCompanionBackend")
        guard FileManager.default.isExecutableFile(atPath:executable.path) else { throw NSError(domain:"ReunionCompanion",code:2,userInfo:[NSLocalizedDescriptionKey:"Bundled Companion runtime not found at \(executable.path)."]) }
        let logDir=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/Reunion Companion",isDirectory:true); try FileManager.default.createDirectory(at:logDir,withIntermediateDirectories:true)
        let logURL=logDir.appendingPathComponent("backend.log"); if !FileManager.default.fileExists(atPath:logURL.path) { FileManager.default.createFile(atPath:logURL.path,contents:nil) }
        let log=try FileHandle(forWritingTo:logURL); try log.seekToEnd(); backendLog=log
        let p=Process(); p.executableURL=executable; p.arguments=["--no-browser"]; p.currentDirectoryURL=resources
        p.environment=ProcessInfo.processInfo.environment; p.standardOutput=log; p.standardError=log; try p.run(); backend=p
    }
    func isCompanionReady()->Bool {
        let sem=DispatchSemaphore(value:0); var ready=false; var request=URLRequest(url:companionURL); request.timeoutInterval=1.0
        URLSession.shared.dataTask(with:request) { data,response,error in defer { sem.signal() }; guard error==nil,let data=data,let http=response as? HTTPURLResponse,(200..<500).contains(http.statusCode),let body=String(data:data,encoding:.utf8) else { return }; ready=body.localizedCaseInsensitiveContains("Reunion Companion") }.resume(); _=sem.wait(timeout:.now()+1.5); return ready
    }
    func loadCompanion() { guard let web=webView else { return }; web.load(URLRequest(url:companionURL)); showMainWindow() }
    func webView(_ webView:WKWebView,decidePolicyFor navigationAction:WKNavigationAction,decisionHandler:@escaping(WKNavigationActionPolicy)->Void) {
        guard let url=navigationAction.request.url else { decisionHandler(.cancel); return }; let host=(url.host ?? "").lowercased(); let local=host=="127.0.0.1" || host=="localhost" || url.scheme=="about"
        if local { decisionHandler(.allow) } else { NSWorkspace.shared.open(url); decisionHandler(.cancel) }
    }
    func showStartupError(_ text:String) { let a=NSAlert(); a.alertStyle = .critical; a.messageText="Reunion Companion could not start"; a.informativeText=text; a.addButton(withTitle:"Quit"); a.runModal(); NSApp.terminate(nil) }
    func applicationWillTerminate(_ notification:Notification) { if let p=backend,p.isRunning { p.terminate(); Thread.sleep(forTimeInterval:0.2); if p.isRunning { p.interrupt() } }; try? backendLog?.close() }
}
let app=NSApplication.shared; let delegate=AppDelegate(); app.delegate=delegate; app.run()
'''

@dataclass(frozen=True)
class BuildPlan:
    repo: Path; output: Path; python: Path; swiftc: str

def repository_root()->Path: return Path(__file__).resolve().parents[1]
def make_plan(repo:Path|None=None,output:Path|None=None)->BuildPlan:
    repo=(repo or repository_root()).resolve(); output=(output or repo/"dist"/f"{APP_NAME}.app").resolve()
    return BuildPlan(repo,output,repo/".venv/bin/python",shutil.which("swiftc") or "")
def swift_source(repo:Path)->str: return SWIFT_TEMPLATE

def info_plist()->dict:
    return {"CFBundleDevelopmentRegion":"en","CFBundleDisplayName":APP_NAME,"CFBundleExecutable":APP_NAME,"CFBundleIdentifier":BUNDLE_ID,"CFBundleInfoDictionaryVersion":"6.0","CFBundleName":APP_NAME,"CFBundlePackageType":"APPL","CFBundleShortVersionString":APP_VERSION,"CFBundleVersion":APP_BUILD,"LSMinimumSystemVersion":"13.0","NSHighResolutionCapable":True,"LSApplicationCategoryType":"public.app-category.reference"}

def pyinstaller_available(python:Path)->bool:
    return subprocess.run([str(python),"-c","import PyInstaller"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def validate(plan:BuildPlan)->list[str]:
    problems=[]
    if not plan.repo.joinpath("src/reunion_companion/companion/ui.py").exists(): problems.append("Repository does not contain the Companion UI module.")
    if not plan.python.exists(): problems.append(f"Build virtual environment Python not found: {plan.python}")
    if plan.python.exists() and not pyinstaller_available(plan.python): problems.append("PyInstaller is required to build the self-contained runtime. Run: python -m pip install PyInstaller")
    if not plan.swiftc: problems.append("swiftc was not found. Install Apple's Command Line Tools.")
    return problems

def build_embedded_runtime(plan:BuildPlan,resources:Path)->Path:
    stage=plan.repo/"build"/"macos-runtime"
    if stage.exists(): shutil.rmtree(stage)
    work=stage/"work"; spec=stage/"spec"; dist=stage/"dist"
    for x in (work,spec,dist): x.mkdir(parents=True,exist_ok=True)
    entry=stage/"backend_entry.py"; entry.write_text("from reunion_companion.companion.ui import main\nif __name__ == '__main__': main()\n")
    cmd=[str(plan.python),"-m","PyInstaller","--noconfirm","--clean","--onedir","--name","ReunionCompanionBackend","--paths",str(plan.repo/"src"),"--collect-all","PIL","--collect-all","pymupdf","--distpath",str(dist),"--workpath",str(work),"--specpath",str(spec),str(entry)]
    subprocess.run(cmd,check=True,cwd=plan.repo)
    frozen=dist/"ReunionCompanionBackend"; exe=frozen/"ReunionCompanionBackend"
    if not exe.is_file(): raise SystemExit(f"Embedded runtime build did not produce {exe}")
    target=resources/"Runtime"/"ReunionCompanionBackend"; shutil.copytree(frozen,target)
    return target

def build(plan:BuildPlan)->Path:
    problems=validate(plan)
    if problems: raise SystemExit("\n".join(problems))
    app=plan.output
    if app.exists(): shutil.rmtree(app)
    macos=app/"Contents"/"MacOS"; resources=app/"Contents"/"Resources"; macos.mkdir(parents=True); resources.mkdir(parents=True)
    source=resources/"ReunionCompanionLauncher.swift"; source.write_text(swift_source(plan.repo))
    with (app/"Contents"/"Info.plist").open("wb") as f: plistlib.dump(info_plist(),f)
    subprocess.run([plan.swiftc,str(source),"-framework","AppKit","-framework","WebKit","-framework","UniformTypeIdentifiers","-o",str(macos/APP_NAME)],check=True)
    build_embedded_runtime(plan,resources)
    return app

def install(app:Path,destination:Path)->Path:
    destination=destination.expanduser().resolve(); destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists(): shutil.rmtree(destination)
    shutil.copytree(app,destination,symlinks=True); return destination

def main():
    ap=argparse.ArgumentParser(description=APP_RELEASE); ap.add_argument("--output",type=Path); ap.add_argument("--install",type=Path); ap.add_argument("--plan",action="store_true"); args=ap.parse_args(); plan=make_plan(output=args.output)
    if args.plan:
        print(f"Release: {APP_RELEASE}\nEngine: {ENGINE_BASELINE}\nRepository: {plan.repo}\nBuild Python: {plan.python}\nRuntime: embedded PyInstaller onedir backend\nOutput: {plan.output}\nswiftc: {plan.swiftc or '(not found)'}"); return
    app=build(plan); print(f"Built: {app}")
    if args.install:
        installed=install(app,args.install); print(f"Installed: {installed}")
        if app.resolve()!=installed.resolve() and app.exists():
            shutil.rmtree(app); print(f"Cleaned build artifact: {app}")
if __name__=="__main__": main()
