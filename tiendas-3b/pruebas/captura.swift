// Navegador sin ventana (WebKit) para pruebas: carga una URL, ejecuta pasos de JavaScript y guarda capturas.
//   captura <url> <ancho> <alto> <pasos.json> <carpeta_salida>
// pasos.json: [{"js":"...", "espera":800, "png":"nombre.png", "imprime":true}, ...]
import Cocoa
import WebKit

let args = CommandLine.arguments
guard args.count >= 6 else { print("uso: captura <url> <ancho> <alto> <pasos.json> <salida>"); exit(2) }
let url = URL(string: args[1])!
let ancho = CGFloat(Double(args[2])!), alto = CGFloat(Double(args[3])!)
let pasos = (try! JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: args[4])))) as! [[String: Any]]
let salida = args[5]
try? FileManager.default.createDirectory(atPath: salida, withIntermediateDirectories: true)

class Delegado: NSObject, WKNavigationDelegate, WKUIDelegate {
    var web: WKWebView!
    var indice = 0
    var iniciado = false
    func webView(_ w: WKWebView, didFinish n: WKNavigation!) {
        if iniciado { return }          // las recargas posteriores no reinician los pasos
        iniciado = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) { self.siguiente() }
    }
    func webView(_ w: WKWebView, didFail n: WKNavigation!, withError e: Error) { print("ERROR carga: \(e)"); exit(1) }
    func webView(_ w: WKWebView, didFailProvisionalNavigation n: WKNavigation!, withError e: Error) { print("ERROR carga: \(e)"); exit(1) }
    // alert/confirm/prompt de la página: se registran y se aceptan
    func webView(_ w: WKWebView, runJavaScriptAlertPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler c: @escaping () -> Void) { print("[alert] \(m)"); c() }
    func webView(_ w: WKWebView, runJavaScriptConfirmPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler c: @escaping (Bool) -> Void) { print("[confirm] \(m)"); c(true) }

    func siguiente() {
        if indice >= pasos.count { print("FIN"); exit(0) }
        let p = pasos[indice]; indice += 1
        let espera = (p["espera"] as? Double ?? 500) / 1000
        let js = p["js"] as? String ?? "1"
        web.evaluateJavaScript(js) { r, e in
            if let e = e { print("[js error paso \(self.indice)] \(e.localizedDescription)") }
            if (p["imprime"] as? Bool) == true { print("[\(self.indice)] \(r ?? "nil")") }
            DispatchQueue.main.asyncAfter(deadline: .now() + espera) {
                if let png = p["png"] as? String { self.foto(png) } else { self.siguiente() }
            }
        }
    }
    func foto(_ nombre: String) {
        let cfg = WKSnapshotConfiguration()
        web.takeSnapshot(with: cfg) { img, e in
            if let img = img, let tiff = img.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff),
               let png = rep.representation(using: .png, properties: [:]) {
                try? png.write(to: URL(fileURLWithPath: "\(salida)/\(nombre)"))
                print("captura \(nombre)")
            } else { print("sin captura \(nombre): \(String(describing: e))") }
            self.siguiente()
        }
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.accessory)
let d = Delegado()
let cfg = WKWebViewConfiguration()
let web = WKWebView(frame: NSRect(x: 0, y: 0, width: ancho, height: alto), configuration: cfg)
web.navigationDelegate = d; web.uiDelegate = d; d.web = web
// ventana dentro de la pantalla (si estuviera fuera, WebKit congela las animaciones) pero casi transparente y sin recibir clics
let ventana = NSWindow(contentRect: NSRect(x: 0, y: 0, width: ancho, height: alto), styleMask: [.borderless], backing: .buffered, defer: false)
ventana.contentView = web
ventana.alphaValue = 0.02
ventana.ignoresMouseEvents = true
ventana.level = .floating          // por encima de las demás: así WebKit no la considera tapada ni congela las animaciones
ventana.orderFrontRegardless()
web.load(URLRequest(url: url))
DispatchQueue.main.asyncAfter(deadline: .now() + 90) { print("TIMEOUT"); exit(3) }
app.run()
