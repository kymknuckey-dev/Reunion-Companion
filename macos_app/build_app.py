#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import argparse, plistlib, shutil, subprocess
import ctypes
import ctypes.util
import os

APP_NAME="Reunion Companion"
APP_VERSION="2.0"
APP_BUILD="6"
# Historical RC1.0.14.8.9.9.4.1.3.12.10.4.1 regression contract: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.10.4.1 — Family Context Safety & GEDCOM Locate QA"
# Historical RC1.0.10 regression contract: APP_RELEASE="FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction QA Pass 1"
# Historical RC1.0.11 regression contract: APP_RELEASE="FFD 2.0 RC1.0.11 — Family-based Book Scope & Lineage Selection"
# Historical RC1.0.11.1 regression contract: APP_RELEASE="FFD 2.0 RC1.0.11.1 — Family Scope & Book Presentation QA Pass 1"
# Historical RC1.0.11.2 regression contract: APP_RELEASE="FFD 2.0 RC1.0.11.2 — Unified Family Charts & HTML Book QA Pass 2"
# Historical RC1.0.11.3 regression contract: APP_RELEASE="FFD 2.0 RC1.0.11.3 — Dual-Line Family Charts & HTML Parity QA Pass 3"
# Historical RC1.0.11.3.1 regression contract: APP_RELEASE="FFD 2.0 RC1.0.11.3.1 — Spouse Family Chart Root Correction"
# Historical RC1.0.11.3.2 regression contract: APP_RELEASE="FFD 2.0 RC1.0.11.3.2 — Spouse Family-of-Origin Chart Correction"
# Historical RC1.0.11.3.3 regression contract: APP_RELEASE="FFD 2.0 RC1.0.11.3.3 — Unified Family Chart Presentation"
# Historical RC1.0.11.3.3.1 regression contract: APP_RELEASE="FFD 2.0 RC1.0.11.3.3.1 — Spouse Lineage Stacking Correction"
# Historical RC1.0.12 regression contract: APP_RELEASE="FFD 2.0 RC1.0.12 — Standalone Descendant Report Pass 1"
# Historical RC1.0.12.1 regression contract: APP_RELEASE="FFD 2.0 RC1.0.12.1 — Descendant Report Preview Access Correction"
# Historical RC1.0.12.2 regression contract: APP_RELEASE="FFD 2.0 RC1.0.12.2 — Descendant Report Controls & Presentation QA"
# Historical RC1.0.12.3 regression contract: APP_RELEASE="FFD 2.0 RC1.0.12.3 — Publish & Descendant Report UX Cleanup"
# Historical RC1.0.12.4 regression contract: APP_RELEASE="FFD 2.0 RC1.0.12.4 — Publish Report Tile Alignment & Iconography"
# Historical RC1.0.12.4.1 regression contract: APP_RELEASE="FFD 2.0 RC1.0.12.4.1 — Publish Icon Column Alignment Correction"
# Historical RC1.0.12.4.2 regression contract: APP_RELEASE="FFD 2.0 RC1.0.12.4.2 — Publish Tile DOM Alignment Correction"
# Historical RC1.0.12.4.3 regression contract: APP_RELEASE="FFD 2.0 RC1.0.12.4.3 — Publish Families Duplication Removal"
# Historical RC1.0.13 regression contract: APP_RELEASE="FFD 2.0 RC1.0.13 — Navigation, Person Focus & Conversation UX Consolidation"
# Historical RC1.0.13.0.1 regression contract: APP_RELEASE="FFD 2.0 RC1.0.13.0.1 — Person Context Mode-aware QA Correction"
# Historical RC1.0.13.1 regression contract: APP_RELEASE="FFD 2.0 RC1.0.13.1 — Persistent Global Navigation, Person Header Parity & Home Explore Removal"
# Historical RC1.0.14.8.9.9.4.1.3.10 regression contract: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.10 — Family Scope Child-only Individual Visibility"
# Historical RC1.0.14.8.9.9.4.1.3.9 regression contract: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.9 — Child-only Individual Family-history Inclusion"
# Historical RC1.0.14.8.9.9.4.1.3.11 regression contract: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.11 — Selectable Child-only Individuals"
# Historical RC1.0.14.8.9.9.4.1.3.11.1 regression contract: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.11.1 — Terminal Individual Opt-in Default"
# Historical RC1.0.14.8.9.9.4.1.3.11.2 regression contract: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.11.2 — Manage Page Layout Consolidation"
# Historical RC1.0.14.8.9.9.4.1.3.12 regression contract: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12 — Data Manager Workflow Consolidation"
# Historical RC1.0.14.8.9.9.4.1.3.12.1 regression contract: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.1 — Data Manager Regression Contract Correction"
# Historical release: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.1.1 — Production Metadata Regression Hardening"
# Historical release: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.2 — Ryerson Retry Timing Visibility"
# Historical release: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.2.1 — Release Metadata Contract Correction"
# Historical release: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.3 — Ryerson Evidence Deduplication"
# Historical release: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.3.1 — Release Metadata Forward-Compatibility Correction"
# Historical release: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.5 — Home & Search Consolidation"
# Historical release: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6 — Research Value Prioritisation"
# Historical release: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.1 — Research Value Specificity Correction"
# Historical release: APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.6.6 — External Evidence Identity & Review Lifecycle Correction"
APP_RELEASE="FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.10.5.1 — Media Filename Suggestions"
# RC1.0.5 Visual QA Pass 2 icon/bundle acceptance remains part of this cumulative build.
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
    var reunionFilesURL: URL?
    var reunionFilesAccessActive = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        configureMenu(); NSApp.setActivationPolicy(.regular); restoreReunionFilesAccess(); createWindow(); NSApp.activate(ignoringOtherApps: true); startOrAttach()
    }
    func configureMenu() {
        let mainMenu=NSMenu(); let appItem=NSMenuItem(); let appMenu=NSMenu()
        appMenu.addItem(withTitle:"About Reunion Companion",action:#selector(showAbout),keyEquivalent:"")
        appMenu.addItem(withTitle:"Diagnostics…",action:#selector(showDiagnostics),keyEquivalent:"")
        appMenu.addItem(withTitle:"Reunion Files Access…",action:#selector(chooseReunionFilesAccess),keyEquivalent:"")
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
    @objc func showAbout() { let a=NSAlert(); a.messageText="Reunion Companion"; a.informativeText="__APP_RELEASE__\nGenealogy Engine: __ENGINE_BASELINE__"; a.addButton(withTitle:"OK"); a.runModal() }
    @objc func reloadCurrentPage() { webView?.reload() }
    @objc func showDiagnostics() {
        let backendState = isCompanionReady() ? "Running" : "Not responding"
        let ollamaState = isOllamaReady() ? "Running" : "Not responding"
        let dbPath = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".reunion-companion/companion.sqlite3").path
        let logPath = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/Reunion Companion/backend.log").path
        let runtimePath = Bundle.main.resourceURL?.appendingPathComponent("Runtime/ReunionCompanionBackend/ReunionCompanionBackend").path ?? "(not found)"
        let model = ProcessInfo.processInfo.environment["REUNION_LLM_MODEL"] ?? configuredModel()
        let modelDisplay = model.isEmpty ? "(automatic)" : model
        let reunionFilesDisplay = reunionFilesURL?.path ?? "(not granted)"
        let a=NSAlert(); a.messageText="Reunion Companion Diagnostics"
        a.informativeText="Application: __APP_RELEASE__\nGenealogy Engine: __ENGINE_BASELINE__\nBackend: \(backendState)\nDatabase: \(dbPath)\nOllama: \(ollamaState)\nModel: \(modelDisplay)\nRuntime: \(runtimePath)\nReunion Files: \(reunionFilesDisplay)\nLog: \(logPath)"
        a.addButton(withTitle:"OK"); a.runModal()
    }
    func reunionBookmarkURL() -> URL {
        let dir=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".reunion-companion",isDirectory:true)
        try? FileManager.default.createDirectory(at:dir,withIntermediateDirectories:true)
        return dir.appendingPathComponent("reunion-files.bookmark")
    }
    func restoreReunionFilesAccess() {
        let bookmarkURL=reunionBookmarkURL()
        guard let data=try? Data(contentsOf:bookmarkURL) else { return }
        var stale=false
        guard let url=try? URL(resolvingBookmarkData:data,options:[.withSecurityScope],relativeTo:nil,bookmarkDataIsStale:&stale) else { return }
        if stale, let refreshed=try? url.bookmarkData(options:[.withSecurityScope],includingResourceValuesForKeys:nil,relativeTo:nil) { try? refreshed.write(to:bookmarkURL,options:.atomic) }
        if url.startAccessingSecurityScopedResource() { reunionFilesURL=url; reunionFilesAccessActive=true }
    }
    @objc func chooseReunionFilesAccess() {
        let panel=NSOpenPanel(); panel.title="Choose your Reunion Files folder"; panel.message="Select the folder containing Reunion media and related files."; panel.prompt="Grant Access"
        panel.canChooseFiles=false; panel.canChooseDirectories=true; panel.allowsMultipleSelection=false
        if let current=reunionFilesURL { panel.directoryURL=current }
        guard panel.runModal() == .OK, let url=panel.url else { return }
        if reunionFilesAccessActive { reunionFilesURL?.stopAccessingSecurityScopedResource(); reunionFilesAccessActive=false }
        guard url.startAccessingSecurityScopedResource() else {
            let a=NSAlert(); a.alertStyle = .warning; a.messageText="Reunion Files access was not granted"; a.informativeText="Choose the Reunion Files folder again."; a.runModal(); return
        }
        reunionFilesURL=url; reunionFilesAccessActive=true
        do {
            let data=try url.bookmarkData(options:[.withSecurityScope],includingResourceValuesForKeys:nil,relativeTo:nil)
            try data.write(to:reunionBookmarkURL(),options:.atomic)
            let a=NSAlert(); a.messageText="Reunion Files access granted"; a.informativeText=url.path+"\n\nReunion Companion will restore this access on future launches."; a.addButton(withTitle:"OK"); a.runModal()
            webView?.reload()
        } catch {
            let a=NSAlert(); a.alertStyle = .warning; a.messageText="Reunion Files access could not be saved"; a.informativeText=error.localizedDescription; a.runModal()
        }
    }
    func chooseMediaRoot() {
        let panel=NSOpenPanel(); panel.title="Choose Reunion Media folder"; panel.message="Select the Media folder whose contents should be compared with Reunion/GEDCOM references."; panel.prompt="Use Media Folder"
        panel.canChooseFiles=false; panel.canChooseDirectories=true; panel.allowsMultipleSelection=false
        if let current=reunionFilesURL { panel.directoryURL=current }
        guard panel.runModal() == .OK, let folder=panel.url else { return }
        guard let endpoint=URL(string:"http://127.0.0.1:8765/quality/media-root") else { return }
        var req=URLRequest(url:endpoint); req.httpMethod="POST"; req.timeoutInterval=10
        var components=URLComponents(); components.queryItems=[URLQueryItem(name:"path",value:folder.path)]
        req.httpBody=components.percentEncodedQuery?.data(using:.utf8); req.setValue("application/x-www-form-urlencoded",forHTTPHeaderField:"Content-Type")
        let sem=DispatchSemaphore(value:0); var ok=false; var message="The Media folder could not be saved."
        URLSession.shared.dataTask(with:req) { data,response,error in
            defer { sem.signal() }
            if let http=response as? HTTPURLResponse, (200..<300).contains(http.statusCode) { ok=true }
            if let data=data, let obj=try? JSONSerialization.jsonObject(with:data) as? [String:Any], let text=obj["message"] as? String { message=text }
            if let error=error { message=error.localizedDescription }
        }.resume(); _=sem.wait(timeout:.now()+12)
        if ok { webView?.load(URLRequest(url:URL(string:"http://127.0.0.1:8765/quality/media")!)) }
        else { let a=NSAlert(); a.alertStyle = .warning; a.messageText="Media folder could not be selected"; a.informativeText=message; a.runModal() }
    }
    func locateGEDCOM() {
        let panel=NSOpenPanel(); panel.title="Locate expected Reunion GEDCOM"; panel.message="Choose the GEDCOM export for the active Companion Family File."; panel.prompt="Use GEDCOM"
        panel.canChooseFiles=true; panel.canChooseDirectories=false; panel.allowsMultipleSelection=false
        panel.allowedFileTypes=["ged","gedcom"]
        if let current=reunionFilesURL { panel.directoryURL=current }
        guard panel.runModal() == .OK, let file=panel.url else { return }
        guard let endpoint=URL(string:"http://127.0.0.1:8765/data/import") else { return }
        var req=URLRequest(url:endpoint); req.httpMethod="POST"; req.timeoutInterval=120
        var components=URLComponents(); components.queryItems=[URLQueryItem(name:"path",value:file.path)]
        req.httpBody=components.percentEncodedQuery?.data(using:.utf8); req.setValue("application/x-www-form-urlencoded",forHTTPHeaderField:"Content-Type")
        let sem=DispatchSemaphore(value:0); var ok=false; var message="The GEDCOM could not be associated with this Family File."
        URLSession.shared.dataTask(with:req) { data,response,error in
            defer { sem.signal() }
            if let http=response as? HTTPURLResponse, (200..<300).contains(http.statusCode) { ok=true }
            if let error=error { message=error.localizedDescription }
        }.resume(); _=sem.wait(timeout:.now()+125)
        if ok { webView?.load(URLRequest(url:URL(string:"http://127.0.0.1:8765/data")!)) }
        else { let a=NSAlert(); a.alertStyle = .warning; a.messageText="GEDCOM could not be located"; a.informativeText=message; a.runModal() }
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
        panel.allowedFileTypes=["ged","gedcom"]
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
            if self.port8765Occupied() { DispatchQueue.main.async { self.showStartupError("Port 8765 is already in use by an incompatible or unidentified service. Reunion Companion will not attach to it.\n\nQuit the older Reunion Companion or other service using port 8765, then reopen this application.") }; return }
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
        var env=ProcessInfo.processInfo.environment
        let runtimeRoot=resources.appendingPathComponent("Runtime/ReunionCompanionBackend")
        let internalLibs=runtimeRoot.appendingPathComponent("_internal").path
        let fontconfigRoot=runtimeRoot.appendingPathComponent("fontconfig")
        env["FONTCONFIG_FILE"]=fontconfigRoot.appendingPathComponent("etc/fonts/fonts.conf").path
        env["FONTCONFIG_PATH"]=fontconfigRoot.appendingPathComponent("etc/fonts").path
        p.environment=env; p.standardOutput=log; p.standardError=log; try p.run(); backend=p
    }
    func backendIdentity()->[String:Any]? {
        guard let url=URL(string:"http://127.0.0.1:8765/runtime/identity") else { return nil }
        let sem=DispatchSemaphore(value:0); var identity:[String:Any]?; var request=URLRequest(url:url); request.timeoutInterval=1.0
        URLSession.shared.dataTask(with:request) { data,response,error in
            defer { sem.signal() }
            guard error==nil,let data=data,let http=response as? HTTPURLResponse,http.statusCode==200,let obj=try? JSONSerialization.jsonObject(with:data) as? [String:Any] else { return }
            identity=obj
        }.resume(); _=sem.wait(timeout:.now()+1.5); return identity
    }
    func isCompanionReady()->Bool {
        guard let identity=backendIdentity() else { return false }
        return identity["service"] as? String == "reunion-companion-backend" && identity["protocol"] as? Int == 1 && identity["application"] as? String == "FFD 2.0 RC1.0.3" && identity["engine_baseline"] as? String == "FFD 1.9 RC1"
    }
    func port8765Occupied()->Bool {
        guard let url=URL(string:"http://127.0.0.1:8765/") else { return false }
        let sem=DispatchSemaphore(value:0); var occupied=false; var request=URLRequest(url:url); request.timeoutInterval=0.5
        URLSession.shared.dataTask(with:request) { _,response,error in occupied = (response != nil || error == nil); sem.signal() }.resume(); _=sem.wait(timeout:.now()+0.75); return occupied
    }
    func loadCompanion() { guard let web=webView else { return }; web.load(URLRequest(url:companionURL)); showMainWindow() }
    func webView(_ webView:WKWebView,decidePolicyFor navigationAction:WKNavigationAction,decisionHandler:@escaping(WKNavigationActionPolicy)->Void) {
        guard let url=navigationAction.request.url else { decisionHandler(.cancel); return }
        if url.scheme=="reunion-companion" && url.host=="choose-media-root" { decisionHandler(.cancel); DispatchQueue.main.async { self.chooseMediaRoot() }; return }
        if url.scheme=="reunion-companion" && url.host=="locate-gedcom" { decisionHandler(.cancel); DispatchQueue.main.async { self.locateGEDCOM() }; return }
        let host=(url.host ?? "").lowercased(); let local=host=="127.0.0.1" || host=="localhost" || url.scheme=="about"
        if local { decisionHandler(.allow) } else { NSWorkspace.shared.open(url); decisionHandler(.cancel) }
    }
    func showStartupError(_ text:String) { let a=NSAlert(); a.alertStyle = .critical; a.messageText="Reunion Companion could not start"; a.informativeText=text; a.addButton(withTitle:"Quit"); a.runModal(); NSApp.terminate(nil) }
    func applicationWillTerminate(_ notification:Notification) { if let p=backend,p.isRunning { p.terminate(); Thread.sleep(forTimeInterval:0.2); if p.isRunning { p.interrupt() } }; try? backendLog?.close(); if reunionFilesAccessActive { reunionFilesURL?.stopAccessingSecurityScopedResource() } }
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
def swift_source(repo:Path)->str:
    return (SWIFT_TEMPLATE
            .replace("__APP_RELEASE__",APP_RELEASE)
            .replace("__ENGINE_BASELINE__",ENGINE_BASELINE))

def info_plist()->dict:
    return {"CFBundleDevelopmentRegion":"en","CFBundleDisplayName":APP_NAME,"CFBundleExecutable":APP_NAME,"CFBundleIdentifier":BUNDLE_ID,"CFBundleInfoDictionaryVersion":"6.0","CFBundleName":APP_NAME,"CFBundlePackageType":"APPL","CFBundleShortVersionString":APP_VERSION,"CFBundleVersion":APP_BUILD,"CFBundleIconFile":"ReunionCompanion.icns","CFBundleIconName":"ReunionCompanion","LSMinimumSystemVersion":"13.0","NSHighResolutionCapable":True,"LSApplicationCategoryType":"public.app-category.reference"}

def build_app_icon(plan:BuildPlan,resources:Path)->Path:
    master=plan.repo/"macos_app/assets/AppIconMaster.png"
    if not master.is_file():
        raise SystemExit(f"Application icon master missing: {master}")
    sips=shutil.which("sips")
    iconutil=shutil.which("iconutil")
    if not sips or not iconutil:
        raise SystemExit("sips and iconutil are required to build the macOS application icon.")
    iconset=plan.repo/"build/macos-icon/ReunionCompanion.iconset"
    if iconset.parent.exists(): shutil.rmtree(iconset.parent)
    iconset.mkdir(parents=True)
    sizes=[(16,"icon_16x16.png"),(32,"icon_16x16@2x.png"),(32,"icon_32x32.png"),(64,"icon_32x32@2x.png"),(128,"icon_128x128.png"),(256,"icon_128x128@2x.png"),(256,"icon_256x256.png"),(512,"icon_256x256@2x.png"),(512,"icon_512x512.png"),(1024,"icon_512x512@2x.png")]
    for size,name in sizes:
        subprocess.run([sips,"-z",str(size),str(size),str(master),"--out",str(iconset/name)],check=True,stdout=subprocess.DEVNULL)
    out=resources/"ReunionCompanion.icns"
    subprocess.run([iconutil,"-c","icns",str(iconset),"-o",str(out)],check=True)
    if not out.is_file() or out.stat().st_size < 1024:
        raise SystemExit(f"macOS application icon was not produced correctly: {out}")
    return out

def pyinstaller_available(python:Path)->bool:
    return subprocess.run([str(python),"-c","import PyInstaller"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def validate(plan:BuildPlan)->list[str]:
    problems=[]
    if not plan.repo.joinpath("src/reunion_companion/companion/ui.py").exists(): problems.append("Repository does not contain the Companion UI module.")
    if not plan.repo.joinpath("macos_app/assets/AppIconMaster.png").exists(): problems.append("RC1.0.5 application icon master was not found.")
    if not plan.python.exists(): problems.append(f"Build virtual environment Python not found: {plan.python}")
    if plan.python.exists() and not pyinstaller_available(plan.python): problems.append("PyInstaller is required to build the self-contained runtime. Run: python -m pip install PyInstaller")
    if plan.python.exists():
        if subprocess.run([str(plan.python),"-c","import weasyprint"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0:
            problems.append("WeasyPrint is required to build the self-contained PDF publishing runtime.")
    if not plan.swiftc: problems.append("swiftc was not found. Install Apple's Command Line Tools.")
    return problems


WEASYPRINT_NATIVE_ROOTS = (
    "gobject-2.0",
    "glib-2.0",
    "gio-2.0",
    "pango-1.0",
    "pangocairo-1.0",
    "cairo",
    "harfbuzz",
    "fontconfig",
)

def _otool_dependencies(path:Path)->list[tuple[str,Path]]:
    """Return (Mach-O load path, resolved filesystem path) for Homebrew deps.

    Keep the original load path because install_name_tool must replace the
    exact string stored in the Mach-O image. Resolving it too early loses
    /opt/homebrew/opt/... aliases and leaves non-portable references behind.
    """
    out=subprocess.check_output(["otool","-L",str(path)],text=True)
    deps=[]
    for line in out.splitlines()[1:]:
        raw=line.strip().split(" (",1)[0]
        if raw.startswith("/opt/homebrew/"):
            deps.append((raw,Path(raw).resolve()))
    return deps

def weasyprint_native_closure()->list[Path]:
    queue=[]
    for name in WEASYPRINT_NATIVE_ROOTS:
        found=ctypes.util.find_library(name)
        if not found:
            raise SystemExit(f"Required WeasyPrint native library not found: {name}")
        queue.append(Path(found).resolve())

    seen=set()
    while queue:
        path=queue.pop(0)
        if path in seen:
            continue
        if not path.is_file():
            raise SystemExit(f"Required native library missing: {path}")
        seen.add(path)
        for _raw,dep in _otool_dependencies(path):
            if dep not in seen:
                queue.append(dep)
    return sorted(seen)

def bundle_weasyprint_native_libraries(frozen:Path)->Path:
    libdir=frozen/"weasyprint-libs"
    libdir.mkdir(parents=True,exist_ok=True)

    closure=weasyprint_native_closure()

    for src in closure:
        shutil.copy2(src,libdir/src.name)

    # All Homebrew dependencies are colocated, so make every copied dylib
    # resolve other copied dylibs relative to itself.
    copied={src.resolve():libdir/src.name for src in closure}

    for src in closure:
        dst=libdir/src.name

        subprocess.run(
            ["install_name_tool","-id",f"@loader_path/{dst.name}",str(dst)],
            check=True
        )

        for raw,dep in _otool_dependencies(src):
            if dep in copied:
                subprocess.run(
                    [
                        "install_name_tool",
                        "-change",
                        raw,
                        f"@loader_path/{copied[dep].name}",
                        str(dst),
                    ],
                    check=True,
                )

        # install_name_tool invalidates the original Homebrew signature.
        # Apple Silicon requires the modified Mach-O image to be validly
        # signed, so apply a local ad-hoc signature. This is not Developer-ID
        # signing and requires no Apple developer account.
        subprocess.run(
            ["codesign", "--force", "--sign", "-", str(dst)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Compatibility aliases for names WeasyPrint/cffi probes on macOS.
    aliases = {
        "libgobject-2.0-0": "libgobject-2.0.0.dylib",
        "libglib-2.0-0": "libglib-2.0.0.dylib",
        "libgio-2.0-0": "libgio-2.0.0.dylib",
        "libpango-1.0-0": "libpango-1.0.0.dylib",
        "libpangocairo-1.0-0": "libpangocairo-1.0.0.dylib",
        "libpangoft2-1.0-0": "libpangoft2-1.0.0.dylib",
        "libharfbuzz-0": "libharfbuzz.0.dylib",
        "libfontconfig-1": "libfontconfig.1.dylib",
        "libcairo-2": "libcairo.2.dylib",
    }

    for alias,target in aliases.items():
        target_path=libdir/target
        if target_path.exists():
            link=libdir/alias
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to(target)

    # A release bundle must contain no dependency on the build Mac's
    # Homebrew installation.
    unresolved=[]
    for dylib in libdir.glob("*.dylib"):
        out=subprocess.check_output(["otool","-L",str(dylib)],text=True)
        for line in out.splitlines()[1:]:
            dep=line.strip().split(" (",1)[0]
            if dep.startswith("/opt/homebrew/"):
                unresolved.append(f"{dylib.name}: {dep}")
    if unresolved:
        raise SystemExit(
            "Bundled WeasyPrint libraries still contain Homebrew references:\n"
            + "\n".join(unresolved)
        )

    return libdir



def add_weasyprint_compatibility_aliases(frozen:Path)->Path:
    """Add cffi/WeasyPrint probe names to PyInstaller's native runtime.

    Do not copy another Pango/GLib stack. PyInstaller already bundles and
    rewrites these libraries under _internal; aliases must resolve to that
    single native stack.
    """
    internal=frozen/"_internal"
    if not internal.is_dir():
        raise SystemExit(f"PyInstaller internal runtime not found: {internal}")

    aliases = {
        "libgobject-2.0-0": (
            "libgobject-2.0.0.dylib",
            "libgobject-2.0.dylib",
        ),
        "libglib-2.0-0": (
            "libglib-2.0.0.dylib",
            "libglib-2.0.dylib",
        ),
        "libgio-2.0-0": (
            "libgio-2.0.0.dylib",
            "libgio-2.0.dylib",
        ),
        "libpango-1.0-0": (
            "libpango-1.0.0.dylib",
            "libpango-1.0.dylib",
        ),
        "libpangocairo-1.0-0": (
            "libpangocairo-1.0.0.dylib",
            "libpangocairo-1.0.dylib",
        ),
        "libpangoft2-1.0-0": (
            "libpangoft2-1.0.0.dylib",
            "libpangoft2-1.0.dylib",
        ),
        "libfontconfig-1": (
            "libfontconfig.1.dylib",
            "libfontconfig.dylib",
        ),
        "libharfbuzz-0": (
            "libharfbuzz.0.dylib",
            "libharfbuzz.dylib",
        ),
        "libcairo-2": (
            "libcairo.2.dylib",
            "libcairo.dylib",
        ),
    }

    for alias,candidates in aliases.items():
        target=next((name for name in candidates if (internal/name).exists()),None)
        if not target:
            # Some optional Pango components may not be required by this
            # particular PyInstaller/WeasyPrint build.
            continue

        link=internal/alias
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(target)

    return internal



def normalize_weasyprint_harfbuzz(frozen:Path)->None:
    """Ensure WeasyPrint uses a matched HarfBuzz core/subset pair.

    PyInstaller/Pillow may expose Pillow's older private HarfBuzz as the
    top-level libharfbuzz.0.dylib. WeasyPrint's subset library must instead
    use the matching Homebrew HarfBuzz core collected for the PDF runtime.
    Pillow's private PIL/.dylibs copy is left untouched.
    """
    internal=frozen/"_internal"
    core=internal/"libharfbuzz.0.dylib"
    subset=internal/"libharfbuzz-subset.0.dylib"

    hb_prefix=Path(
        subprocess.check_output(
            ["brew","--prefix","harfbuzz"],
            text=True,
        ).strip()
    )

    source_core=hb_prefix/"lib"/"libharfbuzz.0.dylib"
    source_subset=hb_prefix/"lib"/"libharfbuzz-subset.0.dylib"

    if not source_core.is_file() or not source_subset.is_file():
        raise SystemExit("Matched Homebrew HarfBuzz runtime was not found.")

    # Remove PyInstaller's top-level symlink into Pillow's private older
    # HarfBuzz. Do not modify PIL/.dylibs itself.
    if core.exists() or core.is_symlink():
        core.unlink()

    shutil.copy2(source_core,core)
    shutil.copy2(source_subset,subset)

    subprocess.run(
        ["install_name_tool","-id","@rpath/libharfbuzz.0.dylib",str(core)],
        check=True,
    )

    core_changes = (
        ("/opt/homebrew/opt/freetype/lib/libfreetype.6.dylib",
         "@rpath/libfreetype.6.dylib"),
        ("/opt/homebrew/opt/glib/lib/libglib-2.0.0.dylib",
         "@rpath/libglib-2.0.0.dylib"),
        ("/opt/homebrew/opt/graphite2/lib/libgraphite2.3.dylib",
         "@rpath/libgraphite2.3.dylib"),
    )
    for old,new in core_changes:
        subprocess.run(
            ["install_name_tool","-change",old,new,str(core)],
            check=True,
        )

    subprocess.run(
        ["install_name_tool","-id","@rpath/libharfbuzz-subset.0.dylib",str(subset)],
        check=True,
    )

    # Homebrew's subset library may encode either the opt or Cellar path.
    out=subprocess.check_output(["otool","-L",str(subset)],text=True)
    for line in out.splitlines()[1:]:
        dep=line.strip().split(" (",1)[0]
        if dep.startswith("/opt/homebrew/") and dep.endswith("/libharfbuzz.0.dylib"):
            subprocess.run(
                ["install_name_tool","-change",dep,
                 "@rpath/libharfbuzz.0.dylib",str(subset)],
                check=True,
            )

    for dylib in (core,subset):
        subprocess.run(
            ["codesign","--force","--sign","-",str(dylib)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Refuse to package another incompatible pair.
    core_info=subprocess.check_output(["otool","-L",str(core)],text=True)
    subset_info=subprocess.check_output(["otool","-L",str(subset)],text=True)
    if "compatibility version 61430" not in core_info:
        raise SystemExit("Bundled HarfBuzz core is not the expected matched runtime.")
    if "compatibility version 61430" not in subset_info:
        raise SystemExit("Bundled HarfBuzz subset is not the expected matched runtime.")


def bundle_weasyprint_fontconfig(frozen:Path)->Path:
    """Bundle Fontconfig configuration required by Pango/WeasyPrint.

    Homebrew's bottle keeps etc/fonts under .bottle and the conf.d entries
    refer relatively to share/fontconfig/conf.avail. Preserve that layout
    inside the frozen runtime so those references remain valid.
    """
    prefix=Path(
        subprocess.check_output(
            ["brew","--prefix","fontconfig"],
            text=True,
        ).strip()
    ).resolve()

    # brew --prefix resolves through opt -> Cellar. The bottle configuration
    # itself lives below .bottle/etc/fonts.
    etc_fonts=prefix/".bottle"/"etc"/"fonts"
    share_fontconfig=prefix/"share"/"fontconfig"

    if not (etc_fonts/"fonts.conf").is_file():
        raise SystemExit(
            f"Fontconfig fonts.conf was not found at {etc_fonts/'fonts.conf'}"
        )
    if not share_fontconfig.is_dir():
        raise SystemExit(
            f"Fontconfig shared configuration was not found at {share_fontconfig}"
        )

    root=frozen/"fontconfig"

    if root.exists():
        shutil.rmtree(root)

    (root/"etc").mkdir(parents=True,exist_ok=True)
    (root/"share").mkdir(parents=True,exist_ok=True)

    shutil.copytree(
        etc_fonts,
        root/"etc"/"fonts",
        symlinks=True,
    )
    shutil.copytree(
        share_fontconfig,
        root/"share"/"fontconfig",
        symlinks=True,
    )

    config=root/"etc"/"fonts"/"fonts.conf"
    if not config.is_file():
        raise SystemExit("Bundled Fontconfig configuration is incomplete.")

    return root


def verify_frozen_pdf_runtime(executable:Path,fontconfig_root:Path)->None:
    env=dict(os.environ)
    env["FONTCONFIG_FILE"]=str(fontconfig_root/"etc"/"fonts"/"fonts.conf")
    env["FONTCONFIG_PATH"]=str(fontconfig_root/"etc"/"fonts")

    result=subprocess.run(
        [str(executable),"--verify-pdf-runtime"],
        env=env,
        cwd=executable.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if result.returncode != 0:
        raise SystemExit(
            "Frozen WeasyPrint PDF runtime verification failed:\\n"
            + result.stdout
        )

def build_embedded_runtime(plan:BuildPlan,resources:Path)->Path:
    stage=plan.repo/"build"/"macos-runtime"
    if stage.exists(): shutil.rmtree(stage)
    work=stage/"work"; spec=stage/"spec"; dist=stage/"dist"
    for x in (work,spec,dist): x.mkdir(parents=True,exist_ok=True)
    runtime_hook=stage/"weasyprint_frozen_runtime.py"
    runtime_hook.write_text("""import sys
from pathlib import Path

if getattr(sys, "frozen", False) and sys.platform == "darwin":
    from cffi.api import FFI

    _original_dlopen = FFI.dlopen

    # Map WeasyPrint/cffi probe names directly to PyInstaller's canonical
    # libraries. Do not use compatibility symlinks/copies: Pango's linked
    # dependencies must resolve to these exact same Mach-O images.
    _weasy_libraries = {
        "libgobject-2.0-0": "libgobject-2.0.0.dylib",
        "libglib-2.0-0": "libglib-2.0.0.dylib",
        "libgio-2.0-0": "libgio-2.0.0.dylib",
        "libpango-1.0-0": "libpango-1.0.0.dylib",
        "libpangocairo-1.0-0": "libpangocairo-1.0.0.dylib",
        "libpangoft2-1.0-0": "libpangoft2-1.0.dylib",
        "libharfbuzz-0": "libharfbuzz.0.dylib",
        "libharfbuzz-subset-0": "libharfbuzz-subset.0.dylib",
        "libfontconfig-1": "libfontconfig.1.dylib",
        "libcairo-2": "libcairo.2.dylib",
    }

    def _frozen_dlopen(self, name, *args, **kwargs):
        if isinstance(name, str) and name in _weasy_libraries:
            candidate = Path(sys._MEIPASS) / _weasy_libraries[name]
            if candidate.is_file():
                if "--verify-pdf-runtime" in sys.argv:
                    print(
                        "WeasyPrint frozen dlopen:",
                        name,
                        "->",
                        candidate,
                        file=sys.stderr,
                    )
                name = str(candidate)
        return _original_dlopen(self, name, *args, **kwargs)

    FFI.dlopen = _frozen_dlopen
""")

    entry=stage/"backend_entry.py"
    entry.write_text(
        "import sys,tempfile,codecs\n"
        "# Frozen-runtime bootstrap: initialise the codec registry and WeasyPrint\n"
        "# before the long-running Companion server starts.  Real book PDF\n"
        "# publishing imports WeasyPrint later; eager initialisation prevents\n"
        "# import-order/runtime-state regressions in the frozen application.\n"
        "codecs.lookup('utf-16le')\n"
        "'Reunion Companion'.encode('utf-16le')\n"
        "from weasyprint import HTML as _FrozenWeasyHTML\n"
        "if '--verify-pdf-runtime' in sys.argv:\n"
        "    from pathlib import Path\n"
        "    p=Path(tempfile.gettempdir())/'reunion-companion-frozen-pdf-test.pdf'\n"
        "    _FrozenWeasyHTML(string='<!doctype html><html><head><meta charset=\"utf-8\"><style>body{font-family:serif}h1{font-size:24pt}.meta{font-family:sans-serif}</style></head><body><h1>Reunion Companion PDF Runtime</h1><p class=\"meta\">Frozen runtime UTF-16LE and representative typography test — 1933–2026.</p></body></html>').write_pdf(str(p))\n"
        "    if not p.exists() or p.stat().st_size==0: raise SystemExit('Frozen PDF runtime did not create output.')\n"
        "    print('Frozen PDF runtime OK')\n"
        "    raise SystemExit(0)\n"
        "from reunion_companion.companion.ui import main\n"
        "if __name__ == '__main__': main()\n"
    )
    cmd=[
        str(plan.python),"-m","PyInstaller",
        "--noconfirm","--clean","--onedir",
        "--name","ReunionCompanionBackend",
        "--paths",str(plan.repo/"src"),
        "--runtime-hook",str(runtime_hook),
        "--collect-all","PIL",
        "--collect-all","pymupdf",
        "--collect-all","weasyprint",
        "--collect-all","pydyf",
        "--collect-all","tinycss2",
        "--collect-all","cssselect2",
        "--collect-all","pyphen",
        "--collect-all","fontTools",
        "--collect-data","reunion_companion",
        "--distpath",str(dist),
        "--workpath",str(work),
        "--specpath",str(spec),
        str(entry),
    ]
    subprocess.run(cmd,check=True,cwd=plan.repo)
    frozen=dist/"ReunionCompanionBackend"; exe=frozen/"ReunionCompanionBackend"
    if not exe.is_file(): raise SystemExit(f"Embedded runtime build did not produce {exe}")

    normalize_weasyprint_harfbuzz(frozen)
    fontconfig_root=bundle_weasyprint_fontconfig(frozen)
    verify_frozen_pdf_runtime(exe,fontconfig_root)

    target=resources/"Runtime"/"ReunionCompanionBackend"
    shutil.copytree(frozen,target)
    return target

def build(plan:BuildPlan)->Path:
    problems=validate(plan)
    if problems: raise SystemExit("\n".join(problems))
    app=plan.output
    if app.exists(): shutil.rmtree(app)
    macos=app/"Contents"/"MacOS"; resources=app/"Contents"/"Resources"; macos.mkdir(parents=True); resources.mkdir(parents=True)
    source=resources/"ReunionCompanionLauncher.swift"; source.write_text(swift_source(plan.repo))
    with (app/"Contents"/"Info.plist").open("wb") as f: plistlib.dump(info_plist(),f)
    build_app_icon(plan,resources)
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
