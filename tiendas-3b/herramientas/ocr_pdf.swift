// OCR de un PDF o imagen con el motor de macOS (Vision). Uso: ocr_pdf <pdf|imagen> <carpeta_salida> [ancho_px=1000] [max_paginas=todas]
// Guarda p1.jpg, p2.jpg… (páginas a <ancho> px) y ocr.json: [{pagina, w, h, lineas:[{t, x, y, w, h, c}]}] con cajas normalizadas (origen arriba-izquierda).
import Foundation
import PDFKit
import Vision
import AppKit

let a = CommandLine.arguments
guard a.count >= 3 else { print("uso: ocr_pdf <pdf|imagen> <salida> [ancho] [max_paginas]"); exit(2) }
var doc = PDFDocument(url: URL(fileURLWithPath: a[1]))
if doc == nil || (a[1].lowercased().hasSuffix(".jpeg") || a[1].lowercased().hasSuffix(".jpg") || a[1].lowercased().hasSuffix(".png")) {
    // una imagen suelta se trata como un PDF de una página
    if let img = NSImage(contentsOfFile: a[1]), let pg = PDFPage(image: img) { let d = PDFDocument(); d.insert(pg, at: 0); doc = d }
}
guard let doc = doc else { print("no se pudo abrir \(a[1])"); exit(2) }
let maxPag = a.count > 4 ? Int(a[4])! : Int.max
let salida = a[2], ancho = a.count > 3 ? CGFloat(Double(a[3])!) : 1000
try? FileManager.default.createDirectory(atPath: salida, withIntermediateDirectories: true)
var paginas: [[String: Any]] = []
for i in 0..<min(doc.pageCount, maxPag) {
    guard let pg = doc.page(at: i) else { continue }
    let r = pg.bounds(for: .mediaBox), esc = ancho / r.width, tam = NSSize(width: ancho, height: (r.height * esc).rounded())
    let img = pg.thumbnail(of: tam, for: .mediaBox)
    guard let tiff = img.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff), let cg = rep.cgImage else { continue }
    let jpg = rep.representation(using: .jpeg, properties: [.compressionFactor: 0.82])!
    try? jpg.write(to: URL(fileURLWithPath: "\(salida)/p\(i + 1).jpg"))
    // OCR a mayor resolución para leer mejor
    let big = pg.thumbnail(of: NSSize(width: 2000, height: (r.height * 2000 / r.width).rounded()), for: .mediaBox)
    let cgBig = NSBitmapImageRep(data: big.tiffRepresentation!)!.cgImage!
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate; req.recognitionLanguages = ["es-MX", "es-ES"]; req.usesLanguageCorrection = true
    try? VNImageRequestHandler(cgImage: cgBig, options: [:]).perform([req])
    var lineas: [[String: Any]] = []
    for o in (req.results ?? []) {
        guard let c = o.topCandidates(1).first else { continue }
        let b = o.boundingBox
        lineas.append(["t": c.string, "x": b.minX, "y": 1 - b.maxY, "w": b.width, "h": b.height, "c": c.confidence])
    }
    lineas.sort { ($0["y"] as! CGFloat) < ($1["y"] as! CGFloat) }
    paginas.append(["pagina": i + 1, "w": Int(tam.width), "h": Int(tam.height), "lineas": lineas])
    _ = cg
}
let data = try! JSONSerialization.data(withJSONObject: paginas, options: [.prettyPrinted])
try! data.write(to: URL(fileURLWithPath: "\(salida)/ocr.json"))
print("páginas:", min(doc.pageCount, maxPag), "de", doc.pageCount)
